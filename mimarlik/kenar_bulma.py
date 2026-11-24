"""Mürekkep maskesinden kenar (duvar) bulma.

Adımlar (tasarım 5.2): çizgi parçaları (Hough) -> eksen açısı -> doğrudaş birleştirme -> ...
Bütün eşikler karakter yüksekliği h'nin katıdır.
"""

import math

import cv2
import numpy as np

from mimarlik import varsayimlar
from mimarlik.eslestirme import IptalIsareti, IsaretAdayi, KapiBoslugu, KapiIpucu, Kenar, KenarSonucu, Parca
from mimarlik.on_isleme import kalin_lekeleri_sil

ACI_TOLERANSI = 15.0      # derece: eksene bu kadar yakın çizgi yatay/dikey sayılır
BIRLESTIRME_ACISI = 20.0  # derece: kısa kalın çizgilerde Hough açısı ±12° oynar; doğrudaşlığı dik mesafe denetler
DUVAR_UZUNLUGU = 3        # h katı: bundan uzun çizgi kendiliğinden duvar
ACIKLIK_ARALIGI = (1, 8)  # h katı: aynı doğrudaki iki duvar arasındaki boşluk bu aralıktaysa açıklık
SARKAN_SINIRI = 6         # h katı: bir ucu boşta kalan bundan kısa "duvar" budanır (işaret + yazı birleşmesi)
# X işareti (mimar S5, KESİN: "çarpı = orada duvar yok"): eksene çapraz, birbirini kesen iki çizgi
CARPI_ACISI = (25.0, 65.0)   # derece: çizginin eksene göre açısı bu aralıktaysa çapraz
CARPI_KESISIM_ACISI = 60.0   # derece: iki çapraz çizgi arasındaki açı en az bu kadar
CARPI_KESISIM_PAYI = 0.25    # h katı: kesişim noktası iki çizgiye de bu kadar yakın (uçların biraz ötesi olabilir)
# Kapı boşluğu (3. adım, kullanıcı kararı 2026-11-24): boşta kalan iki duvar ucu arası, ipucuyla
KAPI_KAYMASI = 1.0           # h katı: kapının iki yanı bu kadar yana kayık olabilir (normal açıklıkta h/2)
KAPI_IPUCU_MESAFESI = 5.0    # h katı: etiket ya da sayı boşluğun ortasına en fazla bu kadar uzak (01: 2,2h, 02: 4,4h)
KAPI_OLCEK_PAYI = 10         # cm: ipucu yoksa ölçekten tahmin genişlik standart bir kapıya bu kadar yakın olmalı
SANAL_DUVAR = 0.5            # h katı: karşı uç dik bir duvarın ucuysa oraya konan sanal duvar parçası
TASMA_SINIRI = 1.5           # h katı: kapı yanındaki parça dik bir duvarı en fazla bu kadar aşıyorsa kırpılır


class _Cizgi:
    """Doğru parçası; birleştirilmiş çizgiler de bu sınıftadır."""

    __slots__ = ("bas", "bit")

    def __init__(self, bas, bit):
        self.bas, self.bit = (float(bas[0]), float(bas[1])), (float(bit[0]), float(bit[1]))

    @property
    def uzunluk(self):
        return math.dist(self.bas, self.bit)

    @property
    def aci(self):
        """atan2(dy, dx), derece, (-90, 90]."""
        a = math.degrees(math.atan2(self.bit[1] - self.bas[1], self.bit[0] - self.bas[0]))
        if a <= -90:
            a += 180
        elif a > 90:
            a -= 180
        return a


def _katla(a):
    """Açıyı 90°'lik katlarla (-45, 45] aralığına getirir."""
    while a <= -45:
        a += 90
    while a > 45:
        a -= 90
    return a


def _cizgi_parcalari(maske, h):
    cizgiler = cv2.HoughLinesP(maske.astype(np.uint8) * 255, rho=1, theta=np.pi / 360,
                               threshold=max(10, int(h / 2)), minLineLength=h, maxLineGap=h / 4)
    if cizgiler is None:
        return []
    return [_Cizgi((x1, y1), (x2, y2)) for x1, y1, x2, y2 in np.asarray(cizgiler).reshape(-1, 4)]


def _eksen_acisi(parcalar):
    """Uzunlukla ağırlıklı, 90°'ye göre katlanmış ortalama açı (4θ üzerinden dairesel ortalama)."""
    if not parcalar:
        return 0.0
    s = sum(p.uzunluk * math.sin(math.radians(4 * p.aci)) for p in parcalar)
    c = sum(p.uzunluk * math.cos(math.radians(4 * p.aci)) for p in parcalar)
    return _katla(math.degrees(math.atan2(s, c)) / 4)


