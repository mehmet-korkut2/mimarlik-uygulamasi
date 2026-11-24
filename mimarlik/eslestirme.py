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
class IptalIsareti:
    """Duvar çizgisinin üstüne çizilmiş X (mimar, S5: "çarpı = orada duvar yok"): silinen duvar parçası."""
    merkez: Nokta
    cizgiler: tuple[tuple[Nokta, Nokta], ...]   # X'in çapraz çizgileri
    silinen: tuple[Nokta, Nokta]                # duvar çizgisinden çıkarılan parça


@dataclass(frozen=True)
class KapiIpucu:
    """Kapı boşluğunun yakınında olduğu bilinen işaret: K etiketi ("K90"), kapı genişliğinde okunmuş sayı."""
    nokta: Nokta
    kaynak: str      # "etiket" | "sayi"
    deger: int


@dataclass(frozen=True)
class KapiBoslugu:
    """Kenar bulmanın kapı kuralıyla tamamladığı açıklık (iki duvar ucu arası)."""
    bas: Nokta
    bit: Nokta
    kaynak: str      # "etiket" | "sayi"
    deger: int       # kapı genişliği (cm): ipucunun değeri


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
    kutu_uzakligi: float | None = None   # h: Qwen kutusu ile bölge kutusu arası (None: bilinmiyor, ör. testte)


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
    iptaller: tuple[IptalIsareti, ...] = ()   # X ile iptal edilen duvar parçaları
    kapilar: tuple[KapiBoslugu, ...] = ()     # kapı kuralıyla tamamlanan açıklıklar
    bosluklar: tuple[tuple[Nokta, Nokta], ...] = ()   # kapı adayı ama kanıtsız boşluklar (kullanıcıya sorulur)


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


ESITLIK_PAYI = 2.0  # px: bu kadar farkla yakın parçalar "eşit" sayılır (ör. iki parçanın ortak ucu)


def _izdusum_icinde(q: Nokta, parca: Parca) -> bool:
    (x1, y1), (x2, y2) = parca.bas, parca.bit
    dx, dy = x2 - x1, y2 - y1
    n2 = dx * dx + dy * dy
    return n2 > 0 and 0.0 <= ((q[0] - x1) * dx + (q[1] - y1) * dy) / n2 <= 1.0


def parcayi_bul(p: Nokta, kenarlar, tolerans: float, tercih: Nokta | None = None) -> Parca | None:
    """Noktaya en yakın parça; uzaklık toleransı aşıyorsa None.

    Nokta iki parçanın ortak ucundaysa (ölçü işareti çoğu zaman tam oraya düşer) seçim parça sırasına
    kalmasın diye: eşit yakın parçalardan, `tercih` noktasının (ör. sayının merkezi) izdüşümü içine düşen seçilir.
    """
    adaylar = [(nokta_parca_mesafesi(p, parca), parca) for kenar in kenarlar for parca in kenar.parcalar]
    adaylar = [(d, parca) for d, parca in adaylar if d <= tolerans]
    if not adaylar:
        return None
    en_az = min(d for d, _ in adaylar)
    esitler = [parca for d, parca in adaylar if d <= en_az + ESITLIK_PAYI]
    if tercih is not None and len(esitler) > 1:
        icinde = [parca for parca in esitler if _izdusum_icinde(tercih, parca)]
        if icinde:
            return min(icinde, key=lambda parca: nokta_parca_mesafesi(tercih, parca))
    return min(adaylar, key=lambda a: a[0])[1]


# --- Değeri bölgeye atama (tasarım 5.4) -----------------------------------------------------------

HANE_KATSAYISI = 0.8      # hane başına genişlik/yükseklik (01–02 gerçek kutularında medyan 0,814)
# Ö2 (2026-11-24, deneyler/deger_atama): atama YEREL ve SINIRLI. Eskiden merkez uzaklığı köşegenin %20'sine
# (~12,7 h) kadar kabul ediliyordu; Qwen kutusu kayınca değerler zincirleme komşu bölgelere kayıyordu (01'in
# "merdiven" şekli). 14 kayıtlı çalıştırmada yanlış atama 67 -> 29, doğru 124 -> 108, yeri bulunamayan 2 -> 56.
ATAMA_SINIRI = 1.0        # h: Qwen kutusu ile bölge kutusu arası (kutular örtüşürse 0) bundan uzaksa atanmaz
HANE_CEZASI = 0.5         # h: bir hane farkının mesafe karşılığı
EMIN_YAKINLIK = 0.5       # h: "emin" için kutu–bölge uzaklığı en çok bu (ölçümde isabet 106/131)
_YASAK = 1e6


