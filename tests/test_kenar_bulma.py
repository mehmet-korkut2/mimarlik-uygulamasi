import math

import numpy as np
import pytest

from mimarlik.kenar_bulma import kenarlari_bul
from mimarlik.on_isleme import karakter_yuksekligi, murekkep_maskesi
from tests.sentetik import sentetik_kroki


def _bul(aci=0.0):
    bgr, beklenen = sentetik_kroki(aci)
    maske = murekkep_maskesi(bgr)
    return kenarlari_bul(maske, karakter_yuksekligi(maske)), beklenen


def _uc_uzakligi(parca, a, b):
    """İki doğru parçasının uçları arasındaki en büyük uzaklık (yön fark etmez)."""
    d1 = max(math.dist(parca.bas, a), math.dist(parca.bit, b))
    d2 = max(math.dist(parca.bas, b), math.dist(parca.bit, a))
    return min(d1, d2)


def test_eksen_acisi_duz():
    sonuc, _ = _bul(0)
    assert abs(sonuc.eksen_acisi_derece) < 1


@pytest.mark.parametrize("aci", [4, -4])
def test_eksen_acisi_egik(aci):
    sonuc, _ = _bul(aci)
    assert abs(sonuc.eksen_acisi_derece + aci) < 1


def test_egik_fotografta_kenarlar_yatay_dikey():
    sonuc, _ = _bul(4)
    assert sonuc.kenarlar
    assert all(k.yon in ("yatay", "dikey") for k in sonuc.kenarlar)


def test_birlestirme_ab_tek_cizgi():
    sonuc, beklenen = _bul(0)
    a, b = beklenen["kenarlar"]["AB"]
    yakinlar = [p for k in sonuc.kenarlar for p in k.parcalar if _uc_uzakligi(p, a, b) <= 10]
    assert len(yakinlar) == 1


def test_bos_maske():
    sonuc = kenarlari_bul(np.zeros((100, 100), bool), 20)
    assert sonuc.kenarlar == ()
    assert sonuc.kontur_sirasi == ()


# --- Görev 4: duvar/işaret ayrımı, açıklık, parçalar, kontur ---

def _parcalar(sonuc):
    return [p for k in sonuc.kenarlar for p in k.parcalar]


@pytest.mark.parametrize("aci", [0, 4])
def test_kenar_ve_parca_sayilari(aci):
    sonuc, beklenen = _bul(aci)
    assert len(sonuc.kenarlar) == beklenen["kenar_sayisi"]
    assert len(_parcalar(sonuc)) == beklenen["parca_sayisi"]
    assert sum(p.tur == "aciklik" for p in _parcalar(sonuc)) == beklenen["aciklik_sayisi"]


@pytest.mark.parametrize("aci", [0, 4])
def test_acikli_kenarin_parca_turleri(aci):
    sonuc, _ = _bul(aci)
    acikli = [k for k in sonuc.kenarlar if any(p.tur == "aciklik" for p in k.parcalar)]
    assert len(acikli) == 1
    assert [p.tur for p in acikli[0].parcalar] in (["duvar", "aciklik", "duvar"],)


def test_kisa_duvar_isaret_sayilmaz():
    sonuc, beklenen = _bul(0)
    a, b = beklenen["kenarlar"]["FA_alt"]
    assert any(_uc_uzakligi(p, a, b) <= 10 and p.tur == "duvar" for p in _parcalar(sonuc))


@pytest.mark.parametrize("aci", [0, 4])
def test_isaretler(aci):
    sonuc, beklenen = _bul(aci)
    assert len(sonuc.isaretler) == beklenen["isaret_sayisi"]
    duvarlar = [p for p in _parcalar(sonuc) if p.tur == "duvar"]
    from mimarlik.eslestirme import nokta_parca_mesafesi
    for isaret in sonuc.isaretler:
        assert min(nokta_parca_mesafesi(isaret.bas, p) for p in duvarlar) <= 5


@pytest.mark.parametrize("aci", [0, 4])
def test_kontur_sirasi(aci):
    sonuc, beklenen = _bul(aci)
    assert len(sonuc.kontur_sirasi) == 6
    ilk = next(k for k in sonuc.kenarlar if k.id == sonuc.kontur_sirasi[0])
    a, b = beklenen["kenarlar"]["AB"]
    assert all(k.konturda for k in sonuc.kenarlar)
    assert _uc_uzakligi(ilk.parcalar[0], a, b) <= 10 or \
        _uc_uzakligi(_birlesik(ilk), a, b) <= 10


def _birlesik(kenar):
    from mimarlik.eslestirme import Parca
    return Parca("x", "x", "duvar", kenar.parcalar[0].bas, kenar.parcalar[-1].bit)


def test_kalin_leke_eksen_acisini_bozmaz():
    from tests.test_on_isleme import _lekeli_kroki
    bgr, beklenen = _lekeli_kroki()
    maske = murekkep_maskesi(bgr)
    sonuc = kenarlari_bul(maske, karakter_yuksekligi(maske))
    assert abs(sonuc.eksen_acisi_derece) < 1
    assert len(sonuc.kenarlar) == beklenen["kenar_sayisi"]