def _yon(aci, eksen):
    """"yatay" | "dikey" | None (eğik): çizginin eksen açısına göre yönü."""
    d = (aci - eksen) % 180
    if d <= ACI_TOLERANSI or d >= 180 - ACI_TOLERANSI:
        return "yatay"
    if abs(d - 90) <= ACI_TOLERANSI:
        return "dikey"
    return None


def _aci_farki(a, b):
    d = abs(a - b) % 180
    return min(d, 180 - d)


def _birlestirilebilir(a, b, h):
    if _aci_farki(a.aci, b.aci) > BIRLESTIRME_ACISI:
        return False
    # b'nin uçlarının a'nın doğrusuna dik uzaklığı ve a'nın yönündeki boşluk
    ux, uy = a.bit[0] - a.bas[0], a.bit[1] - a.bas[1]
    n = math.hypot(ux, uy)
    ux, uy = ux / n, uy / n
    def dik(p):
        return abs((p[0] - a.bas[0]) * uy - (p[1] - a.bas[1]) * ux)
    def boy(p):
        return (p[0] - a.bas[0]) * ux + (p[1] - a.bas[1]) * uy
    if max(dik(b.bas), dik(b.bit)) > h / 3:
        return False
    t1, t2 = sorted((boy(b.bas), boy(b.bit)))
    bosluk = max(t1 - a.uzunluk, -t2, 0.0)
    return bosluk <= h / 2


def _uydur(grup):
    """Grup parçalarının uçlarından (uzunlukla ağırlıklı) en küçük kareler doğrusu ve uç noktaları."""
    noktalar, agirlik = [], []
    for p in grup:
        for q in (p.bas, p.bit):
            noktalar.append(q)
            agirlik.append(p.uzunluk)
    P = np.array(noktalar)
    w = np.array(agirlik)[:, None]
    merkez = (P * w).sum(0) / w.sum()
    kov = ((P - merkez) * w).T @ (P - merkez)
    _, vektorler = np.linalg.eigh(kov)
    u = vektorler[:, -1]
    t = (P - merkez) @ u
    return _Cizgi(merkez + t.min() * u, merkez + t.max() * u)


def _birlestir(parcalar, h, eksen):
    """Doğrudaş ve üst üste binen (ya da arası ≤ h/2) parçaları tek çizgiye birleştirir.

    Döner: [(çizgi, yön)]. Yön, birleşen çizginin açısından değil üyelerin uzunlukla ağırlıklı
    çoğunluğundan alınır: birleşme açıyı eksen toleransının dışına itebilir (14°+14° -> 22°), ama
    çıktı sözleşmesi yön için yalnız "yatay" | "dikey" kabul eder.
    """
    ebeveyn = list(range(len(parcalar)))

    def kok(i):
        while ebeveyn[i] != i:
            ebeveyn[i] = ebeveyn[ebeveyn[i]]
            i = ebeveyn[i]
        return i

    for i in range(len(parcalar)):
        for j in range(i + 1, len(parcalar)):
            if kok(i) != kok(j) and (_birlestirilebilir(parcalar[i], parcalar[j], h)
                                     or _birlestirilebilir(parcalar[j], parcalar[i], h)):
                ebeveyn[kok(i)] = kok(j)
    gruplar = {}
    for i, p in enumerate(parcalar):
        gruplar.setdefault(kok(i), []).append(p)
    sonuc = []
    for g in gruplar.values():
        agirlik = {}
        for p in g:
            yon = _yon(p.aci, eksen)
            if yon:
                agirlik[yon] = agirlik.get(yon, 0.0) + p.uzunluk
        sonuc.append((_uydur(g), max(agirlik, key=agirlik.get) if agirlik else None))
    return sonuc


# --- Bağlantılar: köşeler ve T-birleşimler ---------------------------------------------------------

def _segment_mesafesi(p, c):
    (x1, y1), (x2, y2) = c.bas, c.bit
    dx, dy = x2 - x1, y2 - y1
    n2 = dx * dx + dy * dy
    t = 0.0 if n2 == 0 else max(0.0, min(1.0, ((p[0] - x1) * dx + (p[1] - y1) * dy) / n2))
    return math.hypot(p[0] - x1 - t * dx, p[1] - y1 - t * dy)


def _kesisim(a, b):
    (x1, y1), (x2, y2), (x3, y3), (x4, y4) = a.bas, a.bit, b.bas, b.bit
    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(d) < 1e-9:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / d
    return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))


def _t(c, p):
    """p'nin c doğrultusundaki izdüşüm konumu (c.bas'tan piksel)."""
    ux, uy = c.bit[0] - c.bas[0], c.bit[1] - c.bas[1]
    n = math.hypot(ux, uy)
    return ((p[0] - c.bas[0]) * ux + (p[1] - c.bas[1]) * uy) / n


