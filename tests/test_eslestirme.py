import json

import pytest

from mimarlik.eslestirme import (Bolge, Kenar, KenarSonucu, Kroki, Olcu, Parca, kroki_sozluk,
                                 nokta_parca_mesafesi, parcayi_bul)


def _parca(pid, bas, bit, tur="duvar"):
    return Parca(id=pid, kenar_id=pid.split(".")[0], tur=tur, bas=bas, bit=bit)


def test_nokta_parca_dik_mesafe():
    assert nokta_parca_mesafesi((5, 3), _parca("K1.1", (0, 0), (10, 0))) == pytest.approx(3)


def test_nokta_parca_izdusum_disinda_uca_mesafe():
    assert nokta_parca_mesafesi((13, 4), _parca("K1.1", (0, 0), (10, 0))) == pytest.approx(5)


def test_parcayi_bul_yakini_secer_tolerans_disinda_none():
    p1 = _parca("K1.1", (0, 0), (100, 0))
    p2 = _parca("K2.1", (0, 50), (100, 50))
    kenarlar = (Kenar("K1", "yatay", (p1,), True), Kenar("K2", "yatay", (p2,), True))
    assert parcayi_bul((50, 10), kenarlar, tolerans=20) == p1
    assert parcayi_bul((50, 40), kenarlar, tolerans=20) == p2
    assert parcayi_bul((50, 25), kenarlar, tolerans=20) is None


def test_kroki_json_a_cevrilir():
    p = _parca("K1.1", (0, 0), (100, 0))
    kroki = Kroki(eksen_acisi_derece=0.0, kenarlar=(Kenar("K1", "yatay", (p,), True),), kontur_sirasi=("K1",),
                  olculer=(Olcu(180, (10, 10, 50, 30), "K1.1", "isaret", "uzunluk"),),
                  yeri_bulunamayan=(45,), okunmamis_bolgeler=((0, 0, 5, 5),))
    veri = json.loads(json.dumps(kroki_sozluk(kroki)))
    assert veri["kenarlar"][0]["parcalar"][0]["tur"] == "duvar"
    assert veri["olculer"][0]["parca_id"] == "K1.1"
    assert veri["yeri_bulunamayan"] == [45]


def test_kenar_sonucu_ve_bolge_olusturulur():
    s = KenarSonucu(eksen_acisi_derece=1.5, kenarlar=(), kontur_sirasi=(), isaretler=())
    assert s.kenarlar == ()
    assert Bolge(kutu=(0, 0, 1, 1), temas=None).temas is None
