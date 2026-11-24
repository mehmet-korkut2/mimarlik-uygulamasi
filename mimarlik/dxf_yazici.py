"""Çizgi listelerini katman ve birimle DXF dosyasına yazan fonksiyonlar."""

import math
from collections.abc import Iterable
from pathlib import Path

import ezdxf
from ezdxf import zoom
from ezdxf.document import Drawing

from mimarlik.standartlar import (
    KATMAN_KALINLIKLARI,
    KATMAN_RENKLERI,
    OLCU_STILI,
    OLCU_YAZI_STILI,
    OLCU_YAZI_YUKSEKLIGI,
)

# DXF $INSUNITS kodları
BIRIM_KODLARI = {"mm": 4, "cm": 5, "m": 6}


def yeni_cizim(birim: str = "cm") -> Drawing:
    """Katmanları ve ölçü stili hazır, boş bir R2010 çizimi oluşturur."""
    if birim not in BIRIM_KODLARI:
        raise ValueError(
            f"Bilinmeyen birim: {birim!r}. Desteklenenler: {sorted(BIRIM_KODLARI)}"
        )

    doc = ezdxf.new("R2010", setup=False)
    doc.units = BIRIM_KODLARI[birim]  # $INSUNITS: AutoCAD bu birimle açar
    doc.header["$MEASUREMENT"] = 1  # metrik

    for ad, renk in KATMAN_RENKLERI.items():
        doc.layers.add(ad, color=renk, lineweight=KATMAN_KALINLIKLARI[ad])
    doc.header["$LWDISPLAY"] = 1  # çizgi kalınlıkları ekranda da görünsün (AutoCAD "LWT" düğmesi)

    # Ölçü yazısının stili çizimde tanımlı olmalı (setup=False ile yalnızca
    # "Standard" gelir). standartlar.py'de başka bir ad seçilirse burada oluşur.
    if OLCU_YAZI_STILI not in doc.styles:
        doc.styles.add(OLCU_YAZI_STILI)

    doc.dimstyles.new(
        OLCU_STILI,
        dxfattribs={
            "dimtxsty": OLCU_YAZI_STILI,  # boşsa AutoCAD ölçü yazısını çizemez
            "dimtxt": OLCU_YAZI_YUKSEKLIGI,  # yazı yüksekliği
            "dimtsz": 5,  # >0 olunca ok yerine tick çizilir
            "dimdec": 0,  # ondalık basamak yok
            "dimexe": 10,  # yardımcı çizgi ölçü çizgisinin ötesine uzama
            "dimexo": 5,  # yardımcı çizginin nesneden boşluğu
            "dimgap": 5,  # yazı ile ölçü çizgisi arası
        },
    )
    # Varsayılan ölçü stili; ezdxf "ISO-25" yazar ama setup=False ile o stil yok.
    doc.header["$DIMSTYLE"] = OLCU_STILI
    return doc


def _katmani_dogrula(katman: str) -> None:
    """Katman standartlar.py'de birebir tanımlı değilse ValueError verir.

    doc.layers ile kontrol etmiyoruz: ezdxf (AutoCAD gibi) büyük/küçük harf
    ayırmaz, "duvar" yazım hatası sessizce DUVAR'a gider.
    """
    if katman not in KATMAN_RENKLERI:
        raise ValueError(
            f"Tanımsız katman: {katman!r}. Tanımlı katmanlar: {list(KATMAN_RENKLERI)}"
        )


def _sonlu_sayilar(ne: str, *degerler) -> list[float]:
    """Değerleri float'a çevirir; NaN/sonsuz ya da sayı olmayan değerde ValueError.

    NaN içeren bir DXF'i AutoCAD tümden reddedebilir; hatayı burada yakalıyoruz.
    """
    try:
        sayilar = [float(v) for v in degerler]
    except (TypeError, ValueError) as hata:
        raise ValueError(f"{ne}: sayı olmayan değer: {degerler!r}") from hata
    if not all(math.isfinite(s) for s in sayilar):
        raise ValueError(f"{ne}: NaN/sonsuz değer kabul edilmez: {degerler!r}")
    return sayilar


