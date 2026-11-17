"""Eşleştirme ölçümünün puanlama kütüphanesi (tasarım 7.2).

Gerçek cevap: gercek_eslestirme.py (kenar parçaları, sayı -> parça) + ../bul_kes_okut/konumlar.py (kutular).
"""

import math
import sys
from collections import Counter
from pathlib import Path

KLASOR = Path(__file__).resolve().parent
REPO = KLASOR.parents[1]
for yol in (REPO, KLASOR, KLASOR.parent / "bul_kes_okut"):
    if str(yol) not in sys.path:
        sys.path.insert(0, str(yol))

from gercek_eslestirme import ANLAM_BILINMIYOR, ESLESME, KAPSAM_BELIRSIZ, KENARLAR, KONTUR  # noqa: E402
from konumlar import GERCEK  # noqa: E402
from mimarlik.eslestirme import Kenar, KenarSonucu, Parca  # noqa: E402

ACI_FARKI = 20.0  # derece: kenara_eslestir için paralellik


def gercek_kenarlar(kod: str) -> KenarSonucu:
    kenarlar = []
    for kid, parcalar in KENARLAR[kod].items():
        (_, _, a, _), (_, _, _, b) = parcalar[0], parcalar[-1]
        yon = "yatay" if abs(b[0] - a[0]) > abs(b[1] - a[1]) else "dikey"
        kenarlar.append(Kenar(kid, yon, tuple(Parca(pid, kid, tur, bas, bit) for pid, tur, bas, bit in parcalar),
                              kid in KONTUR[kod]))
    return KenarSonucu(0.0, tuple(kenarlar), tuple(KONTUR[kod]), ())


def gercek_ciftler(kod: str) -> list[tuple[int, str]]:
    return [(deger, ESLESME[kod][ad]) for ad, deger, _ in GERCEK[kod]]


def mimara_bagli_ciftler(kod: str) -> list[tuple[int, str]]:
    adlar = ANLAM_BILINMIYOR[kod] | KAPSAM_BELIRSIZ[kod]
    return [(deger, ESLESME[kod][ad]) for ad, deger, _ in GERCEK[kod] if ad in adlar]


def _parcalar(sonuc):
    return [p for k in sonuc.kenarlar for p in k.parcalar]


def _uc_farki(p, q):
    """İki parçanın uçları arasındaki en büyük uzaklık (yön fark etmez)."""
    return min(max(math.dist(p.bas, q.bas), math.dist(p.bit, q.bit)),
               max(math.dist(p.bas, q.bit), math.dist(p.bit, q.bas)))


def parcalari_eslestir(bulunan: KenarSonucu, gercek: KenarSonucu, tol: float = 25) -> dict[str, str]:
    """Bulunan parça id -> gerçek parça id; iki uç da ≤ tol. Bire bir, en yakın çift önce."""
    adaylar = sorted((_uc_farki(b, g), b.id, g.id) for b in _parcalar(bulunan) for g in _parcalar(gercek))
    eslesme, kullanilan = {}, set()
    for fark, bid, gid in adaylar:
        if fark > tol:
            break
        if bid not in eslesme and gid not in kullanilan:
            eslesme[bid] = gid
            kullanilan.add(gid)
    return eslesme


def _segment_mesafesi(p, q):
    from mimarlik.eslestirme import nokta_parca_mesafesi
    return nokta_parca_mesafesi(p, q)


def _aci(p):
    return math.degrees(math.atan2(p.bit[1] - p.bas[1], p.bit[0] - p.bas[0])) % 180


