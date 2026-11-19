"""birlestirme: tire varsa geometrik, yoksa Y2; çelişki / gürültü / çift değer -> emin değil."""

from mimarlik.birlestirme import birlestir, gurultu_mu
from mimarlik.eslestirme import Kenar, KenarSonucu, Olcu, Parca

H = 20.0


def _sonuc():
    # K1 konturda (uzun), K2 konturda ama K2.2 kısa (< 2h = 40 px), K3 konturda değil (iç duvar)
    k1 = Kenar("K1", "yatay", (Parca("K1.1", "K1", "duvar", (0, 0), (400, 0)),), True)
    k2 = Kenar("K2", "dikey", (Parca("K2.1", "K2", "duvar", (400, 0), (400, 300)),
                               Parca("K2.2", "K2", "duvar", (400, 300), (400, 330))), True)
    k3 = Kenar("K3", "dikey", (Parca("K3.1", "K3", "duvar", (200, 0), (200, 200)),), False)
    return KenarSonucu(0.0, (k1, k2, k3), ("K1", "K2"), ())


def _olcu(deger, parca, neden):
    return Olcu(deger, (0, 0, 10, 10), parca, neden, "uzunluk")


def test_gurultu():
    s = _sonuc()
    assert not gurultu_mu("K1.1", s, H)
    assert gurultu_mu("K2.2", s, H)        # kısa
    assert gurultu_mu("K3.1", s, H)        # konturda değil
    assert gurultu_mu("K9.9", s, H)        # bilinmeyen


def test_tireli_geometrik_kazanir_uyusursa_emin():
    son, kalan = birlestir((_olcu(180, "K1.1", "isaret"),), (), [(180, "K1.1")], _sonuc(), H)
    assert (son[0].parca_id, son[0].kaynak, son[0].emin) == ("K1.1", "geometrik", True)
    assert kalan == []


def test_tireli_celiskide_emin_degil_ama_geometrik_kalir():
    son, _ = birlestir((_olcu(180, "K1.1", "isaret"),), (), [(180, "K2.1")], _sonuc(), H)
    assert (son[0].parca_id, son[0].emin) == ("K1.1", False)
    assert "çelişki" in son[0].sebep


def test_tiresiz_y2_kazanir():
    son, _ = birlestir((_olcu(240, "K2.1", "en_yakin"),), (), [(240, "K2.1")], _sonuc(), H)
    assert (son[0].parca_id, son[0].kaynak, son[0].emin) == ("K2.1", "y2", True)


def test_tiresiz_celiski_y2_kazanir_emin_degil():
    son, _ = birlestir((_olcu(240, "K1.1", "en_yakin"),), (), [(240, "K2.1")], _sonuc(), H)
    assert (son[0].parca_id, son[0].kaynak, son[0].emin) == ("K2.1", "y2", False)


def test_y2_gurultu_parcasi_emin_degil():
    son, _ = birlestir((_olcu(15, None, None),), (), [(15, "K2.2")], _sonuc(), H)
    assert (son[0].parca_id, son[0].emin) == ("K2.2", False)
    assert "gürültü" in son[0].sebep


def test_y2_baglamadiysa_en_yakin_emin_degil():
    son, _ = birlestir((_olcu(240, "K2.1", "en_yakin"),), (), [], _sonuc(), H)
    assert (son[0].parca_id, son[0].kaynak, son[0].emin) == ("K2.1", "geometrik", False)


def test_yeri_bulunamayan_deger_y2_ile_baglanir():
    son, _ = birlestir((), (300,), [(300, "K1.1")], _sonuc(), H)
    assert (son[0].deger, son[0].bolge, son[0].parca_id, son[0].emin) == (300, None, "K1.1", True)


def test_hicbir_yere_baglanamayan():
    son, _ = birlestir((), (77,), [], _sonuc(), H)
    assert (son[0].parca_id, son[0].kaynak, son[0].emin) == (None, None, False)


def test_tireli_once_tuketir_ayni_degerli_ikinci_okuma_kalan_y2_girdisini_alir():
    olculer = (_olcu(90, "K1.1", "en_yakin"), _olcu(90, "K2.1", "isaret"))
    son, kalan = birlestir(olculer, (), [(90, "K1.1"), (90, "K2.1")], _sonuc(), H)
    assert [o.parca_id for o in son] == ["K1.1", "K2.1"]   # sıra korunur
    assert all(o.emin for o in son) and kalan == []


def test_ayni_parcaya_iki_deger_emin_degil():
    olculer = (_olcu(180, "K1.1", "isaret"), _olcu(40, "K1.1", "en_yakin"))
    son, _ = birlestir(olculer, (), [(40, "K1.1")], _sonuc(), H)
    assert not son[0].emin and not son[1].emin
    assert "2 değer" in son[0].sebep


def test_sadece_y2_girdileri_doner():
    _, kalan = birlestir((_olcu(180, "K1.1", "isaret"),), (), [(180, "K1.1"), (55, "K2.1")], _sonuc(), H)
    assert kalan == [(55, "K2.1")]