def _uc(c, p, tol):
    """p, c'nin hangi ucunda: "bas" | "bit" | None (ortada)."""
    t = _t(c, p)
    if t <= tol:
        return "bas"
    if t >= c.uzunluk - tol:
        return "bit"
    return None


def _baglantilar(cizgiler, yonler, tol):
    """[(i, j, P)]: farklı yönlü iki çizginin, ikisine de ≤ tol uzaklıktaki kesişimi."""
    sonuc = []
    for i in range(len(cizgiler)):
        for j in range(i + 1, len(cizgiler)):
            if yonler[i] == yonler[j]:
                continue
            p = _kesisim(cizgiler[i], cizgiler[j])
            if p and _segment_mesafesi(p, cizgiler[i]) <= tol and _segment_mesafesi(p, cizgiler[j]) <= tol:
                sonuc.append((i, j, p))
    return sonuc


# --- X işaretleri: iptal edilen duvar parçaları ---------------------------------------------------

def _carpilar(parcalar, eksen, h):
    """[(merkez, [çapraz çizgiler])]: birbirini kesen iki çapraz çizgi; yakın kesişimler (h) tek X sayılır."""
    capraz = [p for p in parcalar if CARPI_ACISI[0] <= (p.aci - eksen) % 90 <= CARPI_ACISI[1]]
    kesisimler = []
    for i in range(len(capraz)):
        for j in range(i + 1, len(capraz)):
            a, b = capraz[i], capraz[j]
            if _aci_farki(a.aci, b.aci) < CARPI_KESISIM_ACISI:
                continue
            p = _kesisim(a, b)
            if p and _segment_mesafesi(p, a) <= CARPI_KESISIM_PAYI * h and                     _segment_mesafesi(p, b) <= CARPI_KESISIM_PAYI * h:
                kesisimler.append((p, a, b))
    gruplar = []   # [noktalar, çizgiler]
    for p, a, b in kesisimler:
        for g in gruplar:
            if any(math.dist(p, q) <= h for q in g[0]):
                g[0].append(p)
                g[1].update((a, b))
                break
        else:
            gruplar.append([[p], {a, b}])
    return [((sum(q[0] for q in n) / len(n), sum(q[1] for q in n) / len(n)), list(c)) for n, c in gruplar]


def _iptal_et(cizgiler, yonler, carpilar, h, tol):
    """X'in üstünden geçtiği duvar çizgisinden, X'i içine alan parçayı (iki yandaki en yakın dik çizgi
    birleşimi ya da çizgi ucu arası) çıkarır. Döner: (çizgiler, yönler, iptaller)."""
    cizgiler, yonler, iptaller = list(cizgiler), list(yonler), []
    for merkez, capraz in carpilar:
        if not cizgiler:
            break
        yakin = [k for k in range(len(cizgiler)) if _segment_mesafesi(merkez, cizgiler[k]) <= tol]
        if not yakin:
            continue
        i = max(yakin, key=lambda k: cizgiler[k].uzunluk)   # iptal edilen bir duvar: X'in kendi kırıntısı değil
        c = cizgiler[i]
        uzunluk, tx = c.uzunluk, _t(c, merkez)
        sinirlar = [0.0, uzunluk]
        for j, d in enumerate(cizgiler):
            if j == i or yonler[j] == yonler[i] or _segment_mesafesi(merkez, d) <= tol:
                continue   # paralel çizgi ya da X'in kendi kırıntısı sınır değildir
            p = _kesisim(c, d)
            if p and _segment_mesafesi(p, c) <= tol and _segment_mesafesi(p, d) <= tol:
                sinirlar.append(min(max(_t(c, p), 0.0), uzunluk))
        ta = max(t for t in sinirlar if t <= tx)
        tb = min(t for t in sinirlar if t >= tx)
        ux, uy = (c.bit[0] - c.bas[0]) / uzunluk, (c.bit[1] - c.bas[1]) / uzunluk

        def nokta(t):
            return (c.bas[0] + t * ux, c.bas[1] + t * uy)

        kalan = [_Cizgi(nokta(a), nokta(b)) for a, b in ((0.0, ta), (tb, uzunluk)) if b - a > tol]
        cizgiler[i:i + 1] = kalan
        yonler[i:i + 1] = [yonler[i]] * len(kalan)
        iptaller.append(IptalIsareti(merkez=merkez, cizgiler=tuple((s.bas, s.bit) for s in capraz),
                                     silinen=(nokta(ta), nokta(tb))))
    return cizgiler, yonler, iptaller


# --- Kapı boşlukları (ipucuyla) ---------------------------------------------------------------------

def _bos_uc_mu(i, uc, cizgiler, baglantilar, tol):
    """i'nin `uc` ucunda (dik) başka bir çizgiyle birleşim yok mu?"""
    return not any(i in (a, b) and _uc(cizgiler[i], p, tol) == uc for a, b, p in baglantilar)


