"""geometri.plan_kur: kenar boyları sayılardan, eksikler kapanmadan/ölçekten, kapanma kontrolü."""

import pytest

from mimarlik import varsayimlar
from mimarlik.birlestirme import SonOlcu
from mimarlik.eslestirme import Kenar, KenarSonucu, Parca
from mimarlik.geometri import plan_kur

H = 20.0


def _kenar(kid, yon, *parcalar, konturda=True):
    return Kenar(kid, yon, tuple(Parca(f"{kid}.{n}", kid, t, a, b) for n, (t, a, b) in enumerate(parcalar, 1)),
                 konturda)


def _dikdortgen(alt=None, ic=False):
    """Görüntüde 400x300 px dikdörtgen, saat yönünde: üst, sağ, alt, sol."""
    alt = alt or [("duvar", (400, 300), (0, 300))]
    kenarlar = [_kenar("K1", "yatay", ("duvar", (0, 0), (400, 0))),
                _kenar("K2", "dikey", ("duvar", (400, 0), (400, 300))),
                _kenar("K3", "yatay", *alt),
                _kenar("K4", "dikey", ("duvar", (0, 300), (0, 0)))]
    if ic:
        kenarlar.append(_kenar("K5", "dikey", ("duvar", (200, 0), (200, 100)), konturda=False))
    return KenarSonucu(0.0, tuple(kenarlar), ("K1", "K2", "K3", "K4"), ())


def _o(deger, parca, emin=True):
    return SonOlcu(deger, None, parca, "y2", emin, "" if emin else "x", None, None, parca, "uzunluk")


def test_kapanan_dikdortgen():
    plan = plan_kur(_dikdortgen(), [_o(400, "K1.1"), _o(300, "K2.1"), _o(400, "K3.1"), _o(300, "K4.1")], H)
    assert [k.yon for k in plan.kenarlar] == [(1, 0), (0, -1), (-1, 0), (0, 1)]   # DXF: y yukarı
    assert plan.kenarlar[1].bit == (400, -300)
    assert plan.kapanma["yatay"] == {"fark_cm": 0, "tutuyor": True, "not": "yatay fark 0 cm, tolerans içinde"}
    assert all(k.durum == "olcu" and k.emin for k in plan.kenarlar)


def test_tolerans_icindeki_fark_yazilir():
    plan = plan_kur(_dikdortgen(), [_o(400, "K1.1"), _o(300, "K2.1"), _o(397, "K3.1"), _o(300, "K4.1")], H)
    assert plan.kapanma["yatay"]["not"] == "yatay fark 3 cm, tolerans içinde"
    assert plan.kapanma["yatay"]["tutuyor"]


def test_kapanmayan():
    plan = plan_kur(_dikdortgen(), [_o(400, "K1.1"), _o(300, "K2.1"), _o(360, "K3.1"), _o(300, "K4.1")], H)
    assert plan.kapanma["yatay"] == {"fark_cm": 40, "tutuyor": False, "not": "yatay fark 40 cm, kapanmıyor"}
    assert plan.kapanma["dikey"]["tutuyor"]


def test_tek_bilinmeyen_kapanmadan_hesaplanir():
    plan = plan_kur(_dikdortgen(), [_o(420, "K1.1"), _o(300, "K2.1"), _o(300, "K4.1")], H)
    k3 = plan.kenarlar[2]
    assert (k3.boy, k3.durum, k3.emin) == (420, "hesaplandi", False)
    assert plan.kapanma["yatay"]["fark_cm"] == 0


def test_iki_bilinmeyen_olcekten_tahmin():
    # yatayda iki bilinmeyen (K1, K3) -> ölçekten; dikeyde tek bilinmeyen (K4) -> kapanmadan
    plan = plan_kur(_dikdortgen(), [_o(600, "K2.1")], H)   # 2 cm/px
    assert plan.olcek_cm_px == 2
    assert [(k.boy, k.durum) for k in plan.kenarlar] == [(800, "tahmin"), (600, "olcu"), (800, "tahmin"),
                                                          (600, "hesaplandi")]


