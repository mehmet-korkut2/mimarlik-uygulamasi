import pytest

from konum_istem import cevaptan_kutular, piksele_cevir


def test_duz_json_dizisi():
    metin = '[{"bbox_2d": [10, 20, 30, 40], "label": "180"}, {"bbox_2d": [1, 2, 3, 4], "label": "50"}]'
    assert cevaptan_kutular(metin) == [
        {"deger": 180, "kutu": [10, 20, 30, 40]},
        {"deger": 50, "kutu": [1, 2, 3, 4]},
    ]


def test_kod_blogu_icindeki_json():
    metin = '```json\n[{"bbox_2d": [10, 20, 30, 40], "label": "102"}]\n```'
    assert cevaptan_kutular(metin) == [{"deger": 102, "kutu": [10, 20, 30, 40]}]


def test_etikette_birim_ve_sayi_tipi():
    metin = '[{"bbox_2d": [0, 0, 5, 5], "label": "240 cm"}, {"bbox_2d": [0, 0, 5, 5], "label": 45}]'
    assert [k["deger"] for k in cevaptan_kutular(metin)] == [240, 45]


def test_sayi_olmayan_etiket_deger_none():
    metin = '[{"bbox_2d": [0, 0, 5, 5], "label": "h1"}]'
    # "h1" içindeki 1 bir ölçü değil ama filtre onu alır; dünkü kuralla aynı davranış.
    assert cevaptan_kutular(metin)[0]["deger"] == 1
    assert cevaptan_kutular('[{"bbox_2d": [0, 0, 5, 5], "label": "?"}]')[0]["deger"] is None


def test_kutusu_bozuk_oge_atlanmaz_kutu_none():
    metin = '[{"bbox_2d": [0, 0, 5], "label": "90"}, {"label": "10"}]'
    assert cevaptan_kutular(metin) == [{"deger": 90, "kutu": None}, {"deger": 10, "kutu": None}]


def test_kesik_json_kurtarilir():
    # Model cevabı yarıda keserse tamamlanmış nesneler yine alınır.
    metin = '[{"bbox_2d": [1, 2, 3, 4], "label": "180"}, {"bbox_2d": [5, 6'
    assert cevaptan_kutular(metin) == [{"deger": 180, "kutu": [1, 2, 3, 4]}]


def test_json_yoksa_bos_liste():
    assert cevaptan_kutular("okuyamadım") == []
    assert cevaptan_kutular("") == []
    assert cevaptan_kutular(None) == []


def test_binlik_olcekten_piksele():
    # 0–1000 oranlı koordinat -> 1152x2048 fotoğraf pikseli
    assert piksele_cevir([0, 0, 1000, 1000], 1152, 2048) == pytest.approx([0, 0, 1152, 2048])
    assert piksele_cevir([500, 250, 750, 500], 1152, 2048) == pytest.approx([576, 512, 864, 1024])


def test_ters_koseler_duzeltilir():
    assert piksele_cevir([750, 500, 500, 250], 1000, 1000) == pytest.approx([500, 250, 750, 500])
