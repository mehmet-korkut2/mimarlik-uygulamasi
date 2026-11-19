import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from puanlama_eslestirme import (bolge_puani, ciftleri_cevir, eslestirme_puani, gercek_ciftler,  # noqa: E402
                                 gercek_kenarlar, kenar_puani, kenara_eslestir, mimara_bagli_ciftler,
                                 parcalari_eslestir)
from mimarlik.eslestirme import Bolge, Kenar, KenarSonucu  # noqa: E402


def test_gercek_cift_sayilari():
    assert len(gercek_ciftler("01")) == 10
    assert len(gercek_ciftler("02")) == 14
    assert len(mimara_bagli_ciftler("01")) == 3
    assert len(mimara_bagli_ciftler("02")) == 4


def test_gercek_kenarlar_kontur():
    g = gercek_kenarlar("02")
    assert g.kontur_sirasi[0] == "K1" and len(g.kontur_sirasi) == 10
    assert sum(len(k.parcalar) for k in g.kenarlar) == 16
    assert not next(k for k in g.kenarlar if k.id == "K11").konturda


def test_kendisiyle_eslesme_kimlik():
    g = gercek_kenarlar("01")
    es = parcalari_eslestir(g, g)
    assert all(a == b for a, b in es.items()) and len(es) == 10
    assert kenar_puani(g, g) == {"bulunan": 10, "kaciran": 0, "fazla": 0, "tur_dogru": 10, "kontur_dogru": True}


def test_kaymis_parca_eslesmez():
    g = gercek_kenarlar("01")
    k1 = g.kenarlar[0]
    p = k1.parcalar[0]
    kaymis = replace(p, bas=(p.bas[0], p.bas[1] + 30), bit=(p.bit[0], p.bit[1] + 30))
    b = KenarSonucu(0.0, (Kenar(k1.id, k1.yon, (kaymis,), True),) + g.kenarlar[1:], g.kontur_sirasi, ())
    es = parcalari_eslestir(b, g)
    assert "K1.1" not in es and len(es) == 9


def test_kenara_eslestir_bolunmus_parca():
    g = gercek_kenarlar("01")
    p = g.kenarlar[0].parcalar[0]                      # K1.1'in ilk yarısı tek başına
    yarim = replace(p, id="X1.1", kenar_id="X1", bit=((p.bas[0] + p.bit[0]) / 2, (p.bas[1] + p.bit[1]) / 2))
    b = KenarSonucu(0.0, (Kenar("X1", "yatay", (yarim,), True),), ("X1",), ())
    assert parcalari_eslestir(b, g) == {}
    assert kenara_eslestir(b, g) == {"X1.1": "K1"}


def test_eslestirme_puani():
    assert eslestirme_puani([(40, "K3.1"), (40, "K3.1")], [(40, "K3.1")]) == 1
    assert eslestirme_puani([(300, "K1.1")], [(300, "K1.2")]) == 0
    assert eslestirme_puani([(300, "K1.1")], [(300, "K1.2")], kenar_duzeyi=True) == 1
    assert eslestirme_puani([(300, "K1")], [(300, "K1.2")], kenar_duzeyi=True) == 1


def test_haric_paydayi_da_dusurur():
    gercek = [(15, "K6.3"), (180, "K1.1")]
    tahmin = [(15, "K6.3"), (180, "K2.1")]
    assert eslestirme_puani(tahmin, gercek) == 1
    assert eslestirme_puani(tahmin, gercek, haric=[(15, "K6.3")]) == 0


def test_ciftleri_cevir():
    assert ciftleri_cevir([(40, "K3.1"), (50, "K9.1")], {"K3.1": "K2.1"}) == [(40, "K2.1"), (50, "F:K9.1")]


def test_bolge_puani():
    gercek = [(0, 0, 100, 50), (200, 0, 260, 50)]
    bolgeler = [Bolge((0, 0, 100, 50), None), Bolge((500, 500, 520, 520), None),
                Bolge((200, 0, 228, 50), None), Bolge((232, 0, 260, 50), None)]  # her biri %47
    p = bolge_puani(bolgeler, gercek)
    assert p == {"bulunan": 1, "yazi_olmayan": 1, "bolunmus": 1, "birlesmis": 0}


def test_fazla_cift_dogru_olmayan_her_tahmini_sayar():
    from puanlama_eslestirme import fazla_cift
    gercek = [(40, "K3.1"), (180, "K1.1")]
    assert fazla_cift([(40, "K3.1"), (40, "K3.1"), (45, "F:K9.1"), (180, "K1.1")], gercek) == 2
    assert fazla_cift([], gercek) == 0
