import numpy as np
import pytest

from tests.sentetik import sentetik_kroki

from mimarlik.on_isleme import cizgileri_sil, karakter_yuksekligi, murekkep_maskesi

MAVI_MUREKKEP = (150, 70, 60)   # BGR: koyu mavi tükenmez
GRI_CIZGI = (150, 155, 160)     # defter çizgisi: düşük doygunluk
KAGIT = (215, 222, 225)
KIRMIZI = (40, 40, 200)         # ayraç
SIYAH = (25, 25, 25)            # arka plandaki kumaş


def _resim(renk, boy=(20, 20)):
    return np.full((*boy, 3), renk, dtype=np.uint8)


def test_mavi_murekkep_maskede():
    assert murekkep_maskesi(_resim(MAVI_MUREKKEP)).all()


def test_gri_cizgi_kagit_kirmizi_siyah_maskede_degil():
    for renk in (GRI_CIZGI, KAGIT, KIRMIZI, SIYAH):
        assert not murekkep_maskesi(_resim(renk)).any(), renk


def test_cizgileri_sil_murekkebi_korur_gerisini_beyaz_yapar():
    resim = _resim(GRI_CIZGI, (30, 30))
    resim[10:20, 10:20] = MAVI_MUREKKEP
    sonuc = cizgileri_sil(resim, genislet=0)
    assert (sonuc[10:20, 10:20] == MAVI_MUREKKEP).all()
    assert (sonuc[:5, :5] == 255).all()


def test_genisletme_murekkep_kenarini_korur():
    resim = _resim(KAGIT, (30, 30))
    resim[10:20, 10:20] = MAVI_MUREKKEP
    resim[9, 10:20] = (190, 180, 175)  # kenardaki yumuşak geçiş pikseli (az doygun)
    sonuc = cizgileri_sil(resim, genislet=1)
    assert (sonuc[9, 10:20] == (190, 180, 175)).all()
    assert (sonuc[0, 0] == 255).all()


def test_boyut_ve_tur_korunur():
    resim = _resim(KAGIT, (7, 11))
    sonuc = cizgileri_sil(resim)
    assert sonuc.shape == resim.shape and sonuc.dtype == np.uint8


def test_karakter_yuksekligi_sentetik_yaziya_yakin():
    bgr, _ = sentetik_kroki()
    h = karakter_yuksekligi(murekkep_maskesi(bgr))
    assert 18 <= h <= 40   # FONT_HERSHEY_SIMPLEX 1.2 ölçek ≈ 26 px


def test_karakter_yuksekligi_bos_maskede_hata():
    with pytest.raises(ValueError, match="mürekkep bulunamadı"):
        karakter_yuksekligi(np.zeros((50, 50), bool))
