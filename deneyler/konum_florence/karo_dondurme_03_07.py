"""Örtüşen karolama + döndürme, 03–07 (`RAPOR_03_07.md` bölüm 7'nin sonraki adımı).

Her fotoğraf ~640 px kare, %30 örtüşen karolara bölünür; her karo 0° / 90° / 180° / 270° döndürülüp Florence-2'ye
okutulur. Tespit kutuları özgün fotoğraf koordinatına geri çevrilip kaydedilir; birleştirme ve puan
`puanla_karo.py`'de. Görseller yalnız bellekte; diske yazılmaz. Qwen yok.

    PYTHONIOENCODING=utf-8 .venv-deney/Scripts/python -u deneyler/konum_florence/karo_dondurme_03_07.py
Çıktı: sonuclar/karo_dondurme_03_07.json
    {kod: {"karolar": [[x0, y0, x1, y1], ...], "tespitler": [{"metin", "kutu" (özgün), "aci", "karo"}],
           "sure_s", "kesik": karo başına 1024 token sınırına varan okuma sayısı (yaklaşık: süreden değil, uzunluktan)}}
"""

import json
import math
import time

import cv2

from okuma_03_07 import ADLAR, KLASOR, gorsel

CIKTI = KLASOR / "sonuclar" / "karo_dondurme_03_07.json"
KARO, ORTUSME = 640, 0.3
ACILAR = {"0": None, "90": cv2.ROTATE_90_CLOCKWISE, "180": cv2.ROTATE_180, "270": cv2.ROTATE_90_COUNTERCLOCKWISE}


def konumlar(uzunluk):
    """Kenarları da kapsayan, eşit aralıklı karo başlangıçları."""
    if uzunluk <= KARO:
        return [0]
    adim = KARO * (1 - ORTUSME)
    n = math.ceil((uzunluk - KARO) / adim) + 1
    return [round(i * (uzunluk - KARO) / (n - 1)) for i in range(n)]


def geri_cevir(kutu, aci, gen, yuk):
    """Döndürülmüş karodaki kutu → döndürülmemiş karo koordinatı. gen/yuk: döndürülmemiş karonun boyu."""
    x0, y0, x1, y1 = kutu
    noktalar = [(x0, y0), (x1, y1)]
    if aci == "90":      # (x, y) → (yuk-1-y, x) ; ters: x = yr, y = yuk-1-xr
        noktalar = [(yr, yuk - 1 - xr) for xr, yr in noktalar]
    elif aci == "180":
        noktalar = [(gen - 1 - xr, yuk - 1 - yr) for xr, yr in noktalar]
    elif aci == "270":   # (x, y) → (y, gen-1-x) ; ters: x = gen-1-yr, y = xr
        noktalar = [(gen - 1 - yr, xr) for xr, yr in noktalar]
    xs, ys = [p[0] for p in noktalar], [p[1] for p in noktalar]
    return [min(xs), min(ys), max(xs), max(ys)]


def main():
    from calistir import Florence
    model, sonuc = Florence(), {}
    for kod in ADLAR:
        bgr = gorsel(kod)
        yuk, gen = bgr.shape[:2]
        karolar = [[x, y, min(gen, x + KARO), min(yuk, y + KARO)] for y in konumlar(yuk) for x in konumlar(gen)]
        tespitler, t0 = [], time.perf_counter()
        for i, (x0, y0, x1, y1) in enumerate(karolar):
            parca = bgr[y0:y1, x0:x1]
            for aci, kod_cv in ACILAR.items():
                g = parca if kod_cv is None else cv2.rotate(parca, kod_cv)
                for t in model.oku(g):
                    k = geri_cevir(t["kutu"], aci, x1 - x0, y1 - y0)
                    tespitler.append({"metin": t["metin"], "kutu": [k[0] + x0, k[1] + y0, k[2] + x0, k[3] + y0],
                                      "aci": aci, "karo": i})
        s = round(time.perf_counter() - t0, 1)
        sonuc[kod] = {"karolar": karolar, "tespitler": tespitler, "sure_s": s}
        print(f"florence {kod}: {len(karolar)} karo × 4 açı, {len(tespitler)} tespit, {s} s", flush=True)
        CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
