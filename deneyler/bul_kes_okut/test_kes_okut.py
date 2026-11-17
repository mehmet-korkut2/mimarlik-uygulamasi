import pytest
from PIL import Image

from kes_okut import cevaptan_deger, genislet, kes


def test_genislet_yuksekligin_yarisi_kadar():
    # yükseklik 40 -> her yöne 20
    assert genislet((100, 100, 200, 140), 1000, 1000) == (80, 80, 220, 160)


def test_genislet_en_az_pay():
    # yükseklik 10 -> yarısı 5 ama en az 15
    assert genislet((100, 100, 120, 110), 1000, 1000) == (85, 85, 135, 125)


def test_genislet_fotograf_sinirinda_kirpar():
    assert genislet((5, 5, 50, 45), 60, 50) == (0, 0, 60, 50)


def test_kes_kisa_kenari_buyutur():
    resim = Image.new("RGB", (1000, 1000), "white")
    kesit = kes(resim, (100, 100, 200, 140))  # genişletilmiş: 140x80
    assert min(kesit.size) == 224
    assert kesit.size[0] == pytest.approx(140 * 224 / 80, abs=1)


def test_kes_buyuk_kesiti_kucultmez():
    resim = Image.new("RGB", (2000, 2000), "white")
    kesit = kes(resim, (200, 200, 700, 500))  # pay 150 -> 800x600
    assert kesit.size == (800, 600)


@pytest.mark.parametrize("metin, beklenen", [
    ("102", 102), (" 240 ", 240), ("Sayı: 45", 45), ("**90**", 90), ("1,5", 1),
    ("YOK", None), ("yok", None), ("", None), (None, None), ("Bir sayı yok.", None),
])
def test_cevaptan_deger(metin, beklenen):
    assert cevaptan_deger(metin) == beklenen
