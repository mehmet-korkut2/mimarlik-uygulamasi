"""El çizimi kroki fotoğrafı -> DXF (uçtan uca iskelet).

Kullanım (repo kökünden):
    .venv/Scripts/python -m mimarlik.kroki ornekler/02_kolay_tek_oda_300x240.jpg
    .venv/Scripts/python -m mimarlik.kroki <fotoğraf> --okuma output/02_kolay_tek_oda_300x240.json

Akış: çizgi silme -> Qwen-1 (sayılar + kutular) -> kenar bulma, bölgeler, değer atama, geometrik bağlama
-> Qwen-2 / Y2 (numaralı parçalar) -> birleştirme -> geometri -> DXF + JSON rapor.
Çıktılar: <cikti>/<ad>.dxf, <ad>.json, <ad>_parcalar.jpg (Y2'ye verilen görsel; fotoğraf sayılır,
output/ .gitignore'da). `--okuma`, önceki JSON'daki ham Qwen cevaplarını kullanır (Qwen çağrılmaz).
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
from mimarlik.eslestirme import degerleri_ata, kroki_kur
from mimarlik.geometri import plan_kur
from mimarlik.kenar_bulma import kenarlari_bul
from mimarlik.on_isleme import cizgileri_sil, karakter_yuksekligi, murekkep_maskesi
from mimarlik.plan_cizimi import ciz

Sor = Callable[[str, bytes], str]


def coz(bgr: np.ndarray, sor: Sor) -> dict:
    """Bütün adımlar; dosya yazmaz. Döner: rapor sözlüğü + "_doc" (DXF) ve "_parca_gorseli"."""
    sureler = {}
    t0 = time.perf_counter()
    silinmis = cizgileri_sil(bgr)
    maske = murekkep_maskesi(bgr)
    h = karakter_yuksekligi(maske)
    sonuc = kenarlari_bul(maske, h)
    bolgeler = bolgeleri_bul(maske, sonuc, h)
    sureler["kenar_bolge_s"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    ham_sayilar = sor(okuma.ISTEM_SAYILAR, okuma.png(silinmis))
    sureler["qwen_sayilar_s"] = time.perf_counter() - t0
    ogeler = okuma.sayilari_ayristir(ham_sayilar, bgr.shape[1], bgr.shape[0])
    atanmis, yok, okunmamis = degerleri_ata(bolgeler, ogeler, bgr.shape[:2])
    kroki = kroki_kur(sonuc, atanmis, yok, okunmamis, h)

    parca_gorseli, eslem = okuma.parca_gorseli(silinmis, sonuc)
    t0 = time.perf_counter()
    ham_parcalar = sor(okuma.ISTEM_PARCALAR, okuma.png(parca_gorseli)) if eslem else ""
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
        "ham": {"sayilar": ham_sayilar, "parcalar": ham_parcalar, "eslem": eslem},
        "sure_s": {k: round(v, 1) for k, v in sureler.items()},
        "_doc": doc,
        "_parca_gorseli": parca_gorseli,
    }


def kayittan_sor(json_yolu: Path) -> Sor:
    """Önceki çalıştırmanın ham Qwen cevaplarını döndüren sahte `sor` (istemden hangisi olduğunu anlar)."""
    ham = json.loads(Path(json_yolu).read_text(encoding="utf-8"))["ham"]

    def sor(istem: str, _gorsel: bytes) -> str:
        return ham["sayilar"] if istem == okuma.ISTEM_SAYILAR else ham["parcalar"]

    return sor


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
    sor = kayittan_sor(arg.okuma) if arg.okuma else okuma.qwen_sor
    rapor = coz(bgr, sor)

    ad = arg.fotograf.stem
    dxf = kaydet(rapor.pop("_doc"), arg.cikti / f"{ad}.dxf")
    cv2.imwrite(str(arg.cikti / f"{ad}_parcalar.jpg"), rapor.pop("_parca_gorseli"))
    (arg.cikti / f"{ad}.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=1), encoding="utf-8")
    print(_ozet(rapor))
    print(f"\nYazıldı: {dxf}, {arg.cikti / (ad + '.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
