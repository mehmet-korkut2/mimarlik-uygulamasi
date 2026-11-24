"""plan_cizimi.ciz: DUVAR iç+dış yüz, kapı, ölçüler ve KONTROL katmanı."""

import ezdxf
import pytest

from mimarlik import varsayimlar
from mimarlik.birlestirme import SonOlcu
from mimarlik.dxf_yazici import kaydet
from mimarlik.geometri import plan_kur
from mimarlik.plan_cizimi import ciz
from mimarlik.standartlar import KATMAN_DUVAR, KATMAN_KAPI, KATMAN_KONTROL, KATMAN_OLCU
from tests.test_geometri import H, _dikdortgen, _o


def _okunan(doc, tmp_path):
    return ezdxf.readfile(kaydet(doc, tmp_path / "p.dxf")).modelspace()


def _katmanda(msp, tur, katman):
    return [e for e in msp.query(tur) if e.dxf.layer == katman]


def _uzunluk(e):
    return ((e.dxf.end.x - e.dxf.start.x) ** 2 + (e.dxf.end.y - e.dxf.start.y) ** 2) ** 0.5


def test_kapanan_oda_ic_ve_dis_yuz_kontrol_bos(tmp_path):
    olculer = [_o(400, "K1.1"), _o(300, "K2.1"), _o(400, "K3.1"), _o(300, "K4.1")]
    doc, notlar = ciz(plan_kur(_dikdortgen(), olculer, H), olculer)
    msp = _okunan(doc, tmp_path)
    t = varsayimlar.DIS_DUVAR_KALINLIGI
    boylar = sorted(round(_uzunluk(e)) for e in _katmanda(msp, "LINE", KATMAN_DUVAR))
    assert boylar == sorted([400, 300, 400, 300, 400 + 2 * t, 300 + 2 * t, 400 + 2 * t, 300 + 2 * t])
    assert len(_katmanda(msp, "DIMENSION", KATMAN_OLCU)) == 4
    assert [e for e in msp if e.dxf.layer == KATMAN_KONTROL] == [] and notlar == []


def test_dis_yuz_disarida(tmp_path):
    olculer = [_o(400, "K1.1"), _o(300, "K2.1"), _o(400, "K3.1"), _o(300, "K4.1")]
    doc, _ = ciz(plan_kur(_dikdortgen(), olculer, H), olculer)
    t = varsayimlar.DIS_DUVAR_KALINLIGI
    ys = [e.dxf.start.y for e in _katmanda(_okunan(doc, tmp_path), "LINE", KATMAN_DUVAR)]
    assert max(ys) == pytest.approx(t)            # üst duvarın dış yüzü yukarıda
    assert min(ys) == pytest.approx(-300 - t)     # alt duvarın dış yüzü aşağıda


def test_kapi_boslugu_soveler_kanat_yay(tmp_path):
    alt = [("duvar", (400, 300), (300, 300)), ("aciklik", (300, 300), (210, 300)), ("duvar", (210, 300), (0, 300))]
    olculer = [_o(400, "K1.1"), _o(300, "K2.1"), _o(100, "K3.1"), _o(90, "K3.2"), _o(210, "K3.3"), _o(300, "K4.1")]
    doc, _ = ciz(plan_kur(_dikdortgen(alt), olculer, H), olculer)
    msp = _okunan(doc, tmp_path)
    t = varsayimlar.DIS_DUVAR_KALINLIGI
    duvar = _katmanda(msp, "LINE", KATMAN_DUVAR)
    assert sum(round(_uzunluk(e)) == t for e in duvar) == 2             # iki söve
    assert len(_katmanda(msp, "LINE", KATMAN_KAPI)) == 1
    yay = _katmanda(msp, "ARC", KATMAN_KAPI)[0]
    assert yay.dxf.radius == pytest.approx(90)
    assert (yay.dxf.center.x, yay.dxf.center.y) == pytest.approx((300, -300))   # menteşe açıklığın başında
    assert yay.dxf.start_angle % 360 == pytest.approx(90)               # içeri (yukarı) ...
    assert yay.dxf.end_angle % 360 == pytest.approx(180)                # ... kenar yönüne (sola)
    assert len(_katmanda(msp, "DIMENSION", KATMAN_OLCU)) == 6           # 3 parça + 3 kenar


def test_kapanmayan_kenarlar_ve_aciklik_kontrolde(tmp_path):
    olculer = [_o(400, "K1.1"), _o(300, "K2.1"), _o(360, "K3.1"), _o(300, "K4.1")]
    doc, notlar = ciz(plan_kur(_dikdortgen(), olculer, H), olculer)
    msp = _okunan(doc, tmp_path)
    kontrol = _katmanda(msp, "LINE", KATMAN_KONTROL)
    assert sorted(round(_uzunluk(e)) for e in kontrol) == [40, 360, 400]   # yatay kenarlar + kapanma açığı
    assert any("yatay fark 40 cm, kapanmıyor" in n for n in notlar)
    assert any("KAPANMIYOR" in e.dxf.text for e in _katmanda(msp, "TEXT", KATMAN_KONTROL))


