"""sonuclar/*.json -> RAPOR.md içindeki ölçüm tabloları (sonuç bölümü elle yazılır).

Çalıştırma: deneyler/.venv/Scripts/python deneyler/ocr_karsilastirma/rapor.py
"""

import json
from collections import Counter
from pathlib import Path
from statistics import mean

from dogru_cevaplar import BELIRSIZ, DOGRU
from puanlama import puanla

KLASOR = Path(__file__).resolve().parent
# Gemini 3.8 Flash ücretli katman fiyatı (USD / 1M token, 31.12.2026'ya kadar); düşünme token'ları çıktıya dahil.
GEMINI_GIRDI, GEMINI_CIKTI = 0.75, 3.75


def _sonuclari_oku():
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((KLASOR / "sonuclar").glob("*.json"))]


def _ad(s):
    return f"{s['yontem']} ({s.get('model', s.get('surum', ''))})"


def ozet_tablosu(sonuclar):
    satirlar = ["| Yöntem | Kroki | Çalıştırma | Doğru | Fazla/uydurma | Kaçırılan | Süre (s, ort.) |",
                "|---|---|---|---|---|---|---|"]
    for s in sonuclar:
        for kod, k in s["krokiler"].items():
            puanlar = [puanla(c["sayilar"], DOGRU[kod]) for c in k["calistirmalar"]]
            n = len(puanlar)

            def alan(a):
                degerler = [p[a] for p in puanlar]
                return str(degerler[0]) if n == 1 else f"{mean(degerler):.1f} ({'/'.join(map(str, degerler))})"

            sure = mean(c["sure_s"] for c in k["calistirmalar"])
            satirlar.append(f"| {_ad(s)} | {kod} ({len(DOGRU[kod])} sayı) | {n} | {alan('dogru')} | "
                            f"{alan('fazla')} | {alan('kacirilan')} | {sure:.1f} |")
    return "\n".join(satirlar)


def ayrinti_tablosu(sonuclar):
    satirlar = ["| Yöntem | Kroki | # | Okunan | Fazla değerler | Kaçırılan değerler |",
                "|---|---|---|---|---|---|"]
    for s in sonuclar:
        for kod, k in s["krokiler"].items():
            for i, c in enumerate(k["calistirmalar"], 1):
                p = puanla(c["sayilar"], DOGRU[kod])
                satirlar.append(f"| {_ad(s)} | {kod} | {i} | {c['sayilar']} | {p['fazla_degerler']} | "
                                f"{p['kacirilan_degerler']} |")
    return "\n".join(satirlar)


def belirsiz_tablosu(sonuclar):
    satirlar = ["| Yöntem | # | " + " | ".join(str(b) for b in BELIRSIZ["01"]) + " |",
                "|---|---|" + "---|" * len(BELIRSIZ["01"])]
    for s in sonuclar:
        for i, c in enumerate(s["krokiler"]["01"]["calistirmalar"], 1):
            okunan = Counter(c["sayilar"])
            hucre = ["okundu" if okunan[b] else "—" for b in BELIRSIZ["01"]]
            satirlar.append(f"| {_ad(s)} | {i} | " + " | ".join(hucre) + " |")
    return "\n".join(satirlar)


def tutarlilik_tablosu(sonuclar):
    satirlar = ["| Yöntem | Kroki | 3 çalıştırma birebir aynı mı? | Farklı çıkan değerler |", "|---|---|---|---|"]
    for s in sonuclar:
        for kod, k in s["krokiler"].items():
            kumeler = [Counter(c["sayilar"]) for c in k["calistirmalar"]]
            if len(kumeler) < 2:
                continue
            ortak = kumeler[0]
            for c in kumeler[1:]:
                ortak = ortak & c
            fark = sorted({v for c in kumeler for v in (c - ortak).elements()})
            ayni = all(c == kumeler[0] for c in kumeler)
            satirlar.append(f"| {_ad(s)} | {kod} | {'evet' if ayni else 'hayır'} | {fark or '—'} |")
    return "\n".join(satirlar)


def maliyet_satirlari(sonuclar):
    satirlar = []
    for s in sonuclar:
        if s["yontem"] != "Gemini":
            continue
        cagrilar = [c["token"] for k in s["krokiler"].values() for c in k["calistirmalar"]]
        girdi = mean(t["girdi"] or 0 for t in cagrilar)
        cikti = mean((t["cikti"] or 0) + (t["dusunme"] or 0) for t in cagrilar)
        usd = girdi / 1e6 * GEMINI_GIRDI + cikti / 1e6 * GEMINI_CIKTI
        satirlar.append(f"- Gemini, kroki başına ortalama {girdi:.0f} girdi + {cikti:.0f} çıktı/düşünme token'ı. "
                        f"Ücretsiz katmanda **0 $**; ücretli katmanda olsaydı ≈ **{usd * 100:.2f} sent** / kroki "
                        f"(1.000 kroki ≈ {usd * 1000:.2f} $).")
    return "\n".join(satirlar)


def main():
    sonuclar = _sonuclari_oku()
    bolumler = [
        "<!-- Bu bölüm rapor.py ile üretilir; elle düzenleme. -->",
        "## Ölçümler\n\nDoğru/fazla/kaçırılan çoklu küme olarak sayılır (bkz. puanlama.py). "
        "Birden fazla çalıştırmada ortalama ve parantez içinde tek tek değerler.\n\n" + ozet_tablosu(sonuclar),
        "## 01'in belirsiz sayıları (15, 90, 10)\n\n" + belirsiz_tablosu(sonuclar),
        "## Tutarlılık\n\n" + tutarlilik_tablosu(sonuclar),
        "## Maliyet\n\n- EasyOCR ve Qwen3-VL: yerel, **0 $** (elektrik hariç).\n" + maliyet_satirlari(sonuclar),
        "## Ayrıntı: her çalıştırmada okunan sayılar\n\n" + ayrinti_tablosu(sonuclar),
    ]
    (KLASOR / "olcumler.md").write_text("\n\n".join(bolumler) + "\n", encoding="utf-8")
    print("Yazıldı: olcumler.md")


if __name__ == "__main__":
    main()
