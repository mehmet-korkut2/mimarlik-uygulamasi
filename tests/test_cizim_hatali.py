"""01 ve 02: ÇİZİM HATALI krokiler (mimar doğruladı, 2026-11-24) — kapanma kontrolü bunu yakalamalı.

Krokilere yazılan gerçek sayılar gerçek dış hatta (S1 toplamı, S3 = B) yerleştirilince bile toplamlar tutmuyor
(01: yatay 40 / dikey 53 cm, 02: 48 / 60 cm). Mimar bunun yorumdan değil, çizim hatasından geldiğini doğruladı.
Bu dosya o hatanın yakalandığını sabitler. 01–02 okuma/bağlama ölçümünde geçerli, geometri/kapanma/DXF
doğruluğunu ölçmek için KULLANILMAZ;
düzeltilmiş ölçüler mimardan gelince "doğru hal" ayrı test verisi olarak eklenecek.

Veri yalnız sayılar ve yönler (fotoğraf yok); kaynak: deneyler/kapi_kurali/olcum.py GERCEK_DIS_HAT.
"""

import pytest

from mimarlik.birlestirme import SonOlcu
from mimarlik.eslestirme import Kenar, KenarSonucu, Parca
from mimarlik.geometri import plan_kur

# (yön (x, y; görüntüde y aşağı), parça değerleri): kontur sırasıyla. Üç parçalı kenar: duvar – kapı – duvar.
DIS_HAT = {
    "01": [((1, 0), [180]), ((0, 1), [50]), ((1, 0), [40]), ((0, 1), [120]), ((-1, 0), [140]),
           ((0, -1), [10, 90, 15]), ((-1, 0), [120]), ((0, -1), [108])],
    "02": [((1, 0), [300]), ((0, 1), [45]), ((1, 0), [45]), ((0, 1), [240]), ((-1, 0), [200]), ((0, -1), [40]),
           ((-1, 0), [40]), ((0, 1), [40]), ((-1, 0), [102]), ((0, -1), [200]), ((1, 0), [45]),
           ((0, -1), [15, 90, 40])],
}
BEKLENEN_FARK = {"01": (40, 53), "02": (48, 60)}   # cm, yatay / dikey (mutlak)


def _kroki(kod):
    """Gerçek dış hattın kenar dizisi (piksel boyları önemsiz: geometri yalnız sıra ve yönü kullanır)."""
    kenarlar, olculer, p = [], [], (0.0, 0.0)
    for n, (yon, degerler) in enumerate(DIS_HAT[kod], 1):
        parcalar = []
        for m, d in enumerate(degerler, 1):
            q = (p[0] + yon[0] * 100, p[1] + yon[1] * 100)
            tur = "aciklik" if len(degerler) == 3 and m == 2 else "duvar"
            parcalar.append(Parca(f"K{n}.{m}", f"K{n}", tur, p, q))
            olculer.append(SonOlcu(d, None, f"K{n}.{m}", "geometrik", True, "", f"K{n}.{m}", "isaret", None,
                                   "uzunluk"))
            p = q
        kenarlar.append(Kenar(f"K{n}", "yatay" if yon[0] else "dikey", tuple(parcalar), True))
    return KenarSonucu(0.0, tuple(kenarlar), tuple(k.id for k in kenarlar), ()), olculer


@pytest.mark.parametrize("kod", ["01", "02"])
def test_cizim_hatali_kroki_kapanma_kontrolunde_yakalanir(kod):
    sonuc, olculer = _kroki(kod)
    plan = plan_kur(sonuc, olculer, h=20.0)
    assert all(k.durum == "olcu" for k in plan.kenarlar)            # her kenar okunan sayıdan: tahmin yok
    yatay, dikey = plan.kapanma["yatay"], plan.kapanma["dikey"]
    assert (abs(yatay["fark_cm"]), abs(dikey["fark_cm"])) == BEKLENEN_FARK[kod]
    assert not yatay["tutuyor"] and not dikey["tutuyor"]          # hata kullanıcıya gösterilir