def _uc_noktasi(c, uc):
    return c.bas if uc == "bas" else c.bit


def _duvar_gibi(k, cizgiler, baglantilar, h):
    """Kendisi duvar boyunda (≥ DUVAR_UZUNLUGU·h) ya da öyle bir çizgiye değiyor: rakam çizgisi değil."""
    if cizgiler[k].uzunluk >= DUVAR_UZUNLUGU * h:
        return True
    return any(k in (a, b) and cizgiler[b if a == k else a].uzunluk >= DUVAR_UZUNLUGU * h for a, b, _ in baglantilar)


def _duvarin_ortasinda(k, uc, cizgiler, baglantilar, h, tol):
    """k'nin `uc` ucu duvar boyunda dik bir çizginin ORTASINA mı değiyor (T birleşimi)? Kapı oradan başlamaz:
    01'de `180`'in tiki üst duvarın ortasından odaya doğru uzanıyordu. Bir çizginin ucuna değmek (kapı kanadının
    menteşesi, köşe) engel değil."""
    for a, b, p in baglantilar:
        if k not in (a, b) or _uc(cizgiler[k], p, tol) != uc:
            continue
        diger = b if a == k else a
        if cizgiler[diger].uzunluk >= DUVAR_UZUNLUGU * h and _uc(cizgiler[diger], p, tol) is None:
            return True
    return False


def _kapi_adaylari(cizgiler, yonler, baglantilar, h, tol):
    """[(i, ui, j, uj, A, B, bosluk_px)]: i'nin A ucundan dışarı doğru, karşıda j'nin B ucu.

    Uçların boşta olması aranmaz: kapı kanadı ve ölçü çizgisi kapının uçlarına değer (02). İki yan da duvar
    gibi olmalı; asıl eleme ipucunda (boşluğun ortasına yakın etiket/sayı) ya da ölçekte.
    """
    adaylar = []
    for i, c in enumerate(cizgiler):
        if not _duvar_gibi(i, cizgiler, baglantilar, h):
            continue
        for ui in ("bas", "bit"):
            if _duvarin_ortasinda(i, ui, cizgiler, baglantilar, h, tol):
                continue
            a, diger = _uc_noktasi(c, ui), _uc_noktasi(c, _diger_uc(ui))
            dx, dy = (a[0] - diger[0]) / c.uzunluk, (a[1] - diger[1]) / c.uzunluk   # dışarı doğru
            for j, d in enumerate(cizgiler):
                if j == i or not _duvar_gibi(j, cizgiler, baglantilar, h):
                    continue
                if max(c.uzunluk, d.uzunluk) < DUVAR_UZUNLUGU * h:
                    continue   # en az bir yan gerçek duvar: iki kısa çizgi (tik, rakam) arası kapı sayılmaz
                for uj in ("bas", "bit"):
                    b = _uc_noktasi(d, uj)
                    s = (b[0] - a[0]) * dx + (b[1] - a[1]) * dy
                    kayma = abs((b[0] - a[0]) * dy - (b[1] - a[1]) * dx)
                    if not (ACIKLIK_ARALIGI[0] * h <= s <= ACIKLIK_ARALIGI[1] * h and kayma <= KAPI_KAYMASI * h):
                        continue
                    if yonler[j] == yonler[i] and ((_t(d, a) < _t(d, b)) != (uj == "bas") or
                                                   _duvarin_ortasinda(j, uj, cizgiler, baglantilar, h, tol)):
                        continue   # karşıdaki parça da bu doğrultuda: boşluğa bakan ucu B olmalı
                    if yonler[j] != yonler[i] and (d.uzunluk < SARKAN_SINIRI * h or
                                                   not _bos_uc_mu(j, uj, cizgiler, baglantilar, tol)):
                        continue   # eksik kısa parçayı tahmin ediyoruz: karşıda boşta kalmış UZUN bir duvar ucu şart
                    adaylar.append((i, ui, j, uj, a, b, s))
    return adaylar


def _kapi_secimi(aday, ipuclari, olcek, h):
    """(kaynak, değer, uzaklık) ya da None: önce etiket, sonra sayı (yakında), yoksa ölçekten genişlik."""
    _, _, _, _, a, b, s = aday
    orta = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)   # etiket/ölçü kapının ortasına yazılır
    for kaynak in ("etiket", "sayi"):
        yakin = [(math.dist(ip.nokta, orta), ip) for ip in ipuclari if ip.kaynak == kaynak]
        yakin = [(m, ip) for m, ip in yakin if m <= KAPI_IPUCU_MESAFESI * h]
        if yakin:
            m, ip = min(yakin, key=lambda x: x[0])
            return kaynak, ip.deger, m
    if olcek:
        genislik = s * olcek
        en_yakin = min(varsayimlar.KAPI_GENISLIKLERI, key=lambda g: abs(g - genislik))
        if abs(en_yakin - genislik) <= KAPI_OLCEK_PAYI:
            return "olcek", en_yakin, float("inf")
    return None


