"""Ö2: değer atamayı yerel ve sınırlı yapmanın etkisi (deneyler/sekil_01/RAPOR.md, H1).

Kayıtlı Qwen-1 cevapları (Qwen çağrılmaz; konum deneyi 3 + ürün koşulu 3 + iskelet kaydı, 01 ve 02) ve
fotoğraftan bulunan sayı bölgeleri (kenar bulma 1. geçiş). Her (değer, bölge) ataması gerçeğe göre:
  doğru  : bölge, aynı değerli gerçek sayının kutusuyla örtüşüyor,
  yanlış : başka bir bölgeye,
  yok    : "yeri bulunamadı" (Y2'ye / kullanıcıya kalır).
Kurallar: eski (Ö2'den önce: merkez uzaklığı ≤ köşegenin %20'si) ve sınırlı (Qwen kutusu ile bölge kutusu arası ≤ k·h).
"Emin" adayı: atanan çiftin kutu–bölge uzaklığı ≤ e·h; isabeti (doğru / emin) ölçülür.

Çalıştırma (repo kökünden): PYTHONIOENCODING=utf-8 .venv/Scripts/python deneyler/deger_atama/olcum.py
"""

import json
import math
import sys
from pathlib import Path

import cv2

KLASOR = Path(__file__).resolve().parent
REPO = KLASOR.parents[1]
sys.path.insert(0, str(REPO / "deneyler" / "bul_kes_okut"))
sys.path.insert(0, str(REPO / "deneyler" / "konum_kalibrasyon"))
sys.path.insert(0, str(REPO))
from konumlar import GERCEK  # noqa: E402

import mimarlik.eslestirme as es  # noqa: E402
from mimarlik.bolge_bulma import bolgeleri_bul  # noqa: E402
from mimarlik.kenar_bulma import kenarlari_bul  # noqa: E402
from mimarlik.okuma import sayilari_ayristir  # noqa: E402
from mimarlik.on_isleme import karakter_yuksekligi, murekkep_maskesi  # noqa: E402
from olcum import ADLAR, kaynaklar  # noqa: E402  (konum_kalibrasyon: kayıtlı Qwen-1 cevapları)

SINIRLAR = [1, 1.5, 2, 3, 4, 6]       # k (h katı); ürün: 1 h (eslestirme.ATAMA_SINIRI)
EMIN = [0.5, 1, 1.5, 2]               # e (h katı)


def kutu_uzakligi(a, b):
    dx = max(a[0] - b[2], b[0] - a[2], 0)
    dy = max(a[1] - b[3], b[1] - a[3], 0)
    return math.hypot(dx, dy)


def ortusuyor(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def puanla(kod, atanmis, ogeler):
    """Döner: [(sonuç "dogru"|"yanlis", kutu–bölge uzaklığı / h)], yok sayısı."""
    return [("dogru" if any(d == gd and ortusuyor(b.kutu, gk) for _, gd, gk in GERCEK[kod]) else "yanlis", u)
            for b, d, u in atanmis]


def eski_ata(bolgeler, ogeler):
    """Ö2'den önceki kural (sabit): merkez uzaklığı ≤ köşegenin %20'si, hane cezası köşegenin %5'i / hane."""
    from scipy.optimize import linear_sum_assignment
    kosegen = math.hypot(2048, 1152)
    m = [[1e6] * len(ogeler) for _ in bolgeler]
    for i, b in enumerate(bolgeler):
        for j, (d, kutu) in enumerate(ogeler):
            u = math.dist(es._merkez(b.kutu), es._merkez(kutu)) / kosegen
            if u <= 0.2:
                m[i][j] = u + 0.05 * abs(es.hane_tahmini(b.kutu) - len(str(d)))
    return [(bolgeler[i], ogeler[j][0], kutu_uzakligi(bolgeler[i].kutu, ogeler[j][1]))
            for i, j in zip(*linear_sum_assignment(m)) if m[i][j] < 1e6]


def sinirli_ata(bolgeler, ogeler, h, k):
    from scipy.optimize import linear_sum_assignment
    if not bolgeler or not ogeler:
        return []
    m = [[1e6] * len(ogeler) for _ in bolgeler]
    for i, b in enumerate(bolgeler):
        for j, (d, kutu) in enumerate(ogeler):
            u = kutu_uzakligi(b.kutu, kutu) / h
            if u <= k:
                m[i][j] = u + 0.5 * abs(es.hane_tahmini(b.kutu) - len(str(d)))   # hane: ~0,5 h / hane
    return [(bolgeler[i], ogeler[j][0], kutu_uzakligi(bolgeler[i].kutu, ogeler[j][1]) / h)
            for i, j in zip(*linear_sum_assignment(m)) if m[i][j] < 1e6]


def main():
    bolgeler, hler = {}, {}
    for kod, ad in ADLAR.items():
        bgr = cv2.imread(str(REPO / "ornekler" / f"{ad}.jpg"))
        maske = murekkep_maskesi(bgr)
        h = karakter_yuksekligi(maske)
        bolgeler[kod], hler[kod] = bolgeleri_bul(maske, kenarlari_bul(maske, h), h), h
    toplam = {}
    for _, kod, _, ham in kaynaklar():
        ogeler = sayilari_ayristir(ham, 1152, 2048)
        h = hler[kod]
        kurallar = {"eski": [(b, d, u / h) for b, d, u in eski_ata(bolgeler[kod], ogeler)]}
        for k in SINIRLAR:
            kurallar[f"sınırlı {k} h"] = sinirli_ata(bolgeler[kod], ogeler, h, k)
        for ad, atanmis in kurallar.items():
            t = toplam.setdefault(ad, {"dogru": 0, "yanlis": 0, "yok": 0, "emin": {e: [0, 0] for e in EMIN}})
            p = puanla(kod, atanmis, ogeler)
            t["dogru"] += sum(s == "dogru" for s, _ in p)
            t["yanlis"] += sum(s == "yanlis" for s, _ in p)
            t["yok"] += len(ogeler) - len(p)
            for e in EMIN:
                yakin = [s for s, u in p if u <= e]
                t["emin"][e][0] += sum(s == "dogru" for s in yakin)
                t["emin"][e][1] += len(yakin)
    print(f"{'kural':<14} {'doğru':>6} {'yanlış':>7} {'yok':>5}   emin isabeti (kutu–bölge ≤ e·h)")
    for ad, t in toplam.items():
        emin = "  ".join(f"{e}h: {d}/{n}" for e, (d, n) in t["emin"].items())
        print(f"{ad:<14} {t['dogru']:>6} {t['yanlis']:>7} {t['yok']:>5}   {emin}")
    (KLASOR / "sonuclar").mkdir(exist_ok=True)
    (KLASOR / "sonuclar" / "olcum.json").write_text(
        json.dumps({a: {**t, "emin": {str(e): v for e, v in t["emin"].items()}} for a, t in toplam.items()},
                   ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
