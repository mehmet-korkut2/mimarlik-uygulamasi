"""Döndürerek okuma, 03–07: Florence-2 her krokiyi 0° / 90° / 180° / 270° döndürülmüş halde okur (`RAPOR_03_07.md`
bölüm 6, öneri 1). Hedef: sayıların %60'ı yan ya da ters yazılmış, tam görselde %0–8 okunuyor.

Görseller yalnız bellekte döndürülür, diske yazılmaz. Yalnız ham okumalar kaydedilir; puan `puanla_dondurme.py`.
Açı saat yönünde (cv2.rotate). Qwen yok: 4 yön × 5 kroki × 3 tekrar ~7 saat.

Çalıştırma (repo kökünden; Ollama GPU'da model tutmuyor olmalı):
    PYTHONIOENCODING=utf-8 .venv-deney/Scripts/python deneyler/konum_florence/dondurme_03_07.py
Çıktı: sonuclar/dondurme_03_07.json {kod: {"0": {"metinler", "sure_s"}, "90": ..., "180": ..., "270": ...}}
"""

import json
import time

import cv2

from okuma_03_07 import ADLAR, KLASOR, gorsel

CIKTI = KLASOR / "sonuclar" / "dondurme_03_07.json"
ACILAR = {"0": None, "90": cv2.ROTATE_90_CLOCKWISE, "180": cv2.ROTATE_180, "270": cv2.ROTATE_90_COUNTERCLOCKWISE}


def main():
    from calistir import Florence
    model, sonuc = Florence(), {}
    for kod in ADLAR:
        bgr = gorsel(kod)
        for aci, kod_cv in ACILAR.items():
            g = bgr if kod_cv is None else cv2.rotate(bgr, kod_cv)
            t0 = time.perf_counter()
            tespit = model.oku(g)
            s = round(time.perf_counter() - t0, 1)
            sonuc.setdefault(kod, {})[aci] = {"metinler": [t["metin"] for t in tespit], "sure_s": s}
            print(f"florence {kod} {aci}°: {len(tespit)} metin, {s} s", flush=True)
            CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
