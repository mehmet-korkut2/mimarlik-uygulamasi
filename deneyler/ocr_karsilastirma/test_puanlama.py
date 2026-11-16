"""Puanlama testleri: puanlama yanlışsa deneyin tüm sonucu yanlış olur."""

from puanlama import puanla, sayilari_al


def test_sayilari_al_metinden_tam_sayilar():
    assert sayilari_al(["180", "-50", "uo 40", "24°", "GIPTA"]) == [180, 50, 40, 24]


def test_sayilari_al_aralik_disini_atar():
    assert sayilari_al(["0", "12345", "7"]) == [7]


def test_sayilari_al_sayi_listesi_de_kabul_eder():
    assert sayilari_al([180, "50"]) == [180, 50]


def test_puanla_tekrarlari_dogru_sayar():
    # Gerçekte dört 40 var; altı kez okunursa 4 doğru + 2 fazla.
    p = puanla([40] * 6, [40, 40, 40, 40, 45])
    assert (p["dogru"], p["fazla"], p["kacirilan"]) == (4, 2, 1)


def test_puanla_eksik_ve_uydurma():
    p = puanla([180, 999], [180, 50])
    assert (p["dogru"], p["fazla"], p["kacirilan"]) == (1, 1, 1)
    assert p["fazla_degerler"] == [999]
    assert p["kacirilan_degerler"] == [50]


def test_puanla_bos_okuma():
    p = puanla([], [10, 20])
    assert (p["dogru"], p["fazla"], p["kacirilan"]) == (0, 0, 2)


# --- Model cevabını ayrıştırma (istem.cevaptan_sayilar)

from istem import cevaptan_sayilar


def test_cevap_json_dizisi():
    assert cevaptan_sayilar("[180, 50, 40]") == [180, 50, 40]


def test_cevap_kod_blogu_ve_aciklama():
    # Dizi dışındaki sayılar ("2 sayı") sayılmaz; sadece ilk dizi alınır.
    metin = '```json\n[300, 45]\n```\nNot: 2 sayı belirsizdi.'
    assert cevaptan_sayilar(metin) == [300, 45]


def test_cevap_dizisiz_metin_filtreden_gecer():
    assert cevaptan_sayilar("Sayılar: 180 ve 50") == [180, 50]


def test_cevap_bos():
    assert cevaptan_sayilar("") == []
    assert cevaptan_sayilar(None) == []