def _tasmayi_kirp(k, uc, cizgiler, yonler, baglantilar, h, tol):
    """k'nin `uc` ucu boştaysa ve duvar boyunda dik bir çizgi k'yi bu uca TASMA_SINIRI·h'den yakın kesiyorsa,
    k'yi orada keser (02: kapının üstündeki parça üst duvarı aşıyor)."""
    if not _bos_uc_mu(k, uc, cizgiler, baglantilar, tol):
        return
    c = cizgiler[k]
    u = _uc_noktasi(c, uc)
    for j, d in enumerate(cizgiler):
        if j == k or yonler[j] == yonler[k] or d.uzunluk < DUVAR_UZUNLUGU * h:
            continue
        p = _kesisim(c, d)
        if p and _segment_mesafesi(p, c) <= tol and _segment_mesafesi(p, d) <= tol and \
                tol < math.dist(p, u) <= TASMA_SINIRI * h:
            diger = _uc_noktasi(c, _diger_uc(uc))
            cizgiler[k] = _Cizgi(p, diger) if uc == "bas" else _Cizgi(diger, p)
            return


def _kapilari_tamamla(cizgiler, yonler, ipuclari, olcek, h, tol):
    """İpucuyla doğrulanan kapı boşluklarını açıklık çifti yapar. Döner: (çizgiler, yönler, zorunlu, kapılar).

    zorunlu: [(i, j, ui, uj)] açıklık çiftleri (boşluğa bakan uçlarıyla). Karşı uç dik bir duvarın ucuysa
    (01: kapının altındaki kısa parça bulunamamış) o uca bu doğrultuda SANAL_DUVAR·h'lik bir parça eklenir.
    """
    cizgiler, yonler = list(cizgiler), list(yonler)
    baglantilar = _baglantilar(cizgiler, yonler, tol)
    secilenler = []
    for aday in _kapi_adaylari(cizgiler, yonler, baglantilar, h, tol):
        secim = _kapi_secimi(aday, ipuclari, olcek, h)
        if secim:
            secilenler.append((("etiket", "sayi", "olcek").index(secim[0]), secim[2], aday, secim))
    kullanilan, kapili_kisa, zorunlu, kapilar = set(), set(), [], []
    for _, _, (i, ui, j, uj, a, b, s), (kaynak, deger, _) in sorted(secilenler, key=lambda x: (x[0], x[1])):
        if (i, ui) in kullanilan or (j, uj) in kullanilan or {i, j} & kapili_kisa:
            continue   # her uç bir kapıya; kısa bir parçanın iki yanında kapı olmaz
        kullanilan |= {(i, ui), (j, uj)}
        kapili_kisa |= {k for k in (i, j) if cizgiler[k].uzunluk < DUVAR_UZUNLUGU * h}
        if yonler[j] != yonler[i]:   # karşıda dik bir duvarın ucu: o uca bu doğrultuda sanal duvar parçası
            dx, dy = (a[0] - b[0]), (a[1] - b[1])
            n = math.hypot(dx, dy)
            sanal_uc = (b[0] + dx / n * SANAL_DUVAR * h, b[1] + dy / n * SANAL_DUVAR * h)
            cizgiler.append(_Cizgi(b, sanal_uc))   # bas = B (duvara bağlı), bit = boşluğa bakan uç
            yonler.append(yonler[i])
            j, uj = len(cizgiler) - 1, "bit"
        else:
            _tasmayi_kirp(j, _diger_uc(uj), cizgiler, yonler, baglantilar, h, tol)
        _tasmayi_kirp(i, _diger_uc(ui), cizgiler, yonler, baglantilar, h, tol)
        zorunlu.append((i, j, ui, uj))
        kapilar.append(KapiBoslugu(bas=a, bit=b, kaynak=kaynak, deger=int(deger)))
    return cizgiler, yonler, zorunlu, kapilar


# --- Duvar / işaret / açıklık ---------------------------------------------------------------------

def _uca_bagli_duvar(i, uc, baglantilar, duvar, cizgiler, tol):
    """i'nin `uc` ucunda bir duvara bağlantı noktası (yoksa None)."""
    for a, b, p in baglantilar:
        if i in (a, b):
            diger = b if a == i else a
            if diger in duvar and _uc(cizgiler[i], p, tol) == uc:
                return p
    return None


