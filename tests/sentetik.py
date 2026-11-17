"""Testler için kodla çizilmiş oda krokisi (planın "Ortak test görüntüsü" bölümü).

Gerçek fotoğraflara bağımlı olmadan kenar bulma, bölge bulma ve bağlamayı test etmek için.
"""

import cv2
import numpy as np

MUREKKEP = (150, 70, 60)   # BGR, mavi tükenmez
KALINLIK = 4
FONT, OLCEK, YAZI_KALINLIK = cv2.FONT_HERSHEY_SIMPLEX, 1.2, 2
BOYUT = (900, 1000)  # (yükseklik, genişlik)

A, B, C, D, E, F = (100, 100), (700, 100), (700, 300), (800, 300), (800, 700), (100, 700)
DUVARLAR = [(A, B), (B, C), (C, D), (D, E), (E, F),
            (F, (100, 670)),            # 30 px kısa duvar
            ((100, 540), A)]            # açıklık (100,670)-(100,540)
ISARETLER = [((400, 100), (400, 70)), ((800, 500), (830, 500)), ((300, 700), (300, 775))]
SAYILAR = {"180": (360, 60), "240": (835, 515), "60": (420, 760), "102": (230, 770)}


def _yazi_kutusu(metin, sol_alt):
    (g, y), _ = cv2.getTextSize(metin, FONT, OLCEK, YAZI_KALINLIK)
    x, alt = sol_alt
    return (x, alt - y, x + g, alt)


def sentetik_kroki(aci_derece: float = 0.0) -> tuple[np.ndarray, dict]:
    bgr = np.full((*BOYUT, 3), 255, np.uint8)
    for a, b in DUVARLAR + ISARETLER:
        cv2.line(bgr, a, b, MUREKKEP, KALINLIK)
    for metin, sol_alt in SAYILAR.items():
        cv2.putText(bgr, metin, sol_alt, FONT, OLCEK, MUREKKEP, YAZI_KALINLIK, cv2.LINE_AA)

    kenarlar = {"AB": (A, B), "BC": (B, C), "CD": (C, D), "DE": (D, E), "EF": (E, F),
                "FA_alt": (F, (100, 670)), "FA_ust": ((100, 540), A)}
    sayilar = {m: _yazi_kutusu(m, s) for m, s in SAYILAR.items()}

    if aci_derece:
        matris = cv2.getRotationMatrix2D((BOYUT[1] / 2, BOYUT[0] / 2), aci_derece, 1.0)
        bgr = cv2.warpAffine(bgr, matris, (BOYUT[1], BOYUT[0]), borderValue=(255, 255, 255))

        def don(p):
            x, y = p
            return (matris[0, 0] * x + matris[0, 1] * y + matris[0, 2],
                    matris[1, 0] * x + matris[1, 1] * y + matris[1, 2])

        kenarlar = {k: (don(a), don(b)) for k, (a, b) in kenarlar.items()}
        sayilar = {m: _kutu_don(k, don) for m, k in sayilar.items()}

    beklenen = {"kenar_sayisi": 6, "parca_sayisi": 8, "aciklik_sayisi": 1, "isaret_sayisi": 3,
                "sayilar": sayilar, "kenarlar": kenarlar}
    return bgr, beklenen


def _kutu_don(kutu, don):
    x1, y1, x2, y2 = kutu
    koseler = [don(p) for p in ((x1, y1), (x2, y1), (x1, y2), (x2, y2))]
    xs, ys = [p[0] for p in koseler], [p[1] for p in koseler]
    return (min(xs), min(ys), max(xs), max(ys))
