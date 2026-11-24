"""Geometrik bağlama ile Y2'yi birleştirme (karar 2026-11-18, deneyler/eslestirme/RAPOR.md "Karar").

- Ölçü tiresi bulunan sayı ("isaret"): geometrik parça kullanılır (ölçümde 9/9 doğru).
- Diğerleri: Y2'nin parçası kullanılır; Y2 o sayıyı hiçbir parçaya yazmadıysa geometrik (en yakın) parça.
- "Emin değilim" (kullanıcıya sorulacak):
  * iki yol aynı sayıyı farklı parçalara bağladıysa (çelişki; tiresiz sayılar da dahil),
  * Y2 değeri gürültü parçasına yazdıysa (varsayimlar.GURULTU_EN_KISA),
  * yalnızca bir yol bağlayabildiyse ve o yol tire değilse,
  * aynı parçaya birden fazla değer düştüyse,
  * Qwen'in kutusu sayının bölgesine yakın değilse (> EMIN_YAKINLIK h; değer o sayının olmayabilir, Ö2),
  * değerin kâğıtta bölgesi bulunamadıysa (yalnız Y2 bağladı; yakınlık bilinmiyor, Ö2).
- Kapı kuralı bir kapı bulduysa (3. adım), kapı genişliğindeki sayı kapının açıklık parçasına bağlanır
  (kaynak "kapi"): kapıyı o sayı verdiyse en yakın aynı değerli sayı, etiket/ölçekten geldiyse yalnız
  kapıya `KAPI_SAYI_MESAFESI` h içindeki sayı.

Y2 eşleme değer üzerinden yapılır: Qwen-1'in okuduğu her değer, Y2'nin aynı değerli bir girdisini tüketir
(önce aynı parçaya bağlı olanı). Hiçbir okumaya karşılık gelmeyen Y2 girdileri `sadece_y2` olarak döner,
geometride kullanılmaz.
"""

import math
from dataclasses import dataclass, replace

from mimarlik import varsayimlar
from mimarlik.eslestirme import EMIN_YAKINLIK, KenarSonucu, Kutu, Olcu, anlam


@dataclass(frozen=True)
class SonOlcu:
    deger: int
    bolge: Kutu | None
    parca_id: str | None
    kaynak: str | None        # "geometrik" | "y2" | "kapi" | None
    emin: bool
    sebep: str                # emin değilse neden; eminse ""
    geometrik: str | None     # geometrik yolun parçası (rapor için)
    neden: str | None         # geometrik bağlamanın nedeni: "isaret" | "temas" | "en_yakin" | None
    y2: str | None            # Y2'nin parçası
    anlam: str                # "uzunluk" | "bilinmiyor"


def gurultu_mu(parca_id: str, sonuc: KenarSonucu, h: float) -> bool:
    for kenar in sonuc.kenarlar:
        for p in kenar.parcalar:
            if p.id == parca_id:
                return not kenar.konturda or math.dist(p.bas, p.bit) < varsayimlar.GURULTU_EN_KISA * h
    return True  # bilinmeyen parça


def _y2_al(kalan: list[tuple[int, str]], deger: int, tercih: str | None) -> str | None:
    adaylar = [i for i, (d, _) in enumerate(kalan) if d == deger]
    if not adaylar:
        return None
    secilen = next((i for i in adaylar if kalan[i][1] == tercih), adaylar[0])
    return kalan.pop(secilen)[1]


KAPI_SAYI_MESAFESI = 5.0   # h; etiketten/ölçekten gelen kapıda sayının kapıya en büyük uzaklığı


def _kapi_girdileri(girdiler, kapilar, h) -> dict[int, str]:
    """Girdi indeksi -> kapının açıklık parçası. kapilar: [(değer, parça id, orta nokta, kaynak)]."""
    secilen: dict[int, str] = {}
    for deger, parca_id, orta, kaynak in kapilar:
        adaylar = []
        for i, (d, bolge, _, _) in enumerate(girdiler):
            if d != deger or i in secilen:
                continue
            uzaklik = math.inf if bolge is None else math.dist(((bolge[0] + bolge[2]) / 2, (bolge[1] + bolge[3]) / 2), orta)
            if kaynak == "sayi" or uzaklik <= KAPI_SAYI_MESAFESI * h:
                adaylar.append((uzaklik, i))
        if adaylar:
            secilen[min(adaylar)[1]] = parca_id
    return secilen


