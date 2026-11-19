"""varsayimlar.kenar_boyu: mimarın cevabına bağlı kenar boyu kuralları (S1, S3)."""

from mimarlik import varsayimlar
from mimarlik.varsayimlar import kenar_boyu


def test_tek_parcali_kenar():
    assert kenar_boyu([180]) == (180, False)


def test_duvar_kapi_duvar_toplami():  # S1
    assert kenar_boyu([10, 90, 15]) == (115, False)


def test_tek_sayi_kenarin_tamami(monkeypatch):  # S3
    assert kenar_boyu([300, None]) == (300, True)
    monkeypatch.setattr(varsayimlar, "TEK_SAYI_KENARIN_TAMAMI", False)
    assert kenar_boyu([300, None]) == (None, False)


def test_eksik_parca_cozulemez():
    assert kenar_boyu([10, None, 15]) == (None, False)
    assert kenar_boyu([None, None]) == (None, False)


def test_standartlar_kalinligi_varsayimlardan_alir():
    from mimarlik import standartlar
    assert standartlar.DIS_DUVAR_KALINLIGI == varsayimlar.DIS_DUVAR_KALINLIGI
    assert standartlar.IC_DUVAR_KALINLIGI == varsayimlar.IC_DUVAR_KALINLIGI
