"""Çizgi listelerini katman ve birimle DXF dosyasına yazan fonksiyonlar."""

from collections.abc import Iterable
from pathlib import Path

import ezdxf
from ezdxf.document import Drawing

from mimarlik.standartlar import KATMAN_RENKLERI, OLCU_STILI, OLCU_YAZI_YUKSEKLIGI

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
        doc.layers.add(ad, color=renk)

    doc.dimstyles.new(
        OLCU_STILI,
        dxfattribs={
            "dimtxt": OLCU_YAZI_YUKSEKLIGI,  # yazı yüksekliği
            "dimtsz": 5,  # >0 olunca ok yerine tick çizilir
            "dimdec": 0,  # ondalık basamak yok
            "dimexe": 10,  # yardımcı çizgi ölçü çizgisinin ötesine uzama
            "dimexo": 5,  # yardımcı çizginin nesneden boşluğu
            "dimgap": 5,  # yazı ile ölçü çizgisi arası
        },
    )
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


def _cizgiyi_dogrula(cizgi) -> tuple[float, float, float, float]:
    """(x1, y1, x2, y2) biçimini ve sıfırdan büyük uzunluğu kontrol eder."""
    try:
        x1, y1, x2, y2 = (float(v) for v in cizgi)
    except (TypeError, ValueError) as hata:
        raise ValueError(
            f"Çizgi (x1, y1, x2, y2) biçiminde 4 sayı olmalı, gelen: {cizgi!r}"
        ) from hata
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
    """Çizimi kaydeder; klasör yoksa oluşturur. Yazılan yolu döndürür."""
    yol = Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
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
    doc.modelspace().add_arc(
        center=merkez,
        radius=yaricap,
        start_angle=bas_aci,
        end_angle=bit_aci,
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
    olcu = doc.modelspace().add_aligned_dim(
        p1=p1,
        p2=p2,
        distance=uzaklik,
        dimstyle=OLCU_STILI,
        dxfattribs={"layer": katman},
    )
    # render(): ölçünün görünen çizgilerini (blok) üretir; yoksa bazı
    # programlar ölçüyü boş gösterir.
    olcu.render()