def _merkez(kutu: Kutu) -> Nokta:
    return ((kutu[0] + kutu[2]) / 2, (kutu[1] + kutu[3]) / 2)


def kutu_uzakligi(a: Kutu, b: Kutu) -> float:
    """İki kutu arasındaki en kısa uzaklık (örtüşüyorlarsa 0)."""
    dx = max(a[0] - b[2], b[0] - a[2], 0.0)
    dy = max(a[1] - b[3], b[1] - a[3], 0.0)
    return math.hypot(dx, dy)


def hane_tahmini(kutu: Kutu) -> float:
    """Kutunun genişlik/yükseklik oranından hane sayısı tahmini (yuvarlanmaz)."""
    x1, y1, x2, y2 = kutu
    return ((x2 - x1) / max(y2 - y1, 1e-9)) / HANE_KATSAYISI


def degerleri_ata(bolgeler, ogeler, h: float, w_hane: float = HANE_CEZASI):
    """Qwen'in (değer, kutu) öğelerini bölgelere bire bir atar (toplam maliyet en küçük).

    Yalnız kutusu bölgeye ATAMA_SINIRI·h'den yakın çiftler aday: uzaktaki değer zorla atanmaz, "yeri
    bulunamadı" kalır (Y2'ye / kullanıcıya). Maliyet (h): kutu–bölge uzaklığı + w_hane · hane farkı.
    Döner: (atanmış [(Bolge, değer, kutu–bölge uzaklığı h)], yeri bulunamayan [değer], okunmamış [Bolge]).
    """
    from scipy.optimize import linear_sum_assignment

    if not bolgeler or not ogeler:
        return [], [d for d, _ in ogeler], list(bolgeler)
    maliyet = [[0.0] * len(ogeler) for _ in bolgeler]
    uzaklik = [[0.0] * len(ogeler) for _ in bolgeler]
    for i, b in enumerate(bolgeler):
        for j, (deger, kutu) in enumerate(ogeler):
            u = kutu_uzakligi(b.kutu, kutu) / h
            uzaklik[i][j] = u
            maliyet[i][j] = _YASAK if u > ATAMA_SINIRI else u + w_hane * abs(hane_tahmini(b.kutu) - len(str(deger)))
    satirlar, sutunlar = linear_sum_assignment(maliyet)
    atanmis, kullanilan_b, kullanilan_o = [], set(), set()
    for i, j in zip(satirlar, sutunlar):
        if maliyet[i][j] < _YASAK:
            atanmis.append((bolgeler[i], ogeler[j][0], round(uzaklik[i][j], 2)))
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
        parca = parcayi_bul(isaret.bas, sonuc.kenarlar, h / 2, tercih=merkez)
        if parca:
            return parca, "isaret"
    if bolge.temas is not None:
        parca = parcayi_bul(bolge.temas, sonuc.kenarlar, h / 2, tercih=merkez)
        if parca:
            return parca, "temas"
    parca = parcayi_bul(merkez, sonuc.kenarlar, EN_YAKIN_SINIRI * h, tercih=merkez)
    return (parca, "en_yakin") if parca else (None, None)


def anlam(parca: Parca, kenar: Kenar) -> str:
    """Açıklığa ya da çok parçalı kenarın bir parçasına yazılan sayının anlamı mimara bağlı."""
    return "bilinmiyor" if parca.tur == "aciklik" or len(kenar.parcalar) > 1 else "uzunluk"


def kroki_kur(sonuc: KenarSonucu, atanmis, yeri_bulunamayan, okunmamis, h: float) -> Kroki:
    kenar_sozlugu = {k.id: k for k in sonuc.kenarlar}
    olculer = []
    for bolge, deger, *uzaklik in atanmis:
        parca, neden = bagla(bolge, sonuc, h)
        olculer.append(Olcu(deger=int(deger), bolge=bolge.kutu, parca_id=parca.id if parca else None, neden=neden,
                            anlam=anlam(parca, kenar_sozlugu[parca.kenar_id]) if parca else "bilinmiyor",
                            kutu_uzakligi=uzaklik[0] if uzaklik else None))
    return Kroki(eksen_acisi_derece=sonuc.eksen_acisi_derece, kenarlar=sonuc.kenarlar,
                 kontur_sirasi=sonuc.kontur_sirasi, olculer=tuple(olculer),
                 yeri_bulunamayan=tuple(int(d) for d in yeri_bulunamayan),
                 okunmamis_bolgeler=tuple(b.kutu for b in okunmamis))
