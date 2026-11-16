"""dxf_yazici modülünün testleri.

Her test, ezdxf belgesini ya doğrudan ya da diske yazıp geri okuyarak kontrol eder.
"""

import ezdxf
import numpy as np
import pytest

from mimarlik.dxf_yazici import cizgi_ekle, kaydet, olcu_ekle, yay_ekle, yeni_cizim
from mimarlik.standartlar import (
    KATMAN_DUVAR,
    KATMAN_KAPI,
    KATMAN_OLCU,
    KATMAN_RENKLERI,
    OLCU_STILI,
    OLCU_YAZI_STILI,
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


# --- yay_ekle ve olcu_ekle --------------------------------------------------

def test_yay_geri_okunur(tmp_path):
    doc = yeni_cizim()
    yay_ekle(doc, (75, 25), 90, 0, 90, KATMAN_KAPI)
    okunan = ezdxf.readfile(kaydet(doc, tmp_path / "t.dxf"))
    arc = okunan.modelspace().query('ARC[layer=="KAPI"]')[0]
    assert tuple(arc.dxf.center) == pytest.approx((75, 25, 0))
    assert arc.dxf.radius == pytest.approx(90)
    assert (arc.dxf.start_angle, arc.dxf.end_angle) == pytest.approx((0, 90))


def test_olcu_degeri_ve_stili(tmp_path):
    doc = yeni_cizim()
    olcu_ekle(doc, (0, 0), (450, 0), -60, KATMAN_OLCU)
    okunan = ezdxf.readfile(kaydet(doc, tmp_path / "t.dxf"))
    dim = okunan.modelspace().query('DIMENSION[layer=="OLCU"]')[0]
    assert dim.get_measurement() == pytest.approx(450)
    assert dim.dxf.dimstyle == OLCU_STILI
    assert dim.dxf.defpoint[1] == pytest.approx(-60)  # ölçü çizgisi odanın altında


def test_yay_ve_olcu_tanimsiz_katman_hata():
    doc = yeni_cizim()
    with pytest.raises(ValueError):
        yay_ekle(doc, (0, 0), 1, 0, 90, "KAPII")
    with pytest.raises(ValueError):
        olcu_ekle(doc, (0, 0), (1, 0), 1, "OLCUU")


def test_olculu_cizim_audit_temiz():
    doc = yeni_cizim()
    olcu_ekle(doc, (0, 0), (450, 0), -60, KATMAN_OLCU)
    assert not doc.audit().has_errors


# --- İnceleme sonrası: sonlu sayı, yay/ölçü doğrulaması, Faz 2 girdi biçimleri

@pytest.mark.parametrize("kotu", [float("nan"), float("inf"), float("-inf")])
def test_sonlu_olmayan_koordinat_hata(kotu):
    doc = yeni_cizim()
    with pytest.raises(ValueError):
        cizgi_ekle(doc, [(0, 0, kotu, 0)], KATMAN_DUVAR)
    assert len(doc.modelspace().query("LINE")) == 0


@pytest.mark.parametrize("yaricap", [0, -5, float("nan"), float("inf")])
def test_gecersiz_yaricap_hata(yaricap):
    doc = yeni_cizim()
    with pytest.raises(ValueError):
        yay_ekle(doc, (0, 0), yaricap, 0, 90, KATMAN_KAPI)
    assert len(doc.modelspace().query("ARC")) == 0


def test_yay_sonlu_olmayan_merkez_hata():
    with pytest.raises(ValueError):
        yay_ekle(yeni_cizim(), (float("nan"), 0), 90, 0, 90, KATMAN_KAPI)


def test_olcu_ayni_nokta_hata():
    doc = yeni_cizim()
    with pytest.raises(ValueError):
        olcu_ekle(doc, (5, 5), (5, 5), 10, KATMAN_OLCU)
    assert len(doc.modelspace().query("DIMENSION")) == 0


def test_olcu_sonlu_olmayan_deger_hata():
    with pytest.raises(ValueError):
        olcu_ekle(yeni_cizim(), (0, 0), (450, float("inf")), -60, KATMAN_OLCU)
    with pytest.raises(ValueError):
        olcu_ekle(yeni_cizim(), (0, 0), (450, 0), float("nan"), KATMAN_OLCU)


def test_numpy_n4_dizi_dogrudan(tmp_path):
    # Faz 2: (N, 4) float64 dizisi doğrudan cizgiler olarak verilebilmeli.
    doc = yeni_cizim()
    dizi = np.array([[0, 0, 100, 0], [100, 0, 100, 50.5]], dtype=np.float64)
    cizgi_ekle(doc, dizi, KATMAN_DUVAR)
    lines = ezdxf.readfile(kaydet(doc, tmp_path / "t.dxf")).modelspace().query("LINE")
    assert len(lines) == 2
    assert tuple(lines[1].dxf.end) == pytest.approx((100, 50.5, 0))


def test_hough_n14_bicimi_anlasilir_hata():
    # OpenCV HoughLinesP (N, 1, 4) döndürür; Faz 2 bunu (N, 4)'e çevirmeli.
    dizi = np.array([[[0, 0, 100, 0]]], dtype=np.int32)
    with pytest.raises(ValueError, match="4 sayı"):
        cizgi_ekle(yeni_cizim(), dizi, KATMAN_DUVAR)


def test_kaydet_gorunumu_cizime_ortalar(tmp_path):
    # Mimar dosyayı açınca çizimin tamamını ortada görmeli (zoom extents).
    doc = yeni_cizim()
    cizgi_ekle(doc, [(1000, 2000, 1450, 2000), (1450, 2000, 1450, 2350)], KATMAN_DUVAR)
    okunan = ezdxf.readfile(kaydet(doc, tmp_path / "t.dxf"))
    vp = okunan.viewports.get("*Active")[0]
    assert tuple(vp.dxf.center)[:2] == pytest.approx((1225, 2175))
    assert vp.dxf.height >= 350


# --- AutoCAD'de ölçü yazısı görünmüyordu (audit() bunu yakalamaz) -----------
# Testler diske yazılıp geri okunan dosyada yapılır: AutoCAD'in gördüğü budur.

@pytest.fixture
def olculu_okunan(tmp_path):
    doc = yeni_cizim()
    olcu_ekle(doc, (0, 0), (450, 0), -60, KATMAN_OLCU)
    return ezdxf.readfile(kaydet(doc, tmp_path / "t.dxf"))


def test_olcu_stili_var_olan_yazi_stiline_isaret_eder(olculu_okunan):
    stil = olculu_okunan.dimstyles.get(OLCU_STILI)
    assert stil.dxf.get("dimtxsty") == OLCU_YAZI_STILI
    assert OLCU_YAZI_STILI in olculu_okunan.styles


def test_baslik_dimstyle_cizimde_var(olculu_okunan):
    assert olculu_okunan.header["$DIMSTYLE"] == OLCU_STILI
    assert olculu_okunan.header["$DIMSTYLE"] in olculu_okunan.dimstyles


def test_olcu_blogundaki_yazinin_stili_tanimli(olculu_okunan):
    dim = olculu_okunan.modelspace().query("DIMENSION")[0]
    blok = olculu_okunan.blocks.get(dim.dxf.geometry)
    yazilar = [e for e in blok if e.dxftype() == "MTEXT"]
    assert len(yazilar) == 1
    assert yazilar[0].dxf.style in olculu_okunan.styles
