import math

import numpy as np
import pytest

from mimarlik.kenar_bulma import kenarlari_bul
from mimarlik.on_isleme import karakter_yuksekligi, murekkep_maskesi
from tests.sentetik import sentetik_kroki


def _bul(aci=0.0):
    bgr, beklenen = sentetik_kroki(aci)
    maske = murekkep_maskesi(bgr)
    return kenarlari_bul(maske, karakter_yuksekligi(maske)), beklenen


def _uc_uzakligi(parca, a, b):
    """İki doğru parçasının uçları arasındaki en büyük uzaklık (yön fark etmez)."""
    d1 = max(math.dist(parca.bas, a), math.dist(parca.bit, b))
    d2 = max(math.dist(parca.bas, b), math.dist(parca.bit, a))
    return min(d1, d2)


def test_eksen_acisi_duz():
    sonuc, _ = _bul(0)
    assert abs(sonuc.eksen_acisi_derece) < 1


@pytest.mark.parametrize("aci", [4, -4])
def test_eksen_acisi_egik(aci):
    sonuc, _ = _bul(aci)
    assert abs(sonuc.eksen_acisi_derece + aci) < 1


def test_egik_fotografta_kenarlar_yatay_dikey():
    sonuc, _ = _bul(4)
    assert sonuc.kenarlar
    assert all(k.yon in ("yatay", "dikey") for k in sonuc.kenarlar)


def test_birlestirme_ab_tek_cizgi():
    sonuc, beklenen = _bul(0)
    a, b = beklenen["kenarlar"]["AB"]
    yakinlar = [p for k in sonuc.kenarlar for p in k.parcalar if _uc_uzakligi(p, a, b) <= 10]
    assert len(yakinlar) == 1


def test_bos_maske():
    sonuc = kenarlari_bul(np.zeros((100, 100), bool), 20)
    assert sonuc.kenarlar == ()
    assert sonuc.kontur_sirasi == ()
