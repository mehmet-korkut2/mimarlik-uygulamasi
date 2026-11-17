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


# --- Görev 6: değer atama ---

from mimarlik.eslestirme import HANE_KATSAYISI, W_HANE, degerleri_ata, hane_tahmini  # noqa: E402

BOYUT = (1000, 1000)  # köşegen ≈ 1414


def _b(x1, y1, x2, y2):
    return Bolge(kutu=(x1, y1, x2, y2), temas=None)


def test_hane_tahmini_genislik_orani():
    assert hane_tahmini((0, 0, 2 * HANE_KATSAYISI * 30, 30)) == pytest.approx(2)


def test_yakin_kutu_atanir():
    b1, b2 = _b(100, 100, 150, 130), _b(500, 500, 550, 530)
    atanmis, yok, okunmamis = degerleri_ata([b1, b2], [(40, (505, 505, 545, 525)), (90, (95, 95, 150, 135))], BOYUT)
    assert sorted(atanmis, key=lambda a: a[1]) == [(b2, 40), (b1, 90)]
    assert yok == [] and okunmamis == []


def test_fazla_deger_yeri_bulunamayan():
    b1, b2 = _b(100, 100, 150, 130), _b(500, 500, 550, 530)
    ogeler = [(40, (100, 100, 150, 130)), (90, (500, 500, 550, 530)), (45, (120, 110, 160, 140))]
    atanmis, yok, _ = degerleri_ata([b1, b2], ogeler, BOYUT)
    assert len(atanmis) == 2 and len(yok) == 1


def test_uzak_kutu_atanmaz():
    b1 = _b(100, 100, 150, 130)
    atanmis, yok, okunmamis = degerleri_ata([b1], [(40, (525, 525, 575, 555))], BOYUT)  # ~600 px, köşegenin %42'si
    assert atanmis == [] and yok == [40] and okunmamis == [b1]


def test_ayni_deger_iki_bolgeye():
    b1, b2 = _b(100, 100, 150, 130), _b(300, 100, 350, 130)
    atanmis, _, _ = degerleri_ata([b1, b2], [(40, (100, 100, 150, 130)), (40, (300, 100, 350, 130))], BOYUT)
    assert sorted(a[1] for a in atanmis) == [40, 40]
    assert {a[0] for a in atanmis} == {b1, b2}


def test_hane_ipucu_karari_degistirir():
    # dar bölge: 2 hane (genişlik 2·0.8·30=48), geniş bölge: 3 hane (72); ikisi de 30 yüksek
    dar, genis = _b(100, 100, 148, 130), _b(300, 100, 372, 130)
    # kutular iki bölgenin arasında, ikisi de geniş bölgeye biraz daha yakın (ipucusuz toplam: 210 px/214 px)
    ogeler = [(40, (213, 100, 261, 130)), (240, (199, 100, 271, 130))]
    hane_ile, _, _ = degerleri_ata([dar, genis], ogeler, BOYUT, w_hane=W_HANE)
    assert dict((d, b) for b, d in hane_ile)[240] == genis
    ipucusuz, _, _ = degerleri_ata([dar, genis], ogeler, BOYUT, w_hane=0)
    assert dict((d, b) for b, d in ipucusuz)[40] == genis


# --- Görev 7: bağlama ve Kroki ---

from mimarlik.bolge_bulma import bolge_olustur  # noqa: E402
from mimarlik.eslestirme import anlam, bagla, kroki_kur  # noqa: E402
from mimarlik.kenar_bulma import kenarlari_bul  # noqa: E402
from mimarlik.on_isleme import karakter_yuksekligi, murekkep_maskesi  # noqa: E402
from tests.sentetik import sentetik_kroki  # noqa: E402


def _sentetik():
    bgr, beklenen = sentetik_kroki()
    maske = murekkep_maskesi(bgr)
    h = karakter_yuksekligi(maske)
    return maske, h, kenarlari_bul(maske, h), beklenen


def _kenar_bul(sonuc, a, b, tol=10):
    """Uçları (yön fark etmez) a, b'ye ≤ tol olan kenar."""
    import math
    for k in sonuc.kenarlar:
        bas, bit = k.parcalar[0].bas, k.parcalar[-1].bit
        if (math.dist(bas, a) <= tol and math.dist(bit, b) <= tol) or (math.dist(bas, b) <= tol and math.dist(bit, a) <= tol):
            return k
    raise AssertionError(f"kenar yok: {a}-{b}")