def _acik_cift(a, b, h):
    """a ve b aynı doğrudaysa ve aralarındaki boşluk açıklık aralığındaysa (a'nın boşluğa bakan ucu, b'ninki)."""
    if _aci_farki(a.aci, b.aci) > BIRLESTIRME_ACISI:
        return None
    ux, uy = (a.bit[0] - a.bas[0]) / a.uzunluk, (a.bit[1] - a.bas[1]) / a.uzunluk
    if max(abs((p[0] - a.bas[0]) * uy - (p[1] - a.bas[1]) * ux) for p in (b.bas, b.bit)) > h / 2:
        return None
    tb = sorted((_t(a, b.bas), _t(a, b.bit)))
    alt, ust = ACIKLIK_ARALIGI[0] * h, ACIKLIK_ARALIGI[1] * h
    if alt <= tb[0] - a.uzunluk <= ust:   # b, a'nın bit ucunun ötesinde
        return "bit", ("bas" if _t(a, b.bas) < _t(a, b.bit) else "bit")
    if alt <= -tb[1] <= ust:              # b, a'nın bas ucunun gerisinde
        return "bas", ("bit" if _t(a, b.bas) < _t(a, b.bit) else "bas")
    return None


def _diger_uc(uc):
    return "bit" if uc == "bas" else "bas"


def _siniflandir(cizgiler, baglantilar, h, tol, zorunlu=()):
    """Döner: (duvar indeksleri, açıklık çiftleri [(i, j)]). zorunlu: kapı kuralının çiftleri [(i, j, ui, uj)]."""
    duvar = {i for i, c in enumerate(cizgiler) if c.uzunluk >= DUVAR_UZUNLUGU * h}
    ciftler = [(i, j) for i, j, _, _ in zorunlu]
    uclar = {(i, j): (ui, uj) for i, j, ui, uj in zorunlu}   # boşluğa bakan uçlar (budamada boşta sayılmaz)
    duvar.update(k for i, j, _, _ in zorunlu for k in (i, j))
    degisti = True
    while degisti:
        degisti = False
        for i in range(len(cizgiler)):
            if i not in duvar and all(_uca_bagli_duvar(i, u, baglantilar, duvar, cizgiler, tol)
                                      for u in ("bas", "bit")):
                duvar.add(i)
                degisti = True
        for i in range(len(cizgiler)):
            for j in range(i + 1, len(cizgiler)):
                if (i, j) in ciftler:
                    continue
                cift = _acik_cift(cizgiler[i], cizgiler[j], h)
                if not cift:
                    continue
                ui, uj = cift  # boşluğa bakan uçlar; uzak uçlar duvara bağlı olmalı (ya da kendisi duvar)
                if all(k in duvar or _uca_bagli_duvar(k, _diger_uc(u), baglantilar, duvar, cizgiler, tol)
                       for k, u in ((i, ui), (j, uj))):
                    ciftler.append((i, j))
                    uclar[(i, j)] = (ui, uj)
                    duvar.update((i, j))
                    degisti = True
    return _sarkanlari_buda(cizgiler, baglantilar, duvar, ciftler, uclar, h, tol)


def _sarkanlari_buda(cizgiler, baglantilar, duvar, ciftler, uclar, h, tol):
    """Bir ucu hiçbir duvara bağlı olmayan kısa (< SARKAN_SINIRI·h) "duvarları" eler.

    Ölçü işareti rakam çizgileriyle birleşince 3h'yi aşabiliyor ("240"); bu çizgiler bir ucu boşta
    kaldığı için ayırt edilir. Açıklığa bakan uçlar boşta sayılmaz. Uzun duvarlar hiç budanmaz: bir köşe
    kaçırılırsa budamanın bütün dış hatta yayılmasın.
    """
    duvar = set(duvar)
    korunan = set()
    for i, j in ciftler:
        ui, uj = uclar[(i, j)]
        korunan |= {(i, ui), (j, uj)}
    degisti = True
    while degisti:
        degisti = False
        for i in sorted(duvar):
            if cizgiler[i].uzunluk >= SARKAN_SINIRI * h:
                continue
            if any((i, u) not in korunan and not _uca_bagli_duvar(i, u, baglantilar, duvar, cizgiler, tol)
                   for u in ("bas", "bit")):
                duvar.discard(i)
                degisti = True
    return duvar, [(i, j) for i, j in ciftler if i in duvar and j in duvar]


def _isaretler(cizgiler, baglantilar, duvar, h, tol):
    """Tek ucu bir duvara bağlı, diğer ucu boşta çizgiler. Uzunluk sınırı yok: işaret yazıyla birleşebilir."""
    adaylar = []
    for i, c in enumerate(cizgiler):
        if i in duvar or c.uzunluk >= SARKAN_SINIRI * h:
            continue
        uclar = {u: _uca_bagli_duvar(i, u, baglantilar, duvar, cizgiler, tol) for u in ("bas", "bit")}
        bagli = [u for u, p in uclar.items() if p]
        if len(bagli) == 1:
            u = bagli[0]
            adaylar.append((c.uzunluk, uclar[u], c.bit if u == "bas" else c.bas))
    secilen = []  # aynı duvar noktasına değen kopyalardan uzun olanı kalır
    for uzunluk, bas, bit in sorted(adaylar, key=lambda a: -a[0]):
        if all(math.dist(bas, s.bas) > h / 2 for s in secilen):
            secilen.append(IsaretAdayi(bas=bas, bit=tuple(bit)))
    return secilen