def birlestir(olculer: tuple[Olcu, ...], yeri_bulunamayan: tuple[int, ...], y2: list[tuple[int, str]],
              sonuc: KenarSonucu, h: float, kapilar=()) -> tuple[list[SonOlcu], list[tuple[int, str]]]:
    """Döner: (son ölçüler, sadece Y2'nin bağladığı [(değer, parça id)]).

    kapilar: [(değer, açıklık parça id, orta nokta, kapı kaynağı)] — bkz. `kroki.kapi_parcalari`.
    """
    parca_sozlugu = {p.id: (p, k) for k in sonuc.kenarlar for p in k.parcalar}
    girdiler = [(o.deger, o.bolge, o.parca_id, o.neden) for o in olculer] + \
               [(d, None, None, None) for d in yeri_bulunamayan]
    uzaklik = [o.kutu_uzakligi for o in olculer] + [None] * len(yeri_bulunamayan)
    # tireli olanlar önce: aynı değerli Y2 girdisini önce onlar (uyuşan parçayla) tüketsin
    # kapıya bağlanan sayı da önce: Y2'nin aynı değerli girdisi büyük olasılıkla kapının ölçüsü
    kapi_girdisi = _kapi_girdileri(girdiler, kapilar, h)
    sira = sorted(range(len(girdiler)), key=lambda i: (i not in kapi_girdisi, girdiler[i][3] != "isaret"))
    kalan = list(y2)
    sonuclar: dict[int, SonOlcu] = {}
    for i in sira:
        deger, bolge, g, neden = girdiler[i]
        y = _y2_al(kalan, deger, kapi_girdisi.get(i, g))
        sebepler = []
        if i in kapi_girdisi:
            parca, kaynak = kapi_girdisi[i], "kapi"
        elif neden == "isaret":
            parca, kaynak = g, "geometrik"
            if y is not None and y != g:
                sebepler.append(f"çelişki: Y2 {y}")
        elif y is not None:
            parca, kaynak = y, "y2"
            if g is not None and g != y:
                sebepler.append(f"çelişki: geometrik {g}")
            if gurultu_mu(y, sonuc, h):
                sebepler.append("Y2 gürültü parçasına yazdı")
        elif g is not None:
            parca, kaynak = g, "geometrik"
            sebepler.append(f"tire yok, Y2 bağlamadı; en yakın parça ({neden})")
        else:
            parca, kaynak = None, None
            sebepler.append("hiçbir parçaya bağlanamadı")
        if parca is not None and bolge is None:
            sebepler.append("bölgesi bulunamadı (Qwen kutusu hiçbir sayının yanında değil); yalnız Y2 bağladı")
        elif uzaklik[i] is not None and uzaklik[i] > EMIN_YAKINLIK:
            sebepler.append(f"Qwen kutusu bölgeden {uzaklik[i]:.1f} h uzak: değer bu sayının olmayabilir")
        a = anlam(*parca_sozlugu[parca]) if parca in parca_sozlugu else "bilinmiyor"
        sonuclar[i] = SonOlcu(deger, bolge, parca, kaynak, not sebepler, "; ".join(sebepler), g, neden, y, a)

    son = [sonuclar[i] for i in range(len(girdiler))]
    parca_degerleri: dict[str, list[int]] = {}
    for o in son:
        if o.parca_id is not None:
            parca_degerleri.setdefault(o.parca_id, []).append(o.deger)
    for n, o in enumerate(son):
        if o.parca_id is not None and len(parca_degerleri[o.parca_id]) > 1:
            ek = f"aynı parçada {len(parca_degerleri[o.parca_id])} değer: " + \
                 ", ".join(map(str, parca_degerleri[o.parca_id]))
            son[n] = replace(o, emin=False, sebep="; ".join(filter(None, [o.sebep, ek])))
    return son, kalan