def test_birlesen_cizginin_yonu_her_zaman_yatay_ya_da_dikey():
    """İki 14°'lik kısa parça (dik kayma 8.5 px ≤ h/3) birleşince 22°'lik çizgi olur; yön yine "yatay" kalmalı."""
    from mimarlik.kenar_bulma import _Cizgi, _birlestir
    a = _Cizgi((0, 0), (29.1, 7.26))
    b = _Cizgi((25, 15), (54.1, 22.26))
    sonuc = _birlestir([a, b], 30.0, 0.0)
    assert len(sonuc) == 1
    assert sonuc[0][1] == "yatay"


# --- X işaretleri (mimar S5, KESİN: "çarpı = orada duvar yok") -------------------------------------

def _x_krokisi(x_ciz=True):
    """700x600 oda; sol üstte iç duvarlarla ayrılmış köşe (x=300, y=300). X'ler köşe parçalarının üstünde:
    üst duvarda (200, 100), sol duvarda (100, 200). Gerçek dış hat köşenin içinden dolaşmalı."""
    import cv2
    from tests.sentetik import FONT, KALINLIK, MUREKKEP, OLCEK, YAZI_KALINLIK
    bgr = np.full((800, 900, 3), 255, np.uint8)
    for a, b in [((100, 100), (700, 100)), ((700, 100), (700, 600)), ((700, 600), (100, 600)),
                 ((100, 600), (100, 100)), ((300, 100), (300, 300)), ((100, 300), (300, 300))]:
        cv2.line(bgr, a, b, MUREKKEP, KALINLIK)
    if x_ciz:
        for mx, my in [(200, 100), (100, 200)]:
            cv2.line(bgr, (mx - 25, my - 25), (mx + 25, my + 25), MUREKKEP, KALINLIK)
            cv2.line(bgr, (mx - 25, my + 25), (mx + 25, my - 25), MUREKKEP, KALINLIK)
    for metin, yer in [("400", (450, 80)), ("500", (720, 360)), ("600", (380, 650))]:
        cv2.putText(bgr, metin, yer, FONT, OLCEK, MUREKKEP, YAZI_KALINLIK, cv2.LINE_AA)
    maske = murekkep_maskesi(bgr)
    return maske, karakter_yuksekligi(maske)


def _parca_uzerinde(sonuc, nokta, pay=8):
    from mimarlik.eslestirme import nokta_parca_mesafesi
    return any(nokta_parca_mesafesi(nokta, p) <= pay for k in sonuc.kenarlar for p in k.parcalar)


def test_x_isaretsiz_kontur_dis_dikdortgen():
    sonuc = kenarlari_bul(*_x_krokisi(x_ciz=False))
    assert sonuc.iptaller == ()
    assert len(sonuc.kontur_sirasi) == 4


def test_x_ile_iptal_edilen_kose_parcalari_silinir_kontur_icten_dolasir():
    sonuc = kenarlari_bul(*_x_krokisi())
    assert len(sonuc.iptaller) == 2
    merkezler = sorted(tuple(round(v / 10) * 10 for v in i.merkez) for i in sonuc.iptaller)
    assert merkezler == [(100, 200), (200, 100)]
    assert not _parca_uzerinde(sonuc, (200, 100)) and not _parca_uzerinde(sonuc, (100, 200))
    assert _parca_uzerinde(sonuc, (500, 100)) and _parca_uzerinde(sonuc, (100, 450))   # kalan kısımlar duruyor
    assert len(sonuc.kontur_sirasi) == 6                                                # L biçimli dış hat
    konturda = {k.id for k in sonuc.kenarlar if k.konturda}
    ic_kose = [k for k in sonuc.kenarlar if _parca_uzerinde(KenarSonucuTek(k), (300, 200))]
    assert ic_kose and all(k.id in konturda for k in ic_kose)                           # iç duvar artık dış hat


class KenarSonucuTek:
    """_parca_uzerinde için tek kenarlık sarmalayıcı."""
    def __init__(self, kenar):
        self.kenarlar = (kenar,)


def test_x_cizgileri_sayi_bolgesi_olmaz():
    from mimarlik.bolge_bulma import bolgeleri_bul
    maske, h = _x_krokisi()
    bolgeler = bolgeleri_bul(maske, kenarlari_bul(maske, h), h)
    assert len(bolgeler) == 3   # yalnızca 400, 500, 600


# --- Kapı boşluğu kuralı (3. adım): ipucu = etiket, sayı; yoksa ölçek -------------------------------

