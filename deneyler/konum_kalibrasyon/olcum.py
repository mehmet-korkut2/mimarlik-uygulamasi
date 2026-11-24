"""Ö1: Qwen3-VL sayı kutularında sistematik kayma var mı? (deneyler/sekil_01/RAPOR.md)

Kayıtlı Qwen-1 cevapları (Qwen çağrılmaz): konum deneyi (ham fotoğraf, 3 çalıştırma), ürün koşulu (çizgisi silinmiş
fotoğraf, 3 çalıştırma), iskeletin kayıtları (output/, varsa). Kutular `okuma.sayilari_ayristir` ile (0–1000 oran
varsayımı) piksele çevrilir, aynı değerli gerçek kutuyla eşlenir (Macar algoritması, merkez uzaklığı).
Uzaklığı 6 h'den büyük çiftler (modelin yanlış yere koyduğu sayılar) uyumdan çıkarılır.
Her eksen için: oran medyanı (qwen / gerçek) ve en küçük kareler doğrusu qwen = a · gerçek + b.

Çalıştırma (repo kökünden): PYTHONIOENCODING=utf-8 .venv/Scripts/python deneyler/konum_kalibrasyon/olcum.py
"""

import json
import statistics
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

KLASOR = Path(__file__).resolve().parent
REPO = KLASOR.parents[1]
sys.path.insert(0, str(REPO / "deneyler" / "bul_kes_okut"))
sys.path.insert(0, str(REPO))
from konumlar import GERCEK  # noqa: E402

from mimarlik.okuma import sayilari_ayristir  # noqa: E402

GEN, YUK, H = 1152, 2048, 37.0
ADLAR = {"01": "01_kolay_tek_oda_180x140", "02": "02_kolay_tek_oda_300x240"}


def kaynaklar():
    for ad, yol in [("konum (ham foto)", "deneyler/konum_deneyi/sonuclar/qwen_konum.json"),
                    ("ürün (çizgisiz)", "deneyler/cizgi_silme/sonuclar/qwen_urun.json")]:
        d = json.loads((REPO / yol).read_text(encoding="utf-8"))
        for kod, k in d["krokiler"].items():
            for n, c in enumerate(k["calistirmalar"], 1):
                yield ad, kod, n, c["ham"]
    for kod, a in ADLAR.items():
        yol = REPO / "output" / f"{a}_qwen.json"
        if yol.exists():
            yield "iskelet kaydı", kod, 1, json.loads(yol.read_text(encoding="utf-8"))["ham"]["sayilar"]


def merkez(k):
    return ((k[0] + k[2]) / 2, (k[1] + k[3]) / 2)


def ciftler(kod, ham):
    q = sayilari_ayristir(ham, GEN, YUK)
    g = GERCEK[kod]
    maliyet = np.full((len(q), len(g)), 1e9)
    for i, (d, k) in enumerate(q):
        for j, (_, gd, gk) in enumerate(g):
            if d == gd:
                maliyet[i, j] = np.hypot(*np.subtract(merkez(k), merkez(gk)))
    sonuc = []
    for i, j in zip(*linear_sum_assignment(maliyet)):
        if maliyet[i, j] < 6 * H:
            sonuc.append((merkez(g[j][2]), merkez(q[i][1])))
    return sonuc


def uyum(gercek, qwen):
    a, b = np.polyfit(gercek, qwen, 1)
    return round(float(a), 3), round(float(b), 1)


def main():
    tum = {"x": {"g": [], "q": []}, "y": {"g": [], "q": []}}
    satirlar = []
    for kaynak, kod, n, ham in kaynaklar():
        c = ciftler(kod, ham)
        gx, gy = [p[0][0] for p in c], [p[0][1] for p in c]
        qx, qy = [p[1][0] for p in c], [p[1][1] for p in c]
        tum["x"]["g"] += gx; tum["x"]["q"] += qx; tum["y"]["g"] += gy; tum["y"]["q"] += qy
        s = {"kaynak": kaynak, "kroki": kod, "calistirma": n, "cift": len(c),
             "x_oran_medyan": round(statistics.median(q / g for q, g in zip(qx, gx)), 3),
             "y_oran_medyan": round(statistics.median(q / g for q, g in zip(qy, gy)), 3),
             "x_uyum_a_b": uyum(gx, qx), "y_uyum_a_b": uyum(gy, qy)}
        satirlar.append(s)
        print(f"{kaynak:<16} {kod} #{n}  çift {len(c):>2}  x oran {s['x_oran_medyan']:.3f}  y oran "
              f"{s['y_oran_medyan']:.3f}  x: a={s['x_uyum_a_b'][0]:.3f} b={s['x_uyum_a_b'][1]:>6.1f}  "
              f"y: a={s['y_uyum_a_b'][0]:.3f} b={s['y_uyum_a_b'][1]:>6.1f}")
    toplam = {e: uyum(tum[e]["g"], tum[e]["q"]) for e in ("x", "y")}
    oran = {e: round(statistics.median(q / g for q, g in zip(tum[e]["q"], tum[e]["g"])), 3) for e in ("x", "y")}
    print(f"\nHepsi ({len(tum['x']['g'])} çift): x oran {oran['x']}  uyum {toplam['x']} · y oran {oran['y']}  uyum {toplam['y']}")
    (KLASOR / "sonuclar").mkdir(exist_ok=True)
    (KLASOR / "sonuclar" / "olcum.json").write_text(
        json.dumps({"calistirmalar": satirlar, "hepsi": {"oran": oran, "uyum_a_b": toplam}}, ensure_ascii=False,
                   indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
