"""Florence-2 / PaddleOCR / Qwen / bölge bulucu: yer bulma, okuma ve Qwen değerleriyle birleştirme.

Girdi: sonuclar/tespitler.json (calistir.py, .venv-deney), kayıtlı Qwen-1 cevapları (konum deneyi ve ürün koşulu,
3'er), konumlar.GERCEK (24 kutu). Qwen ve bölge bulucu ürün ortamında hesaplanır (Qwen çağrılmaz).

1. Yer: gerçek kutu "bulundu" = merkezi gerçek kutunun içinde (0,5 h pay) olan ya da IoU ≥ 0,3 bir kutu var.
   Merkez hatası: bulunan kutunun merkezi ile gerçek merkez (h = 37 px). Fazla: hiçbir gerçek kutuya değmeyen kutu.
2. Okuma: bulunan kutunun metnindeki sayı gerçek değere eşit.
3. Birleştirme: Qwen-1'in değerleri (ürün koşulu, 3 kayıt) bulucu kutularına atanır (Macar algoritması).
   Maliyet = kutu–kutu uzaklığı (h) + metin cezası (bulucu aynı sayıyı okuduysa 0, aynı hane sayısı / tek
   rakam farkı 0,5, diğer 1,5). Aday sınırı: uzaklık ≤ 1 h ya da metin tam eşit. Puan set_of_mark/olcum.puanla ile.

Çalıştırma (repo kökünden): PYTHONIOENCODING=utf-8 .venv/Scripts/python deneyler/konum_florence/olcum.py
"""

import importlib.util
import json
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

import cv2

KLASOR = Path(__file__).resolve().parent
REPO = KLASOR.parents[1]
sys.path[:0] = [str(REPO), str(REPO / "deneyler" / "bul_kes_okut")]
from konumlar import GERCEK  # noqa: E402

from mimarlik import okuma  # noqa: E402
from mimarlik.bolge_bulma import bolgeleri_bul  # noqa: E402
from mimarlik.eslestirme import kutu_uzakligi  # noqa: E402
from mimarlik.kenar_bulma import kenarlari_bul  # noqa: E402
from mimarlik.on_isleme import karakter_yuksekligi, murekkep_maskesi  # noqa: E402

ADLAR = {"01": "01_kolay_tek_oda_180x140", "02": "02_kolay_tek_oda_300x240"}
H = 37.0


