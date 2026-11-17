import math

import pytest

from mimarlik.bolge_bulma import bolge_olustur, bolgeleri_bul
from mimarlik.eslestirme import nokta_parca_mesafesi
from mimarlik.kenar_bulma import kenarlari_bul
from mimarlik.on_isleme import karakter_yuksekligi, murekkep_maskesi
from tests.sentetik import sentetik_kroki


def _hazirla(aci=0.0):
    bgr, beklenen = sentetik_kroki(aci)
    maske = murekkep_maskesi(bgr)
    h = karakter_yuksekligi(maske)
    return maske, h, kenarlari_bul(maske, h), beklenen


def _ortusme(kutu, bolge_kutusu):
    """kutu alanının bölge kutusu içinde kalan oranı."""
    x1, y1, x2, y2 = kutu
    bx1, by1, bx2, by2 = bolge_kutusu
    g = max(0.0, min(x2, bx2) - max(x1, bx1))
    y = max(0.0, min(y2, by2) - max(y1, by1))
    return g * y / ((x2 - x1) * (y2 - y1))


@pytest.mark.parametrize("aci", [0, 4])
def test_her_sayiyi_tek_bolge_kapsar(aci):
    maske, h, sonuc, beklenen = _hazirla(aci)
    bolgeler = bolgeleri_bul(maske, sonuc, h)
    for ad, kutu in beklenen["sayilar"].items():
        kapsayan = [b for b in bolgeler if _ortusme(kutu, b.kutu) >= 0.5]
        assert len(kapsayan) == 1, ad


def test_180_bolunmez():
    maske, h, sonuc, beklenen = _hazirla()
    bolgeler = bolgeleri_bul(maske, sonuc, h)
    parcali = [b for b in bolgeler if _ortusme(b.kutu, beklenen["sayilar"]["180"]) > 0.5]
    assert len(parcali) == 1


def test_duvar_boyunca_bolge_yok():
    maske, h, sonuc, beklenen = _hazirla()
    bolgeler = bolgeleri_bul(maske, sonuc, h)
    sayi_disi = [b for b in bolgeler if all(_ortusme(k, b.kutu) == 0 for k in beklenen["sayilar"].values())]
    assert sayi_disi == []


def test_duvara_bitisik_kutu_temas_noktasi_verir():
    maske, h, sonuc, _ = _hazirla()
    bolge = bolge_olustur(maske, (805, 480, 870, 520), sonuc, h)   # sağ duvarın (x=800) 5 px sağı
    sag_duvar = [p for k in sonuc.kenarlar for p in k.parcalar
                 if abs(p.bas[0] - 800) < 5 and abs(p.bit[0] - 800) < 5]
    assert bolge.temas is not None
    assert min(nokta_parca_mesafesi(bolge.temas, p) for p in sag_duvar) <= 5


def test_duvardan_uzak_kutu_temas_yok():
    maske, h, sonuc, beklenen = _hazirla()
    assert bolge_olustur(maske, beklenen["sayilar"]["60"], sonuc, h).temas is None


def test_aralikli_yazilmis_sayi_tek_bolge():
    """Gevşek el yazısında rakam aralığı ~0.7–1 karakter boyu olabilir (02"deki "2 0 0")."""
    import cv2
    from tests.sentetik import FONT, MUREKKEP, OLCEK, YAZI_KALINLIK
    bgr, _ = sentetik_kroki()
    maske0 = murekkep_maskesi(bgr)
    h = karakter_yuksekligi(maske0)
    x = 450
    for rakam in "200":
        cv2.putText(bgr, rakam, (x, 400), FONT, OLCEK, MUREKKEP, YAZI_KALINLIK, cv2.LINE_AA)
        (g, _), _ = cv2.getTextSize(rakam, FONT, OLCEK, YAZI_KALINLIK)
        x += g + int(0.6 * h)   # yazı tipi kenar boşluklarıyla mürekkep aralığı ≈ 0.7h
    maske = murekkep_maskesi(bgr)
    sonuc = kenarlari_bul(maske, h)
    kutu = (450, 400 - 30, x, 400)
    assert len([b for b in bolgeleri_bul(maske, sonuc, h) if _ortusme(b.kutu, kutu) > 0.1]) == 1


def test_duvar_dibindeki_kucuk_artik_bolge_degil():
    import cv2
    from tests.sentetik import MUREKKEP
    bgr, _ = sentetik_kroki()
    cv2.rectangle(bgr, (300, 106), (310, 112), MUREKKEP, -1)   # üst duvarın hemen altında 10x6 px leke
    maske = murekkep_maskesi(bgr)
    h = karakter_yuksekligi(maske)
    bolgeler = bolgeleri_bul(maske, kenarlari_bul(maske, h), h)
    assert not [b for b in bolgeler if _ortusme((300, 106, 310, 112), b.kutu) > 0]
