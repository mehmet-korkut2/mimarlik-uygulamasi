"""Örnek oda: dxf_yazici modülünü kullanarak tek odalı bir plan üretir.

Çalıştırmak için (repo kökünden):
    .venv/Scripts/python -m mimarlik.demo_oda

Orijin odanın sol-alt DIŞ köşesi. Kapı güney (alt) duvarda, pencere kuzey
(üst) duvarda ortalı. Tüm koordinatlar standartlar.py'deki ölçülerden
hesaplanır; ölçüler değişince plan da değişir.
"""

from pathlib import Path

from mimarlik.dxf_yazici import cizgi_ekle, kaydet, olcu_ekle, yay_ekle, yeni_cizim
from mimarlik.standartlar import (
    DIS_DUVAR_KALINLIGI,
    KAPI_GENISLIGI,
    KATMAN_DUVAR,
    KATMAN_KAPI,
    KATMAN_OLCU,
    KATMAN_PENCERE,
    PENCERE_GENISLIGI,
)

# Demoya özel değerler (mimari standart değil), cm
ODA_IC_GENISLIK = 400
ODA_IC_DERINLIK = 300
KAPI_KOSE_MESAFESI = 50  # kapı boşluğunun iç köşeye uzaklığı
OLCU_MESAFESI = 60  # ölçü çizgisinin duvardan uzaklığı


def _kesik_yatay(y, x_bas, x_bit, bosluk_bas, bosluk_bit):
    """y hizasında, [bosluk_bas, bosluk_bit] aralığı boş bırakılmış yatay çizgi."""
    return [(x_bas, y, bosluk_bas, y), (bosluk_bit, y, x_bit, y)]


def oda_geometrisi() -> dict:
    """Odanın tüm çizgilerini, yaylarını ve ölçülerini hesaplar (dosya yazmaz)."""
    d = DIS_DUVAR_KALINLIGI
    gen = ODA_IC_GENISLIK + 2 * d  # dış genişlik
    der = ODA_IC_DERINLIK + 2 * d  # dış derinlik

    kapi_bas = d + KAPI_KOSE_MESAFESI
    kapi_bit = kapi_bas + KAPI_GENISLIGI
    pen_bas = (gen - PENCERE_GENISLIGI) / 2
    pen_bit = pen_bas + PENCERE_GENISLIGI

    duvarlar = [
        # dış yüz
        *_kesik_yatay(0, 0, gen, kapi_bas, kapi_bit),
        (gen, 0, gen, der),
        *_kesik_yatay(der, 0, gen, pen_bas, pen_bit),
        (0, 0, 0, der),
        # iç yüz
        *_kesik_yatay(d, d, gen - d, kapi_bas, kapi_bit),
        (gen - d, d, gen - d, der - d),
        *_kesik_yatay(der - d, d, gen - d, pen_bas, pen_bit),
        (d, d, d, der - d),
        # söveler: boşlukların kenarında duvarı kapatan kısa çizgiler
        (kapi_bas, 0, kapi_bas, d),
        (kapi_bit, 0, kapi_bit, d),
        (pen_bas, der - d, pen_bas, der),
        (pen_bit, der - d, pen_bit, der),
    ]

    # Kapı içeri açılır: menteşe boşluğun sol iç köşesinde, kanat açık konumda dik.
    kapi_kanadi = [(kapi_bas, d, kapi_bas, d + KAPI_GENISLIGI)]
    kapi_yayi = ((kapi_bas, d), KAPI_GENISLIGI, 0, 90, KATMAN_KAPI)

    # Pencere: duvarın iki yüzü + ortada cam çizgisi.
    pencere = [(pen_bas, y, pen_bit, y) for y in (der, der - d / 2, der - d)]

    olculer = [
        ((0, 0), (gen, 0), -OLCU_MESAFESI, KATMAN_OLCU),  # alt: dış genişlik
        ((gen, 0), (gen, der), -OLCU_MESAFESI, KATMAN_OLCU),  # sağ: dış derinlik
    ]

    return {
        "cizgiler": {
            KATMAN_DUVAR: duvarlar,
            KATMAN_KAPI: kapi_kanadi,
            KATMAN_PENCERE: pencere,
        },
        "yaylar": [kapi_yayi],
        "olculer": olculer,
    }


def oda_ciz(yol: str | Path = "output/oda_demo.dxf") -> Path:
    """Örnek odayı DXF olarak yazar ve dosya yolunu döndürür."""
    geometri = oda_geometrisi()
    doc = yeni_cizim("cm")
    for katman, cizgiler in geometri["cizgiler"].items():
        cizgi_ekle(doc, cizgiler, katman)
    for merkez, yaricap, bas, bit, katman in geometri["yaylar"]:
        yay_ekle(doc, merkez, yaricap, bas, bit, katman)
    for p1, p2, uzaklik, katman in geometri["olculer"]:
        olcu_ekle(doc, p1, p2, uzaklik, katman)
    return kaydet(doc, yol)


if __name__ == "__main__":
    print(f"Yazıldı: {oda_ciz()}")