def _yukle(ad, yol):
    spec = importlib.util.spec_from_file_location(ad, yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


puanla = _yukle("som_olcum", REPO / "deneyler" / "set_of_mark" / "olcum.py").puanla


def merkez(k):
    return ((k[0] + k[2]) / 2, (k[1] + k[3]) / 2)


def iou(a, b):
    ix, iy = max(0, min(a[2], b[2]) - max(a[0], b[0])), max(0, min(a[3], b[3]) - max(a[1], b[1]))
    i = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
    return i / u if u > 0 else 0


def _iceride(p, k, pay):
    return k[0] - pay <= p[0] <= k[2] + pay and k[1] - pay <= p[1] <= k[3] + pay


def yer_ve_okuma(kod, kutular):
    """kutular: [(metin ya da None, kutu)] -> (bulunan, merkez hataları h, okunan doğru, fazla)."""
    bulunan, hatalar, okunan = 0, [], 0
    for _, deger, gk in GERCEK[kod]:
        adaylar = [(m, k) for m, k in kutular if _iceride(merkez(k), gk, 0.5 * H) or iou(k, gk) >= 0.3]
        if not adaylar:
            continue
        bulunan += 1
        m, k = min(adaylar, key=lambda a: math.dist(merkez(a[1]), merkez(gk)))
        hatalar.append(math.dist(merkez(k), merkez(gk)) / H)
        okunan += any(m is not None and okuma._sayi(m) == deger for m, _ in adaylar)
    fazla = sum(not any(iou(k, gk) > 0 or _iceride(merkez(k), gk, 0.5 * H) for _, _, gk in GERCEK[kod])
                for _, k in kutular)
    return bulunan, hatalar, okunan, fazla


def _metin_cezasi(metin, deger):
    s = okuma._sayi(metin) if metin else None
    if s == deger:
        return 0.0
    if s is not None and (len(str(s)) == len(str(deger))
                          and sum(a != b for a, b in zip(str(s), str(deger))) <= 1):
        return 0.5
    return 1.5


def birlestir(tespitler, ogeler):
    from scipy.optimize import linear_sum_assignment
    if not tespitler or not ogeler:
        return []
    m = [[1e6] * len(ogeler) for _ in tespitler]
    for i, t in enumerate(tespitler):
        for j, (d, k) in enumerate(ogeler):
            u = kutu_uzakligi(t["kutu"], k) / H
            ceza = _metin_cezasi(t["metin"], d)
            if u <= 1.0 or ceza == 0.0:
                m[i][j] = u + ceza
    return [(tespitler[i]["kutu"], ogeler[j][0]) for i, j in zip(*linear_sum_assignment(m)) if m[i][j] < 1e6]


def main():
    veri = json.loads((KLASOR / "sonuclar" / "tespitler.json").read_text(encoding="utf-8"))
    tespit = veri["tespitler"]
    kayit = {ad: json.loads((REPO / yol).read_text(encoding="utf-8"))["krokiler"]
             for ad, yol in [("konum", "deneyler/konum_deneyi/sonuclar/qwen_konum.json"),
                             ("ürün", "deneyler/cizgi_silme/sonuclar/qwen_urun.json")]}
    yer_satir, birlesim = [], {}

    def yer_ekle(ad, kod, kutular):
        b, hat, o, f = yer_ve_okuma(kod, kutular)
        yer_satir.append((ad, kod, b, statistics.median(hat) if hat else None, max(hat) if hat else None, o, f))

    for kod, ad in ADLAR.items():
        bgr = cv2.imread(str(REPO / "ornekler" / f"{ad}.jpg"))
        maske = murekkep_maskesi(bgr)
        h = karakter_yuksekligi(maske)
        bl = bolgeleri_bul(maske, kenarlari_bul(maske, h), h)
        yer_ekle("bölge bulucu (bizim)", kod, [(None, b.kutu) for b in bl])
        for kaynak in ("konum", "ürün"):
            for n, c in enumerate(kayit[kaynak][kod]["calistirmalar"], 1):
                yer_ekle(f"Qwen kutuları ({kaynak} #{n})", kod,
                         [(str(d), k) for d, k in okuma.sayilari_ayristir(c["ham"], 1152, 2048)])
        for model, krokiler in tespit.items():
            if "hata" in krokiler:
                continue
            for kosul, t in krokiler[kod].items():
                yer_ekle(f"{model} ({kosul})", kod, [(x["metin"], x["kutu"]) for x in t])
                kendi = [(x["kutu"], okuma._sayi(x["metin"])) for x in t]
                birlesim.setdefault(f"{model} ({kosul}), kendi okuması", []).append(puanla(kod, kendi)[0])
                for c in kayit["ürün"][kod]["calistirmalar"]:
                    ogeler = okuma.sayilari_ayristir(c["ham"], 1152, 2048)
                    birlesim.setdefault(f"{model} ({kosul}) + Qwen değerleri", []).append(
                        puanla(kod, birlestir(t, ogeler))[0])

    print(f"{'kaynak':<40} kroki bulunan/12-14  merkez hata medyan/en çok (h)  okunan  fazla kutu")
    for ad, kod, b, med, mx, o, f in yer_satir:
        print(f"{ad:<40} {kod}    {b:>3}/{len(GERCEK[kod])}        "
              f"{'-' if med is None else f'{med:.2f}':>5} / {'-' if mx is None else f'{mx:.2f}':<5}            {o:>3}   {f:>4}")
    print(f"\n{'birleştirme (24 sayı, toplam)':<50} doğru yanlış  yok  bölge yok  fazla")
    ozet = {}
    for ad, liste in birlesim.items():
        top = sum(liste, Counter())
        ozet[ad] = {**dict(top), "olcum_sayisi": len(liste)}
        print(f"{ad:<50} {top['doğru']:>5} {top['yanlış']:>6} {top['yok']:>4} {top['bölge yok']:>10} {top['fazla']:>6}"
              f"   ({len(liste)} ölçüm; 24 × {len(liste) // 2})")
    for model, krokiler in tespit.items():
        if "hata" in krokiler:
            print(f"{model}: KURULAMADI — {krokiler['hata']}")
    (KLASOR / "sonuclar" / "olcum.json").write_text(json.dumps(
        {"yer": [dict(zip(["kaynak", "kroki", "bulunan", "merkez_hata_medyan_h", "merkez_hata_en_cok_h", "okunan",
                            "fazla"], r)) for r in yer_satir], "birlestirme": ozet,
         "sureler_s": veri.get("sureler_s")}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