def test_emin_olmayan_ve_hesaplanan_kontrolde(tmp_path):
    olculer = [_o(400, "K1.1"), _o(300, "K2.1"), _o(300, "K4.1", emin=False),
               SonOlcu(77, None, None, None, False, "hiçbir parçaya bağlanamadı", None, None, None, "bilinmiyor")]
    doc, notlar = ciz(plan_kur(_dikdortgen(), olculer, H), olculer, sadece_y2=[(55, "K2.1")])
    msp = _okunan(doc, tmp_path)
    assert "? K3 400 cm: okunmadı, kapanmadan hesaplandı" in notlar
    assert "? 300: x" in notlar
    assert "? 77: hiçbir parçaya bağlanamadı" in notlar
    assert "? 55: yalnızca Y2 okudu (K2.1)" in notlar
    assert len(_katmanda(msp, "DIMENSION", KATMAN_KONTROL)) == 1        # hesaplanan kenarın ölçüsü
    assert any(n.startswith("DOĞRULANAMADI: yatay doğrulanamadı: K3") for n in notlar)
    assert not any("KAPANMIYOR" in n for n in notlar)
    # 3 notun yeri var (kapanma, K3, 300): planda 3 numara + "KONTROL NOTLARI" + 5 liste satırı
    assert len(_katmanda(msp, "CIRCLE", KATMAN_KONTROL)) == 3
    assert len(_katmanda(msp, "TEXT", KATMAN_KONTROL)) == 3 + 1 + len(notlar)


def test_ic_duvar_kontrolde(tmp_path):
    olculer = [_o(800, "K1.1"), _o(600, "K2.1"), _o(800, "K3.1"), _o(600, "K4.1")]
    doc, notlar = ciz(plan_kur(_dikdortgen(ic=True), olculer, H), olculer)
    assert "K5 ölçüsüz (konturda değil)" in notlar
    assert len(_katmanda(_okunan(doc, tmp_path), "LINE", KATMAN_KONTROL)) == 1


def test_s3_b_okunan_parca_olcude_hesaplanan_parca_kontrolde(tmp_path):
    alt = [("duvar", (400, 300), (100, 300)), ("duvar", (100, 300), (0, 300))]
    olculer = [_o(420, "K1.1"), _o(300, "K2.1"), _o(320, "K3.1"), _o(300, "K4.1")]
    doc, _ = ciz(plan_kur(_dikdortgen(alt), olculer, H), olculer)
    msp = _okunan(doc, tmp_path)
    olcu = sorted(round(e.get_measurement()) for e in _katmanda(msp, "DIMENSION", KATMAN_OLCU))
    kontrol = sorted(round(e.get_measurement()) for e in _katmanda(msp, "DIMENSION", KATMAN_KONTROL))
    assert olcu == [300, 300, 320, 420] and kontrol == [100]


def test_iptal_edilen_duvar_kontrolde(tmp_path):
    from dataclasses import replace
    olculer = [_o(400, "K1.1"), _o(300, "K2.1"), _o(400, "K3.1"), _o(300, "K4.1")]
    plan = replace(plan_kur(_dikdortgen(), olculer, H), iptaller=(((0, 0), (0, 100)),))
    doc, notlar = ciz(plan, olculer)
    assert "X: iptal edilmiş duvar" in notlar
    assert [round(_uzunluk(e)) for e in _katmanda(_okunan(doc, tmp_path), "LINE", KATMAN_KONTROL)] == [100]


def test_cikarilan_kapi_kontrolde_etiketli_degil(tmp_path):
    from dataclasses import replace
    olculer = [_o(400, "K1.1"), _o(300, "K2.1"), _o(400, "K3.1"), _o(300, "K4.1")]
    plan = replace(plan_kur(_dikdortgen(), olculer, H),
                   kapilar=(((10, 10), "sayi", 90), ((20, 20), "olcek", 80), ((30, 30), "etiket", 100)))
    _, notlar = ciz(plan, olculer)
    assert "? kapı 90: yakında okunan sayıdan" in notlar and "? kapı 80: ölçekten tahmin" in notlar
    assert not any("kapı 100" in n for n in notlar)


def test_hesaplanan_kenar_kontrolde_cizgiyle_isaretli_kapanma_acigi_yok(tmp_path):
    olculer = [_o(400, "K1.1"), _o(300, "K2.1"), _o(300, "K4.1")]          # K3 kapanmadan hesaplanır
    doc, _ = ciz(plan_kur(_dikdortgen(), olculer, H), olculer)
    kontrol = _katmanda(_okunan(doc, tmp_path), "LINE", KATMAN_KONTROL)
    assert sorted(round(_uzunluk(e)) for e in kontrol) == [400]          # yalnız hesaplanan K3 (açık yok: fark 0)


def test_planda_yalniz_numara_tam_metin_sagda_liste(tmp_path):
    olculer = [_o(400, "K1.1"), _o(300, "K2.1", emin=False), _o(300, "K4.1")]
    doc, notlar = ciz(plan_kur(_dikdortgen(), olculer, H), olculer)
    msp = _okunan(doc, tmp_path)
    yazilar = _katmanda(msp, "TEXT", KATMAN_KONTROL)
    numaralar = [e for e in yazilar if e.dxf.text.isdigit()]
    liste = [e for e in yazilar if e.dxf.text[:1].isdigit() and ". " in e.dxf.text]
    assert sorted(e.dxf.text for e in numaralar) == [str(n) for n in range(1, len(numaralar) + 1)]
    assert [e.dxf.text for e in liste] == [f"{n}. {m}" for n, m in enumerate(notlar, 1)]   # sırayla, tam metin
    plan_sag = max(max(e.dxf.start.x, e.dxf.end.x) for e in _katmanda(msp, "LINE", KATMAN_DUVAR))
    assert all(e.dxf.insert.x > plan_sag for e in liste)                        # planın sağında
    ys = [e.dxf.insert.y for e in liste]
    assert ys == sorted(ys, reverse=True) and len(set(ys)) == len(ys)            # alt alta, üst üste binmez
    assert not any(len(e.dxf.text) > 3 and not e.dxf.text[0].isdigit() and e.dxf.text != "KONTROL NOTLARI"
                   for e in yazilar)                                            # planın üstünde uzun metin yok
