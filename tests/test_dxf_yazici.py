"""dxf_yazici modülünün testleri.

Her test, ezdxf belgesini ya doğrudan ya da diske yazıp geri okuyarak kontrol eder.
"""

import pytest

from mimarlik.dxf_yazici import yeni_cizim
from mimarlik.standartlar import KATMAN_RENKLERI, OLCU_STILI, OLCU_YAZI_YUKSEKLIGI


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
