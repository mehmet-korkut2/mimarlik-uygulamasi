"""araclar.dxf_resim: DXF önizlemesi doğru yerde, katman rengiyle çiziliyor mu."""

import cv2
import pytest

from araclar.dxf_resim import RENK, dxf_resmi
from mimarlik.dxf_yazici import cizgi_ekle, kaydet, olcu_ekle, yazi_ekle, yeni_cizim
from mimarlik.standartlar import KATMAN_DUVAR, KATMAN_KONTROL, KATMAN_OLCU


def test_cizgi_ve_kontrol_renkleri(tmp_path):
    doc = yeni_cizim()
    cizgi_ekle(doc, [(0, 0, 1000, 0)], KATMAN_DUVAR)
    cizgi_ekle(doc, [(0, 500, 1000, 500)], KATMAN_KONTROL)
    olcu_ekle(doc, (0, 0), (1000, 0), -60, KATMAN_OLCU)
    yazi_ekle(doc, "yatay fark 40 cm", (0, 600), 15, KATMAN_KONTROL)
    png = dxf_resmi(kaydet(doc, tmp_path / "a.dxf"), tmp_path / "a.png", en_boy=500, pay=0)
    img = cv2.imread(str(png))
    assert max(img.shape[:2]) in (500, 501)
    sutun = img.shape[1] // 2
    renkler = {tuple(int(v) for v in img[y, sutun]) for y in range(img.shape[0])}
    assert RENK["DUVAR"] in renkler and RENK["KONTROL"] in renkler
    assert (img == RENK["OLCU"]).all(axis=2).any()   # ölçü (ortada yazı boşluğu var, bütün resimde ara)
    # y yukarı -> resimde aşağı: KONTROL çizgisi (y=500) DUVAR'ın (y=0) üstünde
    y_kontrol = min(y for y in range(img.shape[0]) if tuple(img[y, sutun]) == RENK["KONTROL"])
    y_duvar = min(y for y in range(img.shape[0]) if tuple(img[y, sutun]) == RENK["DUVAR"])
    assert y_kontrol < y_duvar


def test_bos_dxf_hata(tmp_path):
    with pytest.raises(ValueError):
        dxf_resmi(kaydet(yeni_cizim(), tmp_path / "b.dxf"), tmp_path / "b.png")
