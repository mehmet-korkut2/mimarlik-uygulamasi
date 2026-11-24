"""El çizimi kroki fotoğrafı -> DXF (uçtan uca iskelet).

Kullanım (repo kökünden):
    .venv/Scripts/python -m mimarlik.kroki ornekler/02_kolay_tek_oda_300x240.jpg
    .venv/Scripts/python -m mimarlik.kroki <fotoğraf> --okuma output/02_kolay_tek_oda_300x240.json

Akış: çizgi silme -> Qwen-1 (sayılar + kutular) -> kenar bulma, bölgeler, değer atama, geometrik bağlama
-> Qwen-2 / Y2 (numaralı parçalar) -> birleştirme -> geometri -> DXF + JSON rapor.
Çıktılar: <cikti>/<ad>.dxf, <ad>.json, <ad>_parcalar.jpg (Y2'ye verilen görsel; fotoğraf sayılır,
output/ .gitignore'da). `--okuma`, önceki JSON'daki ham Qwen cevaplarını kullanır: Qwen-1 her zaman kayıttan; Y2 yalnızca
parçalar aynıysa kayıttan, kenar bulma değiştiyse Y2 Qwen'e yeniden sorulur.
"""

import argparse
import json
import sys
import time
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np

from mimarlik import okuma, varsayimlar
from mimarlik.birlestirme import birlestir
from mimarlik.bolge_bulma import bolgeleri_bul
from mimarlik.dxf_yazici import kaydet
from mimarlik.eslestirme import KapiIpucu, degerleri_ata, kroki_kur
from mimarlik.geometri import plan_kur
from mimarlik.kenar_bulma import kenarlari_bul
from mimarlik.on_isleme import cizgileri_sil, karakter_yuksekligi, murekkep_maskesi
from mimarlik.plan_cizimi import ciz

Sor = Callable[[str, bytes], str]


def _parca_geometrisi(sonuc, eslem: dict[str, str]) -> dict[str, list]:
    """{"P3": ["K1.2", [x, y], [x, y]]}: Y2 görselinde hangi etiketin nerede olduğu (0,1 px)."""
    yer = {p.id: p for k in sonuc.kenarlar for p in k.parcalar}
    return {e: [pid, [round(v, 1) for v in yer[pid].bas], [round(v, 1) for v in yer[pid].bit]]
            for e, pid in sorted(eslem.items())}


def _kayit_gecerli(kayit: dict, eslem: dict, geometri: dict) -> bool:
    """Kayıttaki Y2 cevabı bu parçalar için mi? Geometri varsa onunla, yoksa (eski kayıt) eşlemle karşılaştırılır."""
    if "parcalar_geometri" in kayit:
        return kayit["parcalar_geometri"] == geometri
    return kayit.get("eslem") == eslem


def kapi_ipuclari(ham_sayilar: str, atanmis, genislik: int, yukseklik: int) -> list[KapiIpucu]:
    """Kapı kuralının ipuçları: K etiketleri (Qwen kutusu) ve kapı genişliğinde okunan sayılar.

    Okunan sayı için iki nokta: değerin atandığı sayı bölgesinin merkezi (mürekkepten, kesin) ve Qwen'in kendi
    kutusunun merkezi. Değer atama komşu bölgeyle karışabildiği için (hata analizi S7; 02'de 90 -> "40 üst"
    bölgesi) ikisi de ipucu sayılır.
    """
    ipuclari = [KapiIpucu(merkez, "etiket", d) for d, merkez in okuma.kapi_etiketleri(ham_sayilar, genislik, yukseklik)]
    etiket_yerleri = {i.nokta for i in ipuclari}
    for deger, (x1, y1, x2, y2) in okuma.sayilari_ayristir(ham_sayilar, genislik, yukseklik):
        merkez = ((x1 + x2) / 2, (y1 + y2) / 2)
        if deger in varsayimlar.KAPI_GENISLIKLERI and merkez not in etiket_yerleri:   # K90 iki kez sayılmasın
            ipuclari.append(KapiIpucu(merkez, "sayi", deger))
    for bolge, deger in atanmis:
        if int(deger) in varsayimlar.KAPI_GENISLIKLERI:
            x1, y1, x2, y2 = bolge.kutu
            ipuclari.append(KapiIpucu(((x1 + x2) / 2, (y1 + y2) / 2), "sayi", int(deger)))
    return ipuclari