def _kapi_krokisi(dik_uc=False):
    """600x500 oda. Sağ duvarda kapı boşluğu (y 300-400).
    dik_uc=False (02 gibi): boşluğun iki yanında parçalar, alttaki 15 px sağa kaymış.
    dik_uc=True (01 gibi): alttaki kısa parça yok; boşluğun karşısı alt duvarın boşta ucu (y=600)."""
    import cv2
    from tests.sentetik import FONT, KALINLIK, MUREKKEP, OLCEK, YAZI_KALINLIK
    bgr = np.full((800, 900, 3), 255, np.uint8)
    cizgiler = [((100, 100), (700, 100)), ((100, 100), (100, 600)), ((700, 100), (700, 300))]
    if dik_uc:
        cizgiler += [((100, 600), (700, 600))]                       # sağ alt köşe yok: 300-600 boşluk
        cizgiler[2] = ((700, 100), (700, 430))
    else:
        cizgiler += [((100, 600), (715, 600)), ((715, 400), (715, 600))]
    for a, b in cizgiler:
        cv2.line(bgr, a, b, MUREKKEP, KALINLIK)
    for metin, yer in [("600", (360, 80)), ("500", (20, 360)), ("90", (740, 360) if not dik_uc else (740, 525))]:
        cv2.putText(bgr, metin, yer, FONT, OLCEK, MUREKKEP, YAZI_KALINLIK, cv2.LINE_AA)
    maske = murekkep_maskesi(bgr)
    return maske, karakter_yuksekligi(maske)


def _ipucu(nokta, kaynak="sayi", deger=90):
    from mimarlik.eslestirme import KapiIpucu
    return (KapiIpucu(nokta, kaynak, deger),)


def test_kapi_ipucusuz_kayik_bosluk_kontur_kapanmaz_bosluk_sorulur():
    sonuc = kenarlari_bul(*_kapi_krokisi())
    assert sonuc.kapilar == () and sonuc.kontur_sirasi == ()
    assert len(sonuc.bosluklar) == 1                                  # kanıtsız aday: "kapı mı?" diye sorulur
    (a, b), = sonuc.bosluklar
    assert {round(a[1] / 50), round(b[1] / 50)} == {6, 8}              # y 300 – 400 boşluğu


@pytest.mark.parametrize("kaynak", ["sayi", "etiket"])
def test_kapi_ipucuyla_kayik_bosluk_aciklik_olur_kontur_kapanir(kaynak):
    maske, h = _kapi_krokisi()
    sonuc = kenarlari_bul(maske, h, _ipucu((760, 350), kaynak))
    assert [(k.kaynak, k.deger) for k in sonuc.kapilar] == [(kaynak, 90)]
    assert len(sonuc.kontur_sirasi) == 4
    sag = [k for k in sonuc.kenarlar if any(p.tur == "aciklik" for p in k.parcalar)]
    assert len(sag) == 1 and [p.tur for p in sag[0].parcalar].count("duvar") == 2


def test_kapi_ipucu_uzaktaysa_kullanilmaz():
    maske, h = _kapi_krokisi()
    sonuc = kenarlari_bul(maske, h, _ipucu((400, 350)))   # oda ortasında: boşluğun ortasına > 5h
    assert sonuc.kapilar == ()


def test_kapi_karsida_uzun_duvarin_ucu_sanal_parca_ile_kapanir():
    maske, h = _kapi_krokisi(dik_uc=True)
    sonuc = kenarlari_bul(maske, h, _ipucu((760, 515)))
    assert len(sonuc.kapilar) == 1 and len(sonuc.kontur_sirasi) == 4
    assert any(p.tur == "aciklik" for k in sonuc.kenarlar for p in k.parcalar)


def test_olcekten_kapi_yok_kanitsiz_bosluk_kapi_olmaz():
    # kullanıcı kararı 2026-11-24: krokiler ölçeksiz; kapının kanıtı etiket ya da kapı genişliğinde sayı
    import inspect
    assert "olcek" not in inspect.signature(kenarlari_bul).parameters
    assert kenarlari_bul(*_kapi_krokisi()).kapilar == ()



def test_kapi_iki_kisa_cizgi_arasi_aday_degil():
    from mimarlik import kenar_bulma as kb
    h = 26.0
    cizgiler = [kb._Cizgi((100, 100), (500, 100)), kb._Cizgi((300, 100), (300, 140)),   # üstten sarkan tik
                kb._Cizgi((300, 240), (300, 280)), kb._Cizgi((100, 280), (500, 280))]   # alttan çıkan tik
    yonler = ["yatay", "dikey", "dikey", "yatay"]
    bag = kb._baglantilar(cizgiler, yonler, 0.75 * h)
    assert kb._kapi_adaylari(cizgiler, yonler, bag, h, 0.75 * h) == []


def test_kapi_duvarin_ortasindan_baslamaz():
    from mimarlik import kenar_bulma as kb
    h = 26.0
    cizgiler = [kb._Cizgi((100, 100), (500, 100)),    # üst duvar
                kb._Cizgi((300, 20), (300, 100)),     # duvarın ortasına dışarıdan değen tik (+ rakam): 3,1h
                kb._Cizgi((300, 220), (300, 300)),    # karşıda bir parça
                kb._Cizgi((100, 300), (500, 300))]
    yonler = ["yatay", "dikey", "dikey", "yatay"]
    bag = kb._baglantilar(cizgiler, yonler, 0.75 * h)
    adaylar = kb._kapi_adaylari(cizgiler, yonler, bag, h, 0.75 * h)
    assert all(1 not in (a[0], a[2]) for a in adaylar)