def kenara_eslestir(bulunan: KenarSonucu, gercek: KenarSonucu, tol: float = 25) -> dict[str, str]:
    """Bulunan parça id -> gerçek kenar id: parçanın orta noktası paralel bir gerçek parçaya ≤ tol."""
    sonuc = {}
    for b in _parcalar(bulunan):
        orta = ((b.bas[0] + b.bit[0]) / 2, (b.bas[1] + b.bit[1]) / 2)
        en_iyi = None
        for g in _parcalar(gercek):
            fark = abs(_aci(b) - _aci(g)) % 180
            if min(fark, 180 - fark) > ACI_FARKI:
                continue
            d = _segment_mesafesi(orta, g)
            if d <= tol and (en_iyi is None or d < en_iyi[0]):
                en_iyi = (d, g.kenar_id)
        if en_iyi:
            sonuc[b.id] = en_iyi[1]
    return sonuc


def kenar_puani(bulunan: KenarSonucu, gercek: KenarSonucu, tol: float = 25) -> dict:
    eslesme = parcalari_eslestir(bulunan, gercek, tol)
    b_tur = {p.id: p.tur for p in _parcalar(bulunan)}
    g_tur = {p.id: p.tur for p in _parcalar(gercek)}

    def kontur_karsiligi(kid):  # bulunan kenarın gerçek kenarı: parçalarının çoğunun eşleştiği
        sayac = Counter(eslesme[p.id].split(".")[0] for k in bulunan.kenarlar if k.id == kid
                        for p in k.parcalar if p.id in eslesme)
        return sayac.most_common(1)[0][0] if sayac else None

    bulunan_kontur = [kontur_karsiligi(k) for k in bulunan.kontur_sirasi]
    return {
        "bulunan": len(eslesme),
        "kaciran": len(_parcalar(gercek)) - len(eslesme),
        "fazla": len(_parcalar(bulunan)) - len(eslesme),
        "tur_dogru": sum(b_tur[b] == g_tur[g] for b, g in eslesme.items()),
        "kontur_dogru": bulunan_kontur == list(gercek.kontur_sirasi),
    }


def ciftleri_cevir(ciftler, eslesme: dict[str, str]) -> list[tuple[int, str]]:
    """Bulunan parça id'lerini gerçek id'ye çevirir; eşleşmeyenler "F:<id>" (hiç doğru sayılmaz)."""
    return [(d, eslesme.get(pid, f"F:{pid}") if pid else "F:yok") for d, pid in ciftler]


def _kenar(pid):
    return pid.split(".")[0]


def _kenar_duzeyine(sayac):
    sonuc = Counter()
    for (d, p), n in sayac.items():
        sonuc[(d, _kenar(p))] += n
    return sonuc


def eslestirme_puani(tahmin, gercek, kenar_duzeyi: bool = False, haric=()) -> int:
    """(değer, parça) çiftlerinin çoklu küme kesişimi. haric çiftler iki taraftan da bir kez çıkarılır."""
    t, g, h = Counter(tahmin), Counter(gercek), Counter(haric)
    t, g = t - h, g - h
    if kenar_duzeyi:
        t = _kenar_duzeyine(t)
        g = _kenar_duzeyine(g)
    return sum((t & g).values())


def _ortusme(kutu, bolge):
    x1, y1, x2, y2 = kutu
    bx1, by1, bx2, by2 = bolge
    g = max(0.0, min(x2, bx2) - max(x1, bx1))
    y = max(0.0, min(y2, by2) - max(y1, by1))
    return g * y / ((x2 - x1) * (y2 - y1))


def bolge_puani(bolgeler, gercek_kutular) -> dict:
    bulunan = sum(any(_ortusme(k, b.kutu) >= 0.5 for b in bolgeler) for k in gercek_kutular)
    yazi_olmayan = sum(all(_ortusme(b.kutu, k) == 0 for k in gercek_kutular) for b in bolgeler)
    bolunmus = sum(sum(_ortusme(k, b.kutu) >= 0.2 for b in bolgeler) >= 2 for k in gercek_kutular)
    birlesmis = sum(sum(_ortusme(k, b.kutu) >= 0.5 for k in gercek_kutular) >= 2 for b in bolgeler)
    return {"bulunan": bulunan, "yazi_olmayan": yazi_olmayan, "bolunmus": bolunmus, "birlesmis": birlesmis}