def _cizgiyi_dogrula(cizgi) -> tuple[float, float, float, float]:
    """(x1, y1, x2, y2) biçimini, sonlu değerleri ve sıfırdan büyük uzunluğu kontrol eder."""
    try:
        degerler = list(cizgi)
    except TypeError as hata:
        raise ValueError(
            f"Çizgi (x1, y1, x2, y2) biçiminde 4 sayı olmalı, gelen: {cizgi!r}"
        ) from hata
    if len(degerler) != 4:
        raise ValueError(
            f"Çizgi (x1, y1, x2, y2) biçiminde 4 sayı olmalı, gelen: {cizgi!r}"
        )
    x1, y1, x2, y2 = _sonlu_sayilar(f"Çizgi {cizgi!r}", *degerler)
    if x1 == x2 and y1 == y2:
        raise ValueError(f"Sıfır uzunluklu çizgi: {cizgi!r}")
    return x1, y1, x2, y2


def cizgi_ekle(
    doc: Drawing,
    cizgiler: Iterable[tuple[float, float, float, float]],
    katman: str,
) -> None:
    """Çizgileri verilen katmana ekler. Biri bile hatalıysa hiçbiri eklenmez."""
    _katmani_dogrula(katman)
    gecerli = [_cizgiyi_dogrula(c) for c in cizgiler]  # önce hepsini doğrula

    msp = doc.modelspace()
    for x1, y1, x2, y2 in gecerli:
        msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": katman})


def kaydet(doc: Drawing, yol: str | Path) -> Path:
    """Çizimi kaydeder; klasör yoksa oluşturur. Yazılan yolu döndürür.

    Kaydetmeden önce görünümü çizimin tamamına ortalar (zoom extents), böylece
    dosya AutoCAD'de açıldığında çizim ekranın ortasında görünür.
    """
    yol = Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
    zoom.extents(doc.modelspace())
    doc.saveas(yol)
    return yol


def yay_ekle(
    doc: Drawing,
    merkez: tuple[float, float],
    yaricap: float,
    bas_aci: float,
    bit_aci: float,
    katman: str,
) -> None:
    """Yay ekler (kapı açılımı için). Açılar derece, saat yönünün tersine."""
    _katmani_dogrula(katman)
    mx, my, r, a1, a2 = _sonlu_sayilar("Yay", *merkez, yaricap, bas_aci, bit_aci)
    if r <= 0:
        raise ValueError(f"Yay yarıçapı sıfırdan büyük olmalı, gelen: {yaricap!r}")
    doc.modelspace().add_arc(
        center=(mx, my),
        radius=r,
        start_angle=a1,
        end_angle=a2,
        dxfattribs={"layer": katman},
    )


def olcu_ekle(
    doc: Drawing,
    p1: tuple[float, float],
    p2: tuple[float, float],
    uzaklik: float,
    katman: str,
) -> None:
    """p1-p2 arasına AutoCAD'de düzenlenebilir bir hizalı ölçü ekler.

    uzaklik > 0: ölçü çizgisi p1->p2 yönünün solunda, < 0: sağında.
    """
    _katmani_dogrula(katman)
    x1, y1, x2, y2, d = _sonlu_sayilar("Ölçü", *p1, *p2, uzaklik)
    if x1 == x2 and y1 == y2:
        raise ValueError(f"Ölçünün iki noktası aynı olamaz: {p1!r}")
    olcu = doc.modelspace().add_aligned_dim(
        p1=(x1, y1),
        p2=(x2, y2),
        distance=d,
        dimstyle=OLCU_STILI,
        dxfattribs={"layer": katman},
    )
    # render(): ölçünün görünen çizgilerini (blok) üretir; yoksa bazı
    # programlar ölçüyü boş gösterir.
    olcu.render()


def yazi_ekle(
    doc: Drawing,
    metin: str,
    konum: tuple[float, float],
    yukseklik: float,
    katman: str,
) -> None:
    """Tek satırlık yazı (TEXT) ekler; konum yazının sol alt köşesi."""
    _katmani_dogrula(katman)
    x, y, yuk = _sonlu_sayilar("Yazı", *konum, yukseklik)
    if yuk <= 0:
        raise ValueError(f"Yazı yüksekliği sıfırdan büyük olmalı, gelen: {yukseklik!r}")
    doc.modelspace().add_text(
        metin, height=yuk, dxfattribs={"layer": katman, "style": OLCU_YAZI_STILI}
    ).set_placement((x, y))
