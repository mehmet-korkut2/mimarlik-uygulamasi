"""Uçtan uca: sentetik kroki + sahte Qwen -> DXF ve JSON (Qwen çağrılmaz)."""

import json

import cv2
import ezdxf

from mimarlik import okuma
from mimarlik.kroki import coz, main
from mimarlik.standartlar import KATMAN_DUVAR, KATMAN_KONTROL, KATMAN_OLCU
from tests.sentetik import BOYUT, sentetik_kroki


def _qwen1_cevabi(beklenen):
    yuk, gen = BOYUT
    return json.dumps([{"bbox_2d": [x1 / gen * 1000, y1 / yuk * 1000, x2 / gen * 1000, y2 / yuk * 1000],
                        "label": deger} for deger, (x1, y1, x2, y2) in beklenen["sayilar"].items()])


def _sahte_sor(qwen1, qwen2):
    def sor(istem, gorsel):
        assert gorsel[:4] == b"\x89PNG"
        return qwen1 if istem == okuma.ISTEM_SAYILAR else qwen2
    return sor


def test_uctan_uca_y2_bos():
    bgr, beklenen = sentetik_kroki()
    rapor = coz(bgr, _sahte_sor(_qwen1_cevabi(beklenen), "{}"))
    assert sorted(o["deger"] for o in rapor["olculer"]) == [60, 102, 180, 240]
    tireli = [o for o in rapor["olculer"] if o["neden"] == "isaret"]
    assert tireli and all(o["kaynak"] == "geometrik" for o in tireli)
    emin = {o["deger"]: o["emin"] for o in rapor["olculer"]}
    assert emin == {180: True, 240: True, 60: False, 102: False}   # 60 tiresiz + Y2 yok; 60 ile 102 aynı parçada
    assert "aynı parçada 2 değer" in next(o for o in rapor["olculer"] if o["deger"] == 102)["sebep"]
    assert len(rapor["kenarlar"]) == 6                     # L-oda konturu
    assert set(rapor["kapanma"]) == {"yatay", "dikey"}
    katmanlar = {e.dxf.layer for e in rapor["_doc"].modelspace()}
    assert {KATMAN_DUVAR, KATMAN_OLCU, KATMAN_KONTROL} <= katmanlar
    json.dumps({k: v for k, v in rapor.items() if not k.startswith("_")}, ensure_ascii=False)  # yazılabilir


def test_uctan_uca_y2_ile_tiresiz_sayi_y2_parcasina():
    bgr, beklenen = sentetik_kroki()
    q1 = _qwen1_cevabi(beklenen)
    eslem = coz(bgr, _sahte_sor(q1, "{}"))["ham"]["eslem"]
    ters = {pid: etiket for etiket, pid in eslem.items()}
    hedef = next(o for o in coz(bgr, _sahte_sor(q1, "{}"))["olculer"] if o["neden"] != "isaret")
    q2 = json.dumps({ters[hedef["parca_id"]]: [hedef["deger"]]})
    rapor = coz(bgr, _sahte_sor(q1, q2))
    o = next(o for o in rapor["olculer"] if o["deger"] == hedef["deger"])
    assert (o["kaynak"], o["parca_id"], o["y2"]) == ("y2", hedef["parca_id"], hedef["parca_id"])


def _qwen_yasak(istem, gorsel):
    raise AssertionError("Qwen çağrılmamalıydı")


def test_komut_satiri_okuma_kaydiyla(tmp_path, capsys, monkeypatch):
    bgr, beklenen = sentetik_kroki()
    foto = tmp_path / "sentetik.png"
    cv2.imwrite(str(foto), bgr)
    ilk = coz(bgr, _sahte_sor(_qwen1_cevabi(beklenen), "{}"))   # aynı parçalar: Y2 de kayıttan gelmeli
    kayit = tmp_path / "kayit.json"
    kayit.write_text(json.dumps({"ham": ilk["ham"]}), encoding="utf-8")
    monkeypatch.setattr(okuma, "qwen_sor", _qwen_yasak)
    cikti = tmp_path / "cikti"
    assert main([str(foto), "--cikti", str(cikti), "--okuma", str(kayit)]) == 0
    doc = ezdxf.readfile(cikti / "sentetik.dxf")
    assert doc.header["$INSUNITS"] == 5
    rapor = json.loads((cikti / "sentetik.json").read_text(encoding="utf-8"))
    assert rapor["ham"]["sayilar"] == _qwen1_cevabi(beklenen)
    assert (cikti / "sentetik_parcalar.jpg").exists()
    assert "Kapanma:" in capsys.readouterr().out
    assert rapor["ham"]["sayilar_kaynagi"] == "kayit" and rapor["ham"]["parcalar_kaynagi"] == "kayit"


def test_okuma_kaydi_parcalar_degistiyse_yalniz_y2_yeniden_sorulur():
    bgr, beklenen = sentetik_kroki()
    kayit = dict(coz(bgr, _sahte_sor(_qwen1_cevabi(beklenen), "{}"))["ham"])
    kayit["parcalar_geometri"] = {"P1": ["K1.1", [0, 0], [1, 1]]}   # kenar bulma değişmiş gibi
    sorulan = []

    def sor(istem, gorsel):
        sorulan.append(istem)
        return '{"P1": [180]}'

    rapor = coz(bgr, sor, kayit)
    assert sorulan == [okuma.ISTEM_PARCALAR]                        # Qwen-1 kayıttan, yalnız Y2 soruldu
    assert rapor["ham"]["parcalar_kaynagi"] == "qwen" and rapor["ham"]["sayilar_kaynagi"] == "kayit"


def test_eski_kayit_geometrisiz_eslem_ayniysa_kullanilir():
    bgr, beklenen = sentetik_kroki()
    kayit = dict(coz(bgr, _sahte_sor(_qwen1_cevabi(beklenen), "{}"))["ham"])
    del kayit["parcalar_geometri"]
    assert coz(bgr, _qwen_yasak, kayit)["ham"]["parcalar_kaynagi"] == "kayit"


def test_okunamayan_fotograf(tmp_path):
    assert main([str(tmp_path / "yok.jpg")]) == 2


def test_kapi_ipuclari_etiket_ve_kapi_genisligindeki_sayilar():
    from mimarlik.eslestirme import Bolge
    from mimarlik.kroki import kapi_ipuclari
    atanmis = [(Bolge((0, 0, 20, 10), None), 90), (Bolge((100, 100, 120, 110), None), 140)]
    ipuclari = kapi_ipuclari('[{"bbox_2d": [500, 500, 600, 600], "label": "K100"}]', atanmis, 1000, 1000)
    assert [(i.kaynak, i.deger, i.nokta) for i in ipuclari] == [("etiket", 100, (550.0, 550.0)),
                                                                 ("sayi", 90, (10.0, 5.0))]
    kutulu = kapi_ipuclari('[{"bbox_2d": [100, 100, 200, 200], "label": "90"}]', [], 1000, 1000)
    assert [(i.kaynak, i.deger, i.nokta) for i in kutulu] == [("sayi", 90, (150.0, 150.0))]   # Qwen kutusu da
