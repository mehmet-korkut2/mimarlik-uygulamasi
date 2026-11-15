"""Çizgi listelerini katman ve birimle DXF dosyasına yazan fonksiyonlar."""

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
