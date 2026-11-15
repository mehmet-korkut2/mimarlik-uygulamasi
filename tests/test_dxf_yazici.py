"""dxf_yazici modülünün testleri.

Her test, ezdxf belgesini ya doğrudan ya da diske yazıp geri okuyarak kontrol eder.
"""

import ezdxf
import numpy as np
import pytest

from mimarlik.dxf_yazici import cizgi_ekle, kaydet, yeni_cizim
from mimarlik.standartlar import (
    KATMAN_DUVAR,
    KATMAN_RENKLERI,
    OLCU_STILI,
    OLCU_YAZI_YUKSEKLIGI,
)


# --- yeni_cizim -------------------------------------------------------------

def test_yeni_cizim_r2010():
    assert yeni_cizim().dxfversion == "AC1024"


def test_yeni_cizim_varsayilan_birim_cm():
    doc = yeni_cizim()
    assert doc.header["$INSUNITS"] == 5
    assert doc.header["$MEASUREMENT"] == 1


def test_yeni_cizim_mm_birimi():
    assert yeni_cizim("mm").header["$INSUNITS"] == 4


def test_yeni_cizim_bilinmeyen_birim_hata():
    with pytest.raises(ValueError):
        yeni_cizim("inc")


def test_dort_katman_dogru_renkle():
    doc = yeni_cizim()
    assert len(KATMAN_RENKLERI) == 4
    for ad, renk in KATMAN_RENKLERI.items():
        assert doc.layers.get(ad).color == renk


def test_olcu_stili_var():
    stil = yeni_cizim().dimstyles.get(OLCU_STILI)
    assert stil.dxf.dimtxt == OLCU_YAZI_YUKSEKLIGI
    assert stil.dxf.dimtsz > 0  # ok yerine mimari tick


def test_bos_cizim_audit_temiz():
    assert not yeni_cizim().audit().has_errors


# --- cizgi_ekle ve kaydet ---------------------------------------------------

def test_cizgiler_geri_okunur(tmp_path):
    doc = yeni_cizim()
    cizgiler = [(0, 0, 450, 0), (450, 0, 450, 350)]
    cizgi_ekle(doc, cizgiler, KATMAN_DUVAR)
    okunan = ezdxf.readfile(kaydet(doc, tmp_path / "t.dxf"))
    lines = okunan.modelspace().query('LINE[layer=="DUVAR"]')
    assert len(lines) == 2
    assert tuple(lines[0].dxf.start) == pytest.approx((0, 0, 0))
    assert tuple(lines[0].dxf.end) == pytest.approx((450, 0, 0))
    assert tuple(lines[1].dxf.end) == pytest.approx((450, 350, 0))


def test_numpy_koordinatlar(tmp_path):
    # Faz 2'de OpenCV koordinatları numpy tipinde döndürür.
    doc = yeni_cizim()
    cizgi_ekle(doc, [tuple(np.array([0, 0, 10, 0], dtype=np.int32))], KATMAN_DUVAR)
    okunan = ezdxf.readfile(kaydet(doc, tmp_path / "t.dxf"))
    lines = okunan.modelspace().query("LINE")
    assert len(lines) == 1
    assert tuple(lines[0].dxf.end) == pytest.approx((10, 0, 0))


def test_bos_liste_hata_vermez():
    doc = yeni_cizim()
    cizgi_ekle(doc, [], KATMAN_DUVAR)
    assert len(doc.modelspace().query("LINE")) == 0


def test_tanimsiz_katman_hata():
    # ezdxf katman adlarında büyük/küçük harf ayırmaz; biz ayırıyoruz.
    doc = yeni_cizim()
    katman_sayisi = len(doc.layers)
    with pytest.raises(ValueError):
        cizgi_ekle(doc, [(0, 0, 1, 0)], "duvar")
    assert len(doc.layers) == katman_sayisi
    assert len(doc.modelspace().query("LINE")) == 0


def test_sifir_uzunluk_hata():
    with pytest.raises(ValueError):
        cizgi_ekle(yeni_cizim(), [(5, 5, 5, 5)], KATMAN_DUVAR)


def test_yanlis_bicim_hata():
    with pytest.raises(ValueError):
        cizgi_ekle(yeni_cizim(), [(0, 0, 1)], KATMAN_DUVAR)


def test_hatali_cizgi_varsa_hicbiri_eklenmez():
    doc = yeni_cizim()
    with pytest.raises(ValueError):
        cizgi_ekle(doc, [(0, 0, 10, 0), (5, 5, 5, 5)], KATMAN_DUVAR)
    assert len(doc.modelspace().query("LINE")) == 0


def test_ic_ice_klasor_olusturulur(tmp_path):
    yol = kaydet(yeni_cizim(), tmp_path / "a" / "b" / "x.dxf")
    assert yol.exists()
