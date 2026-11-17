"""Sayı bölgelerini bulma: duvarlar ve ölçü işaretleri silindikten sonra kalan mürekkep (tasarım 5.3).

Bölgeler yalnız "burada yazı var" der; değeri eslestirme.degerleri_ata koyar. Kapı yayı, X gibi
yazı olmayan işaretler de bölge olarak çıkar ve atamada eşsiz kalmaları beklenir.
"""

import math

import cv2
import numpy as np

from mimarlik.eslestirme import Bolge, Kutu, KenarSonucu
from mimarlik.on_isleme import kalin_lekeleri_sil

DUVAR_SILME = 0.6      # h katı: duvar parçaları bu kalınlıkta silinir (kalem izi + pay)
ISARET_SILME = 0.2     # h katı: işaret adayları bu kalınlıkta silinir (rakamı fazla bozmadan)
GRUPLAMA = (0.6, 0.3)  # h katı: rakamları sayıya birleştiren genişletme (yatay, dikey)
TEMAS_TOLERANSI = 0.5  # h katı: kutu bir duvara bu kadar yakınsa "temas" var


def _kutu_mesafesi(p, kutu):
    x1, y1, x2, y2 = kutu
    return math.hypot(max(x1 - p[0], 0.0, p[0] - x2), max(y1 - p[1], 0.0, p[1] - y2))


def _temas(kutu, sonuc, h):
    """Kutuya h·TEMAS_TOLERANSI'ndan yakın en yakın duvar parçası noktası (yoksa None)."""
    en_iyi, en_iyi_d = None, TEMAS_TOLERANSI * h
    for kenar in sonuc.kenarlar:
        for p in kenar.parcalar:
            if p.tur != "duvar":
                continue
            n = max(2, int(math.dist(p.bas, p.bit) / 2))
            for t in np.linspace(0.0, 1.0, n):
                q = (p.bas[0] + t * (p.bit[0] - p.bas[0]), p.bas[1] + t * (p.bit[1] - p.bas[1]))
                d = _kutu_mesafesi(q, kutu)
                if d <= en_iyi_d:
                    en_iyi, en_iyi_d = q, d
    return en_iyi


def bolge_olustur(maske: np.ndarray, kutu: Kutu, sonuc: KenarSonucu, h: float) -> Bolge:
    """Verilen kutudan bölge kurar (gerçek kutular için de kullanılır)."""
    kutu = tuple(float(v) for v in kutu)
    return Bolge(kutu=kutu, temas=_temas(kutu, sonuc, h))


def _cizgi(tuval, a, b, kalinlik):
    cv2.line(tuval, (int(round(a[0])), int(round(a[1]))), (int(round(b[0])), int(round(b[1]))), 0, kalinlik)


def bolgeleri_bul(maske: np.ndarray, sonuc: KenarSonucu, h: float) -> list[Bolge]:
    m = kalin_lekeleri_sil(maske, h).astype(np.uint8)
    for kenar in sonuc.kenarlar:
        for p in kenar.parcalar:
            if p.tur == "duvar":
                _cizgi(m, p.bas, p.bit, max(5, int(DUVAR_SILME * h)))
    for isaret in sonuc.isaretler:
        _cizgi(m, isaret.bas, isaret.bit, max(3, int(ISARET_SILME * h)))

    adet, etiket, ist, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    en_az = (h / 4) ** 2
    temiz = np.zeros_like(m)
    for i in range(1, adet):
        if ist[i, cv2.CC_STAT_AREA] >= en_az:
            temiz[etiket == i] = 1

    cekirdek = cv2.getStructuringElement(cv2.MORPH_RECT, (max(1, int(GRUPLAMA[0] * h)), max(1, int(GRUPLAMA[1] * h))))
    adet, grup = cv2.connectedComponents(cv2.dilate(temiz, cekirdek), connectivity=8)
    bolgeler = []
    for g in range(1, adet):
        ys, xs = np.nonzero((grup == g) & (temiz > 0))
        if len(xs) == 0:
            continue
        bolgeler.append(bolge_olustur(maske, (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1), sonuc, h))
    return sorted(bolgeler, key=lambda b: (b.kutu[1], b.kutu[0]))
