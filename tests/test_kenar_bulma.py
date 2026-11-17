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


# --- Görev 4: duvar/işaret ayrımı, açıklık, parçalar, kontur ---

def _parcalar(sonuc):
    return [p for k in sonuc.kenarlar for p in k.parcalar]


@pytest.mark.parametrize("aci", [0, 4])
def test_kenar_ve_parca_sayilari(aci):
    sonuc, beklenen = _bul(aci)
    assert len(sonuc.kenarlar) == beklenen["kenar_sayisi"]
    assert len(_parcalar(sonuc)) == beklenen["parca_sayisi"]
    assert sum(p.tur == "aciklik" for p in _parcalar(sonuc)) == beklenen["aciklik_sayisi"]


@pytest.mark.parametrize("aci", [0, 4])
def test_acikli_kenarin_parca_turleri(aci):
    sonuc, _ = _bul(aci)
    acikli = [k for k in sonuc.kenarlar if any(p.tur == "aciklik" for p in k.parcalar)]
    assert len(acikli) == 1
    assert [p.tur for p in acikli[0].parcalar] in (["duvar", "aciklik", "duvar"],)


def test_kisa_duvar_isaret_sayilmaz():
    sonuc, beklenen = _bul(0)
    a, b = beklenen["kenarlar"]["FA_alt"]
    assert any(_uc_uzakligi(p, a, b) <= 10 and p.tur == "duvar" for p in _parcalar(sonuc))


@pytest.mark.parametrize("aci", [0, 4])
def test_isaretler(aci):
    sonuc, beklenen = _bul(aci)
    assert len(sonuc.isaretler) == beklenen["isaret_sayisi"]
    duvarlar = [p for p in _parcalar(sonuc) if p.tur == "duvar"]
    from mimarlik.eslestirme import nokta_parca_mesafesi
    for isaret in sonuc.isaretler:
        assert min(nokta_parca_mesafesi(isaret.bas, p) for p in duvarlar) <= 5


@pytest.mark.parametrize("aci", [0, 4])
def test_kontur_sirasi(aci):
    sonuc, beklenen = _bul(aci)
    assert len(sonuc.kontur_sirasi) == 6
    ilk = next(k for k in sonuc.kenarlar if k.id == sonuc.kontur_sirasi[0])
    a, b = beklenen["kenarlar"]["AB"]
    assert all(k.konturda for k in sonuc.kenarlar)
    assert _uc_uzakligi(ilk.parcalar[0], a, b) <= 10 or \
        _uc_uzakligi(_birlesik(ilk), a, b) <= 10


def _birlesik(kenar):
    from mimarlik.eslestirme import Parca
    return Parca("x", "x", "duvar", kenar.parcalar[0].bas, kenar.parcalar[-1].bit)


def test_kalin_leke_eksen_acisini_bozmaz():
    from tests.test_on_isleme import _lekeli_kroki
    bgr, beklenen = _lekeli_kroki()
    maske = murekkep_maskesi(bgr)
    sonuc = kenarlari_bul(maske, karakter_yuksekligi(maske))
    assert abs(sonuc.eksen_acisi_derece) < 1
    assert len(sonuc.kenarlar) == beklenen["kenar_sayisi"]


def test_birlesen_cizginin_yonu_her_zaman_yatay_ya_da_dikey():
    """İki 14°'lik kısa parça (dik kayma 8.5 px ≤ h/3) birleşince 22°'lik çizgi olur; yön yine "yatay" kalmalı."""
    from mimarlik.kenar_bulma import _Cizgi, _birlestir
    a = _Cizgi((0, 0), (29.1, 7.26))
    b = _Cizgi((25, 15), (54.1, 22.26))
    sonuc = _birlestir([a, b], 30.0, 0.0)
    assert len(sonuc) == 1
    assert sonuc[0][1] == "yatay"
