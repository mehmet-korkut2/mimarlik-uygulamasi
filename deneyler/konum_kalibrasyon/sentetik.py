"""Ö1, denetimli test: konumu bilinen sayılar beyaz görselde -> Qwen3-VL kutuları (ürünün istemi ve dönüşümü).

Kroki boyutu (1152×2048, dikey) iki kez, en/boy etkisi için yatay (2048×1152) bir kez. Fotoğraf yok, sentetik.
Çalıştırma (repo kökünden, Ollama açık): PYTHONIOENCODING=utf-8 .venv/Scripts/python deneyler/konum_kalibrasyon/sentetik.py
"""

import json
import random
import statistics
import sys
from pathlib import Path

import cv2
import numpy as np

KLASOR = Path(__file__).resolve().parent
sys.path.insert(0, str(KLASOR.parents[1]))
from mimarlik import okuma  # noqa: E402

DEGERLER = [180, 50, 40, 108, 120, 15, 90, 10, 140, 300]


def gorsel(gen, yuk, tohum):
    rng = random.Random(tohum)
    img = np.full((yuk, gen, 3), 255, np.uint8)
    yerler = []
    for i, d in enumerate(DEGERLER):   # x'i bütün genişliğe yay: ölçek/öteleme ayrılsın
        x = int(60 + (gen - 260) * i / (len(DEGERLER) - 1))
        y = rng.randint(80, yuk - 80)
        (w, h), _ = cv2.getTextSize(str(d), cv2.FONT_HERSHEY_SIMPLEX, 1.6, 4)
        cv2.putText(img, str(d), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (180, 60, 20), 4)
        yerler.append((d, (x + w / 2, y - h / 2)))
    return img, yerler


def olc(gen, yuk, tohum):
    img, yerler = gorsel(gen, yuk, tohum)
    ham = okuma.qwen_sor(okuma.ISTEM_SAYILAR, okuma.png(img))
    kutular = okuma.sayilari_ayristir(ham, gen, yuk)
    sonuc = []
    for d, (gx, gy) in yerler:
        k = [kk for dd, kk in kutular if dd == d]
        if k:
            qx, qy = min(((a + c) / 2, (b + e) / 2) for a, b, c, e in k)
            sonuc.append({"deger": d, "gercek": [round(gx), round(gy)], "qwen": [round(qx), round(qy)]})
    xs = [s["qwen"][0] / s["gercek"][0] for s in sonuc]
    ys = [s["qwen"][1] / s["gercek"][1] for s in sonuc]
    a_x, b_x = np.polyfit([s["gercek"][0] for s in sonuc], [s["qwen"][0] for s in sonuc], 1)
    a_y, b_y = np.polyfit([s["gercek"][1] for s in sonuc], [s["qwen"][1] for s in sonuc], 1)
    ozet = {"boyut": [gen, yuk], "tohum": tohum, "bulunan": len(sonuc), "x_oran": round(statistics.median(xs), 3),
            "y_oran": round(statistics.median(ys), 3), "x_uyum": [round(float(a_x), 3), round(float(b_x), 1)],
            "y_uyum": [round(float(a_y), 3), round(float(b_y), 1)], "ham": ham, "ciftler": sonuc}
    print(f"{gen}x{yuk} tohum {tohum}: {len(sonuc)}/10 · x oran {ozet['x_oran']} uyum {ozet['x_uyum']} · "
          f"y oran {ozet['y_oran']} uyum {ozet['y_uyum']}")
    return ozet


def main():
    sonuclar = [olc(1152, 2048, 1), olc(1152, 2048, 2), olc(2048, 1152, 3)]
    (KLASOR / "sonuclar").mkdir(exist_ok=True)
    (KLASOR / "sonuclar" / "sentetik.json").write_text(json.dumps(sonuclar, ensure_ascii=False, indent=1),
                                                        encoding="utf-8")


if __name__ == "__main__":
    main()
