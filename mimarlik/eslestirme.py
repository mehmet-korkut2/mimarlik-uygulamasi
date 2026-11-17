"""Sayı–duvar eşleştirme: veri modeli (geometri adımıyla sözleşme), değer atama ve bağlama.

Bütün koordinatlar orijinal fotoğraf pikselidir (x, y; y aşağı). Tasarım:
docs/superpowers/specs/2026-11-17-sayi-duvar-eslestirme-design.md (bölüm 6).
"""

import math
from dataclasses import asdict, dataclass

Nokta = tuple[float, float]
Kutu = tuple[float, float, float, float]  # x1, y1, x2, y2


@dataclass(frozen=True)
class Parca:
    id: str          # "K3.2"
    kenar_id: str    # "K3"
    tur: str         # "duvar" | "aciklik"
    bas: Nokta
    bit: Nokta


@dataclass(frozen=True)
class Kenar:
    id: str
    yon: str                      # "yatay" | "dikey" (eksen açısına göre)
    parcalar: tuple[Parca, ...]   # kenar yönünde sıralı
    konturda: bool


@dataclass(frozen=True)
class IsaretAdayi:
    """Bir ucu duvara değen, diğer ucu boşta kısa çizgi (ölçü işareti adayı)."""
    bas: Nokta   # duvara değen uç
    bit: Nokta   # boştaki uç


@dataclass(frozen=True)
class Bolge:
    kutu: Kutu
    temas: Nokta | None   # bölge mürekkebinin bir duvara değdiği nokta


@dataclass(frozen=True)
class Olcu:
    deger: int
    bolge: Kutu
    parca_id: str | None
    neden: str | None   # "isaret" | "temas" | "en_yakin" | None
    anlam: str          # "uzunluk" | "bilinmiyor"


@dataclass(frozen=True)
class Kroki:
    eksen_acisi_derece: float
    kenarlar: tuple[Kenar, ...]
    kontur_sirasi: tuple[str, ...]   # kenar id'leri, saat yönünde
    olculer: tuple[Olcu, ...]
    yeri_bulunamayan: tuple[int, ...]
    okunmamis_bolgeler: tuple[Kutu, ...]


@dataclass(frozen=True)
class KenarSonucu:
    """kenar_bulma.kenarlari_bul çıktısı (burada tanımlı: döngüsel import olmasın)."""
    eksen_acisi_derece: float   # yatay duvarların atan2(dy, dx) açısı, (-45, 45]
    kenarlar: tuple[Kenar, ...]
    kontur_sirasi: tuple[str, ...]
    isaretler: tuple[IsaretAdayi, ...]


def kroki_sozluk(kroki: Kroki) -> dict:
    """Kroki -> json.dumps edilebilir sözlük (tuple'lar listeye döner)."""
    return asdict(kroki)


def nokta_parca_mesafesi(p: Nokta, parca: Parca) -> float:
    """Noktanın parça doğru parçasına uzaklığı; izdüşüm parçanın dışındaysa en yakın uca uzaklık."""
    (x1, y1), (x2, y2) = parca.bas, parca.bit
    dx, dy = x2 - x1, y2 - y1
    uzunluk2 = dx * dx + dy * dy
    t = 0.0 if uzunluk2 == 0 else max(0.0, min(1.0, ((p[0] - x1) * dx + (p[1] - y1) * dy) / uzunluk2))
    return math.hypot(p[0] - (x1 + t * dx), p[1] - (y1 + t * dy))


def parcayi_bul(p: Nokta, kenarlar, tolerans: float) -> Parca | None:
    """Noktaya en yakın parça; uzaklık toleransı aşıyorsa None."""
    en_iyi, en_iyi_d = None, tolerans
    for kenar in kenarlar:
        for parca in kenar.parcalar:
            d = nokta_parca_mesafesi(p, parca)
            if d <= en_iyi_d:
                en_iyi, en_iyi_d = parca, d
    return en_iyi


# --- Değeri bölgeye atama (tasarım 5.4) -----------------------------------------------------------

HANE_KATSAYISI = 0.8      # hane başına genişlik/yükseklik (01–02 gerçek kutularında medyan 0,814)
W_HANE = 0.05             # 1 hane farkı ≈ köşegenin %5'i kadar mesafe cezası (~120 px)
MESAFE_UST_SINIR = 0.2    # köşegen oranı; daha uzak (bölge, kutu) çifti atanmaz
_YASAK = 1e6


def _merkez(kutu: Kutu) -> Nokta:
    return ((kutu[0] + kutu[2]) / 2, (kutu[1] + kutu[3]) / 2)