@pytest.mark.parametrize("sayi, kenar_adi, nedenler", [
    ("180", "AB", {"isaret"}),
    ("240", "DE", {"isaret"}),
    ("60", "EF", {"en_yakin"}),
    ("102", "EF", {"isaret", "temas"}),   # işaret rakamların içinden geçiyor (Review Focus 4)
])
def test_bagla(sayi, kenar_adi, nedenler):
    maske, h, sonuc, beklenen = _sentetik()
    bolge = bolge_olustur(maske, beklenen["sayilar"][sayi], sonuc, h)
    parca, neden = bagla(bolge, sonuc, h)
    kenar = _kenar_bul(sonuc, *beklenen["kenarlar"][kenar_adi])
    assert parca is not None and parca.kenar_id == kenar.id
    assert neden in nedenler


def test_anlam():
    _, _, sonuc, beklenen = _sentetik()
    acikli = next(k for k in sonuc.kenarlar if any(p.tur == "aciklik" for p in k.parcalar))
    ab = _kenar_bul(sonuc, *beklenen["kenarlar"]["AB"])
    assert anlam(next(p for p in acikli.parcalar if p.tur == "aciklik"), acikli) == "bilinmiyor"
    assert anlam(next(p for p in acikli.parcalar if p.tur == "duvar"), acikli) == "bilinmiyor"
    assert anlam(ab.parcalar[0], ab) == "uzunluk"


def test_kroki_kur():
    maske, h, sonuc, beklenen = _sentetik()
    atanmis = [(bolge_olustur(maske, beklenen["sayilar"][s], sonuc, h), int(s)) for s in ("180", "60")]
    kroki = kroki_kur(sonuc, atanmis, [45], [], h)
    assert len(kroki.olculer) == 2
    assert kroki.yeri_bulunamayan == (45,)
    assert kroki.kontur_sirasi == sonuc.kontur_sirasi
    veri = json.loads(json.dumps(kroki_sozluk(kroki)))
    assert {o["deger"] for o in veri["olculer"]} == {180, 60}
    assert all(o["anlam"] == "uzunluk" for o in veri["olculer"])


# --- Final inceleme düzeltmeleri ---

from mimarlik.eslestirme import IsaretAdayi  # noqa: E402


def _uc_parcali_kenar(ters):
    """K1: duvar 0–200, açıklık 200–300, duvar 300–600 (y=100). ters=True: alt/sol kenarlardaki gibi ters sıra."""
    p = [Parca("K1.1", "K1", "duvar", (0, 100), (200, 100)), Parca("K1.2", "K1", "aciklik", (200, 100), (300, 100)),
         Parca("K1.3", "K1", "duvar", (300, 100), (600, 100))]
    if ters:
        p = [Parca(q.id, q.kenar_id, q.tur, q.bit, q.bas) for q in reversed(p)]
    return KenarSonucu(0.0, (Kenar("K1", "yatay", tuple(p), True),), ("K1",),
                       (IsaretAdayi(bas=(300, 100), bit=(300, 140)),))


@pytest.mark.parametrize("ters", [False, True])
def test_sinirdaki_isaret_sayinin_ustundeki_parcaya_baglanir(ters):
    sonuc = _uc_parcali_kenar(ters)
    parca, neden = bagla(Bolge(kutu=(310, 135, 450, 170), temas=None), sonuc, 30.0)
    assert (parca.id, neden) == ("K1.3", "isaret")


@pytest.mark.parametrize("ters", [False, True])
def test_sinirdaki_temas_sayinin_ustundeki_parcaya_baglanir(ters):
    sonuc = _uc_parcali_kenar(ters)
    sonuc = KenarSonucu(0.0, sonuc.kenarlar, sonuc.kontur_sirasi, ())
    parca, neden = bagla(Bolge(kutu=(305, 110, 450, 140), temas=(300, 100)), sonuc, 30.0)
    assert (parca.id, neden) == ("K1.3", "temas")


@pytest.mark.parametrize("ters", [False, True])
def test_kosedeki_en_yakin_sayinin_yanindaki_duvara_baglanir(ters):
    """Köşe (0,0); sayının merkezi iki duvara da köşe noktası üzerinden eşit uzak ama yatay duvarın izdüşümünde."""
    yatay = Kenar("K1", "yatay", (Parca("K1.1", "K1", "duvar", (0, 0), (300, 0)),), True)
    dikey = Kenar("K2", "dikey", (Parca("K2.1", "K2", "duvar", (0, 0), (0, -300)),), True)
    kenarlar = (dikey, yatay) if ters else (yatay, dikey)
    sonuc = KenarSonucu(0.0, kenarlar, ("K1", "K2"), ())
    # merkez (0, 30): yatay duvara dik mesafe 30 (izdüşüm x=0, uçta), dikey duvara da 30 (uç (0,0))
    parca, neden = bagla(Bolge(kutu=(-20, 20, 20, 40), temas=None), sonuc, 30.0)
    assert neden == "en_yakin" and parca.id == "K1.1"