# --- Kenarlar ve parçalar -------------------------------------------------------------------------

def _kenar_parcalari(grup, cizgiler, baglantilar, duvar, tol):
    """Bir kenar grubunun (açıklıkla ayrılmış doğrudaş duvarlar) parça listesi: [(tür, bas, bit)]."""
    eksen = _uydur([cizgiler[i] for i in grup])
    araliklar = sorted(tuple(sorted((_t(eksen, cizgiler[i].bas), _t(eksen, cizgiler[i].bit)))) for i in grup)
    duvar_araliklari = [list(araliklar[0])]
    for a, b in araliklar[1:]:
        if a <= duvar_araliklari[-1][1] + tol:
            duvar_araliklari[-1][1] = max(duvar_araliklari[-1][1], b)
        else:
            duvar_araliklari.append([a, b])
    t0, t1 = duvar_araliklari[0][0], duvar_araliklari[-1][1]

    def nokta(t):
        ux, uy = (eksen.bit[0] - eksen.bas[0]) / eksen.uzunluk, (eksen.bit[1] - eksen.bas[1]) / eksen.uzunluk
        return (eksen.bas[0] + t * ux, eksen.bas[1] + t * uy)

    uc_noktalari = {}
    kirilmalar = set()
    for a, b, p in baglantilar:
        if (a in grup) == (b in grup):
            continue
        diger = b if a in grup else a
        if diger not in duvar:
            continue
        t = _t(eksen, p)
        if abs(t - t0) <= tol:
            uc_noktalari[0] = p
        elif abs(t - t1) <= tol:
            uc_noktalari[1] = p
        elif t0 < t < t1:
            kirilmalar.add(round(t, 1))
    sinirlar = sorted({t0, t1, *kirilmalar, *(x for ar in duvar_araliklari for x in ar)})
    sade = [sinirlar[0]]
    for t in sinirlar[1:]:
        if t - sade[-1] > tol:
            sade.append(t)
    sade[-1] = t1

    def aciklikta(t):
        return not any(a - tol <= t <= b + tol for a, b in duvar_araliklari)

    parcalar = []
    for k, (a, b) in enumerate(zip(sade, sade[1:])):
        pa = uc_noktalari.get(0, nokta(a)) if k == 0 else nokta(a)
        pb = uc_noktalari.get(1, nokta(b)) if k == len(sade) - 2 else nokta(b)
        parcalar.append(("aciklik" if aciklikta((a + b) / 2) else "duvar", pa, pb))
    return parcalar


def _dis_bolge(parca_listeleri, sekil, kalinlik):
    """Kenarların dışında kalan (görüntü kenarından ulaşılabilen) pikseller için bool maske."""
    yuk, gen = sekil
    tuval = np.zeros((yuk + 2, gen + 2), np.uint8)
    for parcalar in parca_listeleri:
        for _, a, b in parcalar:
            cv2.line(tuval, (int(round(a[0])) + 1, int(round(a[1])) + 1),
                     (int(round(b[0])) + 1, int(round(b[1])) + 1), 255, kalinlik)
    doldurma = np.zeros((yuk + 4, gen + 4), np.uint8)
    cv2.floodFill(tuval, doldurma, (0, 0), 128)
    return (tuval == 128)[1:-1, 1:-1]