def hane_tahmini(kutu: Kutu) -> float:
    """Kutunun genişlik/yükseklik oranından hane sayısı tahmini (yuvarlanmaz)."""
    x1, y1, x2, y2 = kutu
    return ((x2 - x1) / max(y2 - y1, 1e-9)) / HANE_KATSAYISI


def degerleri_ata(bolgeler, ogeler, boyut, w_hane: float = W_HANE):
    """Qwen'in (değer, kutu) öğelerini bölgelere bire bir atar (toplam maliyet en küçük).

    boyut: (yükseklik, genişlik). Döner: (atanmış [(Bolge, değer)], yeri bulunamayan [değer],
    okunmamış [Bolge]).
    """
    from scipy.optimize import linear_sum_assignment

    kosegen = math.hypot(boyut[0], boyut[1])
    if not bolgeler or not ogeler:
        return [], [d for d, _ in ogeler], list(bolgeler)
    maliyet = [[0.0] * len(ogeler) for _ in bolgeler]
    for i, b in enumerate(bolgeler):
        mb = _merkez(b.kutu)
        for j, (deger, kutu) in enumerate(ogeler):
            d = math.dist(mb, _merkez(kutu)) / kosegen
            maliyet[i][j] = _YASAK if d > MESAFE_UST_SINIR else \
                d + w_hane * abs(hane_tahmini(b.kutu) - len(str(deger)))
    satirlar, sutunlar = linear_sum_assignment(maliyet)
    atanmis, kullanilan_b, kullanilan_o = [], set(), set()
    for i, j in zip(satirlar, sutunlar):
        if maliyet[i][j] < _YASAK:
            atanmis.append((bolgeler[i], ogeler[j][0]))
            kullanilan_b.add(i)
            kullanilan_o.add(j)
    yok = [ogeler[j][0] for j in range(len(ogeler)) if j not in kullanilan_o]
    okunmamis = [bolgeler[i] for i in range(len(bolgeler)) if i not in kullanilan_b]
    return atanmis, yok, okunmamis


# --- Bölgeyi parçaya bağlama ve Kroki (tasarım 5.5, 6) --------------------------------------------

EN_YAKIN_SINIRI = 6   # h katı: en yakın parça bundan uzaksa bağlanmaz
ISARET_PAYI = 0.5     # h katı: işaretin boştaki ucu bölge kutusuna en fazla bu kadar uzak


def _kutu_icinde(p: Nokta, kutu: Kutu, pay: float) -> bool:
    return kutu[0] - pay <= p[0] <= kutu[2] + pay and kutu[1] - pay <= p[1] <= kutu[3] + pay


def bagla(bolge: Bolge, sonuc: KenarSonucu, h: float) -> tuple[Parca | None, str | None]:
    """Bölgeyi bir parçaya bağlar. Sıra: ölçü işareti -> temas -> en yakın parça."""
    merkez = _merkez(bolge.kutu)
    adaylar = [i for i in sonuc.isaretler if _kutu_icinde(i.bit, bolge.kutu, ISARET_PAYI * h)]
    for isaret in sorted(adaylar, key=lambda i: math.dist(i.bit, merkez)):
        parca = parcayi_bul(isaret.bas, sonuc.kenarlar, h / 2)
        if parca:
            return parca, "isaret"
    if bolge.temas is not None:
        parca = parcayi_bul(bolge.temas, sonuc.kenarlar, h / 2)
        if parca:
            return parca, "temas"
    parca = parcayi_bul(merkez, sonuc.kenarlar, EN_YAKIN_SINIRI * h)
    return (parca, "en_yakin") if parca else (None, None)


def anlam(parca: Parca, kenar: Kenar) -> str:
    """Açıklığa ya da çok parçalı kenarın bir parçasına yazılan sayının anlamı mimara bağlı."""
    return "bilinmiyor" if parca.tur == "aciklik" or len(kenar.parcalar) > 1 else "uzunluk"


def kroki_kur(sonuc: KenarSonucu, atanmis, yeri_bulunamayan, okunmamis, h: float) -> Kroki:
    kenar_sozlugu = {k.id: k for k in sonuc.kenarlar}
    olculer = []
    for bolge, deger in atanmis:
        parca, neden = bagla(bolge, sonuc, h)
        olculer.append(Olcu(deger=int(deger), bolge=bolge.kutu, parca_id=parca.id if parca else None, neden=neden,
                            anlam=anlam(parca, kenar_sozlugu[parca.kenar_id]) if parca else "bilinmiyor"))
    return Kroki(eksen_acisi_derece=sonuc.eksen_acisi_derece, kenarlar=sonuc.kenarlar,
                 kontur_sirasi=sonuc.kontur_sirasi, olculer=tuple(olculer),
                 yeri_bulunamayan=tuple(int(d) for d in yeri_bulunamayan),
                 okunmamis_bolgeler=tuple(b.kutu for b in okunmamis))