def coz(bgr: np.ndarray, sor: Sor, kayit: dict | None = None) -> dict:
    """Bütün adımlar; dosya yazmaz. Döner: rapor sözlüğü + "_doc" (DXF) ve "_parca_gorseli".

    kayit: önceki çalıştırmanın "ham" bölümü (--okuma). Qwen-1 cevabı her zaman kayıttan alınır; Y2 cevabı
    yalnızca parçalar aynıysa (kenar bulma değişmediyse) kayıttan, değilse `sor` ile yeniden sorulur.
    """
    sureler = {}
    t0 = time.perf_counter()
    silinmis = cizgileri_sil(bgr)
    maske = murekkep_maskesi(bgr)
    h = karakter_yuksekligi(maske)
    sonuc0 = kenarlari_bul(maske, h)
    bolgeler0 = bolgeleri_bul(maske, sonuc0, h)
    sureler["kenar_bolge_s"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    ham_sayilar = kayit["sayilar"] if kayit else sor(okuma.ISTEM_SAYILAR, okuma.png(silinmis))
    sureler["qwen_sayilar_s"] = time.perf_counter() - t0
    gen, yuk = bgr.shape[1], bgr.shape[0]
    ogeler = okuma.sayilari_ayristir(ham_sayilar, gen, yuk)

    # 1. geçiş (kapı kuralı yok): kapı ipuçları ve ölçek tahmini için
    t0 = time.perf_counter()
    atanmis0, yok0, okunmamis0 = degerleri_ata(bolgeler0, ogeler, bgr.shape[:2])
    kroki0 = kroki_kur(sonuc0, atanmis0, yok0, okunmamis0, h)
    olcek0 = plan_kur(sonuc0, birlestir(kroki0.olculer, kroki0.yeri_bulunamayan, [], sonuc0, h)[0], h).olcek_cm_px
    ipuclari = kapi_ipuclari(ham_sayilar, atanmis0, gen, yuk)
    # 2. geçiş: kapı kuralıyla (etiket -> okunan sayı -> ölçek)
    sonuc = kenarlari_bul(maske, h, tuple(ipuclari), olcek0)
    bolgeler = bolgeleri_bul(maske, sonuc, h)
    atanmis, yok, okunmamis = degerleri_ata(bolgeler, ogeler, bgr.shape[:2])
    kroki = kroki_kur(sonuc, atanmis, yok, okunmamis, h)
    sureler["kapi_gecisi_s"] = time.perf_counter() - t0

    parca_gorseli, eslem = okuma.parca_gorseli(silinmis, sonuc)
    geometri = _parca_geometrisi(sonuc, eslem)
    t0 = time.perf_counter()
    if kayit and _kayit_gecerli(kayit, eslem, geometri):
        ham_parcalar, y2_kaynagi = kayit["parcalar"], "kayit"
    else:
        ham_parcalar = sor(okuma.ISTEM_PARCALAR, okuma.png(parca_gorseli)) if eslem else ""
        y2_kaynagi = "qwen" if eslem else "yok"
    sureler["qwen_parcalar_s"] = time.perf_counter() - t0
    y2 = okuma.parca_degerlerini_ayristir(ham_parcalar, eslem)

    olculer, sadece_y2 = birlestir(kroki.olculer, kroki.yeri_bulunamayan, y2, sonuc, h)
    plan = plan_kur(sonuc, olculer, h)
    doc, kontrol_notlari = ciz(plan, olculer, sadece_y2)

    return {
        "girdi": {"boyut": list(bgr.shape[:2]), "h_px": round(h, 1),
                  "eksen_acisi_derece": round(sonuc.eksen_acisi_derece, 2)},
        "varsayimlar": {k: getattr(varsayimlar, k) for k in dir(varsayimlar) if k.isupper()},
        "olculer": [asdict(o) for o in olculer],
        "sadece_y2": [list(c) for c in sadece_y2],
        "okunmamis_bolgeler": [list(map(float, b)) for b in kroki.okunmamis_bolgeler],
        "kenarlar": [asdict(k) for k in plan.kenarlar],
        "kapanma": plan.kapanma,
        "kapali": bool(plan.kapanma) and all(e["tutuyor"] for e in plan.kapanma.values()),
        "olcek_cm_px": plan.olcek_cm_px,
        "kontrol_notlari": kontrol_notlari,
        "kapilar": [{"bas": [round(v, 1) for v in k.bas], "bit": [round(v, 1) for v in k.bit], "kaynak": k.kaynak,
                     "deger": k.deger} for k in sonuc.kapilar],
        "kapi_ipuclari": [{"nokta": [round(v, 1) for v in i.nokta], "kaynak": i.kaynak, "deger": i.deger}
                          for i in ipuclari],
        "olcek_ilk_gecis": olcek0,
        "iptaller": [{"merkez": [round(v, 1) for v in i.merkez],
                      "silinen": [[round(v, 1) for v in p] for p in i.silinen]} for i in sonuc.iptaller],
        "ham": {"sayilar": ham_sayilar, "parcalar": ham_parcalar, "eslem": eslem, "parcalar_geometri": geometri,
                "sayilar_kaynagi": "kayit" if kayit else "qwen", "parcalar_kaynagi": y2_kaynagi},
        "sure_s": {k: round(v, 1) for k, v in sureler.items()},
        "_doc": doc,
        "_parca_gorseli": parca_gorseli,
    }


def _ozet(rapor: dict) -> str:
    satirlar = ["Değer  Parça    Kaynak      Emin  Sebep"]
    for o in rapor["olculer"]:
        satirlar.append(f"{o['deger']:>5}  {str(o['parca_id']):<8} {str(o['kaynak']):<11} "
                        f"{'evet' if o['emin'] else 'HAYIR':<5} {o['sebep']}")
    for d, pid in rapor["sadece_y2"]:
        satirlar.append(f"{d:>5}  {pid:<8} {'yalnız Y2':<11} {'HAYIR':<5} Qwen-1 okumadı, geometride kullanılmadı")
    satirlar.append("")
    for k in rapor["kenarlar"]:
        satirlar.append(f"{k['kenar_id']:<4} {k['boy']:>7.0f} cm  {k['durum']}{'' if k['emin'] else '  (emin değil)'}")
    satirlar.append("Kapanma: " + "; ".join(e["not"] for e in rapor["kapanma"].values()))
    return "\n".join(satirlar)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m mimarlik.kroki", description="El çizimi kroki fotoğrafı -> DXF")
    ap.add_argument("fotograf", type=Path)
    ap.add_argument("--cikti", type=Path, default=Path("output"), help="çıktı klasörü (varsayılan: output/)")
    ap.add_argument("--okuma", type=Path, help="önceki çalıştırmanın JSON'u: Qwen yerine ham cevapları kullan")
    arg = ap.parse_args(argv)

    bgr = cv2.imread(str(arg.fotograf))
    if bgr is None:
        print(f"Fotoğraf okunamadı: {arg.fotograf}", file=sys.stderr)
        return 2
    kayit = json.loads(arg.okuma.read_text(encoding="utf-8"))["ham"] if arg.okuma else None
    rapor = coz(bgr, okuma.qwen_sor, kayit)
    if kayit and rapor["ham"]["parcalar_kaynagi"] == "qwen":
        print("Not: parçalar kayıttakinden farklı, Y2 Qwen'e yeniden soruldu.")

    ad = arg.fotograf.stem
    dxf = kaydet(rapor.pop("_doc"), arg.cikti / f"{ad}.dxf")
    cv2.imwrite(str(arg.cikti / f"{ad}_parcalar.jpg"), rapor.pop("_parca_gorseli"))
    (arg.cikti / f"{ad}.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    print(_ozet(rapor))
    print(f"\nYazıldı: {dxf}, {arg.cikti / (ad + '.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
