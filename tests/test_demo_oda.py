"""Örnek oda demosunun testleri.

Demo dosyası diske yazılıp ezdxf ile geri okunur; sayılar tasarım
dokümanındaki geometriyle (dış 450x350 cm, duvar 25 cm) eşleşmeli.
"""

import ezdxf
import pytest

from mimarlik.demo_oda import oda_ciz, oda_geometrisi
from mimarlik.standartlar import KATMAN_DUVAR, KATMAN_RENKLERI


@pytest.fixture
def msp(tmp_path):
    okunan = ezdxf.readfile(oda_ciz(tmp_path / "oda.dxf"))
    return okunan.modelspace()


def test_duvar_16_cizgi(msp):
    assert len(msp.query('LINE[layer=="DUVAR"]')) == 16


def test_kapi_1_cizgi_1_yay(msp):
    assert len(msp.query('LINE[layer=="KAPI"]')) == 1
    yaylar = msp.query('ARC[layer=="KAPI"]')
    assert len(yaylar) == 1
    assert yaylar[0].dxf.radius == pytest.approx(90)
    assert tuple(yaylar[0].dxf.center) == pytest.approx((75, 25, 0))


def test_pencere_3_cizgi(msp):
    cizgiler = msp.query('LINE[layer=="PENCERE"]')
    assert len(cizgiler) == 3
    assert sorted(c.dxf.start[1] for c in cizgiler) == pytest.approx([325, 337.5, 350])


def test_olcu_450_ve_350(msp):
    olculer = msp.query('DIMENSION[layer=="OLCU"]')
    assert sorted(o.get_measurement() for o in olculer) == pytest.approx([350, 450])


def test_dis_sinir_450x350(msp):
    xs, ys = [], []
    for c in msp.query('LINE[layer=="DUVAR"]'):
        xs += [c.dxf.start[0], c.dxf.end[0]]
        ys += [c.dxf.start[1], c.dxf.end[1]]
    assert (min(xs), min(ys), max(xs), max(ys)) == pytest.approx((0, 0, 450, 350))


def test_tum_nesneler_4_katmanda(msp):
    for nesne in msp:
        assert nesne.dxf.layer in KATMAN_RENKLERI


def test_audit_temiz(tmp_path):
    okunan = ezdxf.readfile(oda_ciz(tmp_path / "oda.dxf"))
    assert not okunan.audit().has_errors


def test_geometri_tekrarsiz():
    duvarlar = oda_geometrisi()["cizgiler"][KATMAN_DUVAR]
    assert len(duvarlar) == len(set(duvarlar))
