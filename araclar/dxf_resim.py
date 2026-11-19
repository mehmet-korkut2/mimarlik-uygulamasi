"""DXF -> PNG: AutoCAD açmadan gözle kontrol için kaba önizleme.

Kullanım (repo kökünden):
    .venv/Scripts/python -m araclar.dxf_resim output/02_kolay_tek_oda_300x240.dxf output/02_dxf.png

LINE, ARC, TEXT/MTEXT ve DIMENSION (bloktaki çizgi ve yazılar) katman rengiyle çizilir. Türkçe harfler
ASCII'ye çevrilir (OpenCV yazı tipi). Çıktı bir fotoğraf değil ama output/ altına yazın (.gitignore'da).
"""

import math
import sys
from pathlib import Path

import cv2
import ezdxf
import numpy as np

RENK = {"DUVAR": (40, 40, 40), "KAPI": (0, 160, 220), "OLCU": (0, 150, 0), "KONTROL": (0, 0, 230)}  # BGR
GRI = (120, 120, 120)
TR_ASCII = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def _ogeler(doc):
    """(öğe, katman); ölçülerin blok içeriği ölçünün katmanıyla."""
    for e in doc.modelspace():
        if e.dxftype() == "DIMENSION":
            for b in doc.blocks.get(e.dxf.geometry):
                yield b, e.dxf.layer
        else:
            yield e, e.dxf.layer


def _noktalar(e):
    t = e.dxftype()
    if t == "LINE":
        return [(e.dxf.start.x, e.dxf.start.y), (e.dxf.end.x, e.dxf.end.y)]
    if t == "ARC":
        c, r = e.dxf.center, e.dxf.radius
        return [(c.x - r, c.y - r), (c.x + r, c.y + r)]
    if t in ("TEXT", "MTEXT"):
        return [(e.dxf.insert.x, e.dxf.insert.y)]
    return []


def dxf_resmi(dxf_yolu, png_yolu, en_boy: int = 1400, pay: float = 150) -> Path:
    """DXF'i en uzun kenarı `en_boy` px olan PNG'ye çizer; yazılan yolu döndürür."""
    doc = ezdxf.readfile(str(dxf_yolu))
    ogeler = list(_ogeler(doc))
    pts = [p for e, _ in ogeler for p in _noktalar(e)]
    if not pts:
        raise ValueError(f"DXF'te çizilecek öğe yok: {dxf_yolu}")
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs) - pay, max(xs) + pay, min(ys) - pay, max(ys) + pay
    s = en_boy / max(x1 - x0, y1 - y0)
    img = np.full((int((y1 - y0) * s) + 1, int((x1 - x0) * s) + 1, 3), 255, np.uint8)

    def p(x, y):
        return (int((x - x0) * s), int((y1 - y) * s))   # DXF y yukarı, resim y aşağı

    for e, katman in ogeler:
        renk, t = RENK.get(katman, GRI), e.dxftype()
        if t == "LINE":
            cv2.line(img, p(e.dxf.start.x, e.dxf.start.y), p(e.dxf.end.x, e.dxf.end.y), renk, 2)
        elif t == "ARC":
            a1, a2 = e.dxf.start_angle, e.dxf.end_angle
            a2 = a2 + 360 if a2 < a1 else a2
            c, r = e.dxf.center, e.dxf.radius
            yay = [p(c.x + r * math.cos(math.radians(a)), c.y + r * math.sin(math.radians(a)))
                   for a in np.linspace(a1, a2, 30)]
            cv2.polylines(img, [np.array(yay, np.int32)], False, renk, 1)
        elif t in ("TEXT", "MTEXT"):
            metin = (e.dxf.text if t == "TEXT" else e.text).translate(TR_ASCII)
            cv2.putText(img, metin, p(e.dxf.insert.x, e.dxf.insert.y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, renk, 1,
                        cv2.LINE_AA)
    png_yolu = Path(png_yolu)
    png_yolu.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(png_yolu), img):
        raise ValueError(f"PNG yazılamadı: {png_yolu}")
    return png_yolu


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Kullanım: python -m araclar.dxf_resim <girdi.dxf> <çıktı.png>", file=sys.stderr)
        sys.exit(2)
    print(f"Yazıldı: {dxf_resmi(sys.argv[1], sys.argv[2])}")