def test_duvar_kapi_duvar_toplami_ve_parca_boylari():  # S1
    alt = [("duvar", (400, 300), (300, 300)), ("aciklik", (300, 300), (210, 300)), ("duvar", (210, 300), (0, 300))]
    olculer = [_o(400, "K1.1"), _o(300, "K2.1"), _o(100, "K3.1"), _o(90, "K3.2"), _o(210, "K3.3"), _o(300, "K4.1")]
    k3 = plan_kur(_dikdortgen(alt), olculer, H).kenarlar[2]
    assert k3.boy == 400 and [p.boy for p in k3.parcalar] == [100, 90, 210]
    assert [p.tur for p in k3.parcalar] == ["duvar", "aciklik", "duvar"]


def test_tek_sayi_kenarin_tamami_parcalara_pikselle_dagilir(monkeypatch):  # S3
    alt = [("duvar", (400, 300), (100, 300)), ("duvar", (100, 300), (0, 300))]
    olculer = [_o(400, "K1.1"), _o(300, "K2.1"), _o(400, "K3.1"), _o(300, "K4.1")]
    k3 = plan_kur(_dikdortgen(alt), olculer, H).kenarlar[2]
    assert k3.tek_sayi_tamami and k3.boy == 400
    assert [p.boy for p in k3.parcalar] == [300, 100]
    monkeypatch.setattr(varsayimlar, "TEK_SAYI_KENARIN_TAMAMI", False)
    k3 = plan_kur(_dikdortgen(alt), olculer, H).kenarlar[2]   # parça boyu: 400 + 100 px x 1 cm/px
    assert (k3.boy, k3.durum) == (400, "hesaplandi")         # tek bilinmeyen: kapanmadan


def test_emin_olmayan_olcu_kenari_emin_yapmaz_ve_emin_olan_tercih_edilir():
    olculer = [_o(999, "K1.1", emin=False), _o(400, "K1.1"), _o(300, "K2.1"), _o(400, "K3.1"),
               _o(300, "K4.1", emin=False)]
    plan = plan_kur(_dikdortgen(), olculer, H)
    assert plan.kenarlar[0].boy == 400
    assert not plan.kenarlar[3].emin


def test_ic_duvar_olcekten_cm_ye():
    plan = plan_kur(_dikdortgen(ic=True), [_o(800, "K1.1"), _o(600, "K2.1"), _o(800, "K3.1"), _o(600, "K4.1")], H)
    assert plan.ic_duvarlar == (("K5", (400, 0), (400, -200)),)


def test_egik_fotograf_yonleri():
    import math
    a = math.radians(10)

    def don(p):
        return (p[0] * math.cos(a) - p[1] * math.sin(a), p[0] * math.sin(a) + p[1] * math.cos(a))

    s = _dikdortgen()
    kenarlar = tuple(Kenar(k.id, k.yon, tuple(Parca(p.id, p.kenar_id, p.tur, don(p.bas), don(p.bit))
                                              for p in k.parcalar), k.konturda) for k in s.kenarlar)
    s = KenarSonucu(10.0, kenarlar, s.kontur_sirasi, ())
    plan = plan_kur(s, [_o(400, "K1.1"), _o(300, "K2.1"), _o(400, "K3.1"), _o(300, "K4.1")], H)
    assert [k.yon for k in plan.kenarlar] == [(1, 0), (0, -1), (-1, 0), (0, 1)]


def test_kontur_yoksa_not():
    plan = plan_kur(KenarSonucu(0.0, (), (), ()), [], H)
    assert plan.kenarlar == () and plan.notlar == ("dış kontur bulunamadı",)


def test_kontur_yoksa_bulunan_kenarlar_olcekten():
    s = _dikdortgen()
    s = KenarSonucu(0.0, tuple(Kenar(k.id, k.yon, k.parcalar, False) for k in s.kenarlar), (), ())
    plan = plan_kur(s, [_o(800, "K1.1")], H)                  # 2 cm/px, konturda olmayan kenardan
    assert plan.olcek_cm_px == 2 and plan.notlar == ("dış kontur bulunamadı",)
    assert plan.ic_duvarlar[1] == ("K2", (800, 0), (800, -600))


def test_olcek_yoksa_not():
    plan = plan_kur(_dikdortgen(), [], H)
    assert any("ölçek yok" in n for n in plan.notlar)
    assert plan.kenarlar[0].boy == pytest.approx(400)
