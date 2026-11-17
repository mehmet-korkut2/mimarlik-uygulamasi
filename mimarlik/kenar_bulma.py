"""Mürekkep maskesinden kenar (duvar) bulma.

Adımlar (tasarım 5.2): çizgi parçaları (Hough) -> eksen açısı -> doğrudaş birleştirme -> ...
Bütün eşikler karakter yüksekliği h'nin katıdır.
"""

import math

import cv2
import numpy as np

from mimarlik.eslestirme import Kenar, KenarSonucu, Parca

ACI_TOLERANSI = 15.0      # derece: eksene bu kadar yakın çizgi yatay/dikey sayılır
BIRLESTIRME_ACISI = 10.0  # derece: doğrudaş sayılmak için en büyük açı farkı


class _Cizgi:
    """Doğru parçası; birleştirilmiş çizgiler de bu sınıftadır."""

    __slots__ = ("bas", "bit")

    def __init__(self, bas, bit):
        self.bas, self.bit = (float(bas[0]), float(bas[1])), (float(bit[0]), float(bit[1]))

    @property
    def uzunluk(self):
        return math.dist(self.bas, self.bit)

    @property
    def aci(self):
        """atan2(dy, dx), derece, (-90, 90]."""
        a = math.degrees(math.atan2(self.bit[1] - self.bas[1], self.bit[0] - self.bas[0]))
        if a <= -90:
            a += 180
        elif a > 90:
            a -= 180
        return a


def _katla(a):
    """Açıyı 90°'lik katlarla (-45, 45] aralığına getirir."""
    while a <= -45:
        a += 90
    while a > 45:
        a -= 90
    return a


def _cizgi_parcalari(maske, h):
    cizgiler = cv2.HoughLinesP(maske.astype(np.uint8) * 255, rho=1, theta=np.pi / 360,
                               threshold=max(10, int(h / 2)), minLineLength=h, maxLineGap=h / 4)
    if cizgiler is None:
        return []
    return [_Cizgi((x1, y1), (x2, y2)) for x1, y1, x2, y2 in np.asarray(cizgiler).reshape(-1, 4)]


def _eksen_acisi(parcalar):
    """Uzunlukla ağırlıklı, 90°'ye göre katlanmış ortalama açı (4θ üzerinden dairesel ortalama)."""
    if not parcalar:
        return 0.0
    s = sum(p.uzunluk * math.sin(math.radians(4 * p.aci)) for p in parcalar)
    c = sum(p.uzunluk * math.cos(math.radians(4 * p.aci)) for p in parcalar)
    return _katla(math.degrees(math.atan2(s, c)) / 4)


def _yon(aci, eksen):
    """"yatay" | "dikey" | None (eğik): çizginin eksen açısına göre yönü."""
    d = (aci - eksen) % 180
    if d <= ACI_TOLERANSI or d >= 180 - ACI_TOLERANSI:
        return "yatay"
    if abs(d - 90) <= ACI_TOLERANSI:
        return "dikey"
    return None


def _aci_farki(a, b):
    d = abs(a - b) % 180
    return min(d, 180 - d)


def _birlestirilebilir(a, b, h):
    if _aci_farki(a.aci, b.aci) > BIRLESTIRME_ACISI:
        return False
    # b'nin uçlarının a'nın doğrusuna dik uzaklığı ve a'nın yönündeki boşluk
    ux, uy = a.bit[0] - a.bas[0], a.bit[1] - a.bas[1]
    n = math.hypot(ux, uy)
    ux, uy = ux / n, uy / n
    def dik(p):
        return abs((p[0] - a.bas[0]) * uy - (p[1] - a.bas[1]) * ux)
    def boy(p):
        return (p[0] - a.bas[0]) * ux + (p[1] - a.bas[1]) * uy
    if max(dik(b.bas), dik(b.bit)) > h / 3:
        return False
    t1, t2 = sorted((boy(b.bas), boy(b.bit)))
    bosluk = max(t1 - a.uzunluk, -t2, 0.0)
    return bosluk <= h / 2


def _uydur(grup):
    """Grup parçalarının uçlarından (uzunlukla ağırlıklı) en küçük kareler doğrusu ve uç noktaları."""
    noktalar, agirlik = [], []
    for p in grup:
        for q in (p.bas, p.bit):
            noktalar.append(q)
            agirlik.append(p.uzunluk)
    P = np.array(noktalar)
    w = np.array(agirlik)[:, None]
    merkez = (P * w).sum(0) / w.sum()
    kov = ((P - merkez) * w).T @ (P - merkez)
    _, vektorler = np.linalg.eigh(kov)
    u = vektorler[:, -1]
    t = (P - merkez) @ u
    return _Cizgi(merkez + t.min() * u, merkez + t.max() * u)


def _birlestir(parcalar, h):
    """Doğrudaş ve üst üste binen (ya da arası ≤ h/2) parçaları tek çizgiye birleştirir."""
    ebeveyn = list(range(len(parcalar)))

    def kok(i):
        while ebeveyn[i] != i:
            ebeveyn[i] = ebeveyn[ebeveyn[i]]
            i = ebeveyn[i]
        return i

    for i in range(len(parcalar)):
        for j in range(i + 1, len(parcalar)):
            if kok(i) != kok(j) and (_birlestirilebilir(parcalar[i], parcalar[j], h)
                                     or _birlestirilebilir(parcalar[j], parcalar[i], h)):
                ebeveyn[kok(i)] = kok(j)
    gruplar = {}
    for i, p in enumerate(parcalar):
        gruplar.setdefault(kok(i), []).append(p)
    return [_uydur(g) for g in gruplar.values()]


def kenarlari_bul(maske: np.ndarray, h: float) -> KenarSonucu:
    parcalar = _cizgi_parcalari(maske, h)
    eksen = _eksen_acisi(parcalar)
    eksenli = [p for p in parcalar if _yon(p.aci, eksen)]
    cizgiler = _birlestir(eksenli, h)
    kenarlar = []
    for i, c in enumerate(sorted(cizgiler, key=lambda c: (c.bas[1], c.bas[0])), 1):
        kid = f"K{i}"
        kenarlar.append(Kenar(kid, _yon(c.aci, eksen), (Parca(f"{kid}.1", kid, "duvar", c.bas, c.bit),), False))
    return KenarSonucu(eksen, tuple(kenarlar), (), ())
