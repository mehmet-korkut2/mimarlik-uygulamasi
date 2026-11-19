"""okuma: Qwen cevaplarının ayrıştırılması ve Y2 parça görseli (Qwen çağrılmaz)."""

import numpy as np

from mimarlik.eslestirme import Kenar, KenarSonucu, Parca
from mimarlik.okuma import parca_degerlerini_ayristir, parca_gorseli, png, sayilari_ayristir


def test_sayilar_piksele_cevrilir_ve_kose_sirasi_duzelir():
    metin = 'İşte: [{"bbox_2d": [500, 100, 250, 200], "label": "180"}]'
    assert sayilari_ayristir(metin, 2000, 1000) == [(180, (500.0, 100.0, 1000.0, 200.0))]


def test_bozuk_ogeler_atlanir():
    metin = ('[{"bbox_2d": [0,0,10,10], "label": "abc"}, {"bbox_2d": [0,0,10], "label": "90"},'
             ' {"label": "60"}, {"bbox_2d": [0,0,10,10], "label": "60"}]')
    assert [d for d, _ in sayilari_ayristir(metin, 1000, 1000)] == [60]


def test_kesik_cevaptan_tamamlanan_nesneler_kurtarilir():
    metin = '[{"bbox_2d": [0,0,10,10], "label": "102"}, {"bbox_2d": [5,5,'
    assert [d for d, _ in sayilari_ayristir(metin, 1000, 1000)] == [102]


def test_bos_ya_da_json_olmayan_cevap():
    assert sayilari_ayristir("", 10, 10) == []
    assert sayilari_ayristir("bulamadım", 10, 10) == []


def test_parca_degerleri():
    eslem = {"P1": "K1.1", "P2": "K2.1"}
    metin = '```json\n{"P1": [180, "40"], "P2": [], "P9": [5], "P3": "x"}\n```'
    assert parca_degerlerini_ayristir(metin, eslem) == [(180, "K1.1"), (40, "K1.1")]
    assert parca_degerlerini_ayristir("{bozuk", eslem) == []


def _sonuc():
    p = [Parca("K1.1", "K1", "duvar", (10, 10), (190, 10)), Parca("K2.1", "K2", "duvar", (190, 10), (190, 190)),
         Parca("K2.2", "K2", "aciklik", (190, 190), (190, 250))]
    return KenarSonucu(0.0, (Kenar("K1", "yatay", (p[0],), True), Kenar("K2", "dikey", (p[1], p[2]), True)),
                       ("K1", "K2"), ())


def test_parca_gorseli_her_parcayi_etiketler_ve_kopya_uzerinde_cizer():
    bgr = np.full((300, 300, 3), 255, np.uint8)
    resim, eslem = parca_gorseli(bgr, _sonuc())
    assert sorted(eslem) == ["P1", "P2", "P3"]
    assert sorted(eslem.values()) == ["K1.1", "K2.1", "K2.2"]
    assert (bgr == 255).all()                       # girdi değişmez
    assert (resim[10, 30] == (0, 0, 230)).all()     # parça kırmızı çizildi (etiketin dışı)
    assert parca_gorseli(bgr, _sonuc())[1] == eslem  # sabit tohum: aynı numaralar


def test_png():
    assert png(np.zeros((4, 4, 3), np.uint8))[:4] == b"\x89PNG"