def kenarlari_bul(maske: np.ndarray, h: float, kapi_ipuclari: tuple[KapiIpucu, ...] = (),
                  olcek: float | None = None) -> KenarSonucu:
    """kapi_ipuclari / olcek verilirse kapı kuralı çalışır (boşta iki duvar ucu arasındaki boşluk, yakınında
    K etiketi ya da kapı genişliğinde okunmuş sayı varsa; yoksa ölçekten tahminle). Verilmezse çalışmaz."""
    tol = 0.75 * h  # elle çizilen köşelerde çizgiler tam buluşmuyor; h/2 02'nin konturunu kapatmıyordu
    parcalar = _cizgi_parcalari(kalin_lekeleri_sil(maske, h), h)
    eksen = _eksen_acisi(parcalar)
    birlesik = _birlestir([p for p in parcalar if _yon(p.aci, eksen)], h, eksen)
    cizgiler = [c for c, _ in birlesik]
    yonler = [y for _, y in birlesik]
    cizgiler, yonler, iptaller = _iptal_et(cizgiler, yonler, _carpilar(parcalar, eksen, h), h, tol)
    zorunlu, kapilar = [], []
    if kapi_ipuclari or olcek:
        cizgiler, yonler, zorunlu, kapilar = _kapilari_tamamla(cizgiler, yonler, kapi_ipuclari, olcek, h, tol)
    baglantilar = _baglantilar(cizgiler, yonler, tol)
    duvar, ciftler = _siniflandir(cizgiler, baglantilar, h, tol, zorunlu)
    isaretler = _isaretler(cizgiler, baglantilar, duvar, h, tol)
    if not duvar:
        return KenarSonucu(eksen, (), (), tuple(isaretler), tuple(iptaller), tuple(kapilar))

    # açıklık çiftleriyle bağlı duvarlar tek kenar grubudur
    ebeveyn = {i: i for i in duvar}

    def kok(i):
        while ebeveyn[i] != i:
            i = ebeveyn[i]
        return i

    for i, j in ciftler:
        ebeveyn[kok(i)] = kok(j)
    gruplar = {}
    for i in sorted(duvar):
        gruplar.setdefault(kok(i), set()).add(i)
    gruplar = list(gruplar.values())
    parca_listeleri = [_kenar_parcalari(g, cizgiler, baglantilar, duvar, tol) for g in gruplar]

    # dış kontur: bir yanı dışarıda, diğer yanı içeride olan kenarlar; saat yönünde yönlendirilir
    dis = _dis_bolge(parca_listeleri, maske.shape, 3)
    adim = max(4.0, h / 2)

    def disarida(p):
        x, y = int(round(p[0])), int(round(p[1]))
        return not (0 <= y < dis.shape[0] and 0 <= x < dis.shape[1]) or bool(dis[y, x])

    kayitlar = []  # (konturda, parça listesi, yön)
    for g, pl in zip(gruplar, parca_listeleri):
        bas, bit = pl[0][1], pl[-1][2]
        dx, dy = bit[0] - bas[0], bit[1] - bas[1]
        n = math.hypot(dx, dy)
        nx, ny = -dy / n, dx / n
        en_uzun = max(pl, key=lambda q: math.dist(q[1], q[2]))
        m = ((en_uzun[1][0] + en_uzun[2][0]) / 2, (en_uzun[1][1] + en_uzun[2][1]) / 2)
        s1, s2 = disarida((m[0] + nx * adim, m[1] + ny * adim)), disarida((m[0] - nx * adim, m[1] - ny * adim))
        yon = yonler[min(g)]  # gruptaki çizgiler doğrudaş: yönleri aynı
        konturda = s1 != s2
        ters = s1 if konturda else ((dx < 0) if yon == "yatay" else (dy < 0))
        if ters:
            pl = [(t, b, a) for t, a, b in reversed(pl)]
        kayitlar.append((konturda, pl, yon))

    ic = ~dis
    konturlar, _ = cv2.findContours(ic.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    sira = []
    if konturlar:
        k = max(konturlar, key=cv2.contourArea).reshape(-1, 2).astype(float)
        if np.sum(k[:, 0] * np.roll(k[:, 1], -1) - np.roll(k[:, 0], -1) * k[:, 1]) < 0:
            k = k[::-1]  # saat yönü (görüntü koordinatında pozitif alan)
        for idx, (konturda, pl, _) in enumerate(kayitlar):
            if konturda:
                a, b = pl[0][1], pl[-1][2]
                q = (a[0] + 0.25 * (b[0] - a[0]), a[1] + 0.25 * (b[1] - a[1]))
                sira.append((int(np.argmin(((k - q) ** 2).sum(1))), idx))
        sira.sort()
        if sira:
            ilk = min(range(len(sira)), key=lambda s: sum(kayitlar[sira[s][1]][1][0][1]))
            sira = sira[ilk:] + sira[:ilk]
    kontur_idx = [idx for _, idx in sira]
    ic_idx = sorted((i for i, r in enumerate(kayitlar) if i not in kontur_idx),
                    key=lambda i: (kayitlar[i][1][0][1][1], kayitlar[i][1][0][1][0]))

    kenarlar = []
    for no, idx in enumerate(kontur_idx + ic_idx, 1):
        konturda, pl, yon = kayitlar[idx]
        kid = f"K{no}"
        kenarlar.append(Kenar(kid, yon, tuple(Parca(f"{kid}.{m}", kid, t, a, b) for m, (t, a, b) in enumerate(pl, 1)),
                              konturda and idx in kontur_idx))
    return KenarSonucu(eksen, tuple(kenarlar), tuple(f"K{n}" for n in range(1, len(kontur_idx) + 1)),
                       tuple(isaretler), tuple(iptaller), tuple(kapilar))
