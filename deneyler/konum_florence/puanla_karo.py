"""Karolama + döndürme puanı (sonuclar/karo_dondurme_03_07.json × dogru_cevaplar_03_07.py). Model çağırmaz.

    PYTHONIOENCODING=utf-8 .venv/Scripts/python deneyler/konum_florence/puanla_karo.py

Birleştirme (konumla; karolar ve açılar aynı sayıyı tekrar tekrar okur):
1. Süzme: 4'ten çok sayı içeren ya da aynı değeri 3+ kez tekrarlayan okuma = uydurma dizi, atılır.
2. Kümeleme: özgün koordinattaki kutular IoU ≥ 0,3 ya da birinin merkezi ötekinin içindeyse aynı yer.
3. Oylama: kümede en çok okunan sayı dizisi (eşitlikte daha çok sayılı olan) o yerin cevabı.
Puanlama `puanla_03_07.eslestir` ile aynı (çoklu küme, "?" puana girmez).

Sütunlar: karo 0° (yalnız karolama) / karo 4 açı, süzmesiz / karo 4 açı, süzmeli (asıl) / yalnız ≥ 2 oy alan yerler
(temkinli) / aday: kümede herhangi bir okuma doğruysa (düzeltme ekranında aday listesi olarak gösterilse üst sınır).
"""

import json
from collections import Counter

from puanla_03_07 import GERCEK, KLASOR, eslestir, ogeler, sayilar, virgul_kaybi

KAYIT = KLASOR / "sonuclar" / "karo_dondurme_03_07.json"
# Karşılaştırma için önceki satırlar (RAPOR_03_07.md bölüm 1 ve 7)
ONCEKI = {"tam 0°": 18, "tam 4 açı birleşik": 43}


def uydurma(ss):
    return len(ss) > 4 or (ss and Counter(ss).most_common(1)[0][1] >= 3)


def _iou(a, b):
    x0, y0, x1, y1 = max(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), min(a[3], b[3])
    ic = max(0, x1 - x0) * max(0, y1 - y0)
    alan = lambda k: max(1, (k[2] - k[0]) * (k[3] - k[1]))  # noqa: E731
    return ic / (alan(a) + alan(b) - ic)


def _icinde(a, b):
    cx, cy = (a[0] + a[2]) / 2, (a[1] + a[3]) / 2
    return b[0] <= cx <= b[2] and b[1] <= cy <= b[3]


def kumele(tespitler):
    """[(sayılar tuple, kutu, açı)] → küme listesi (her küme tespit listesi). Birleşim-bul."""
    ana = list(range(len(tespitler)))

    def bul(i):
        while ana[i] != i:
            ana[i] = ana[ana[i]]
            i = ana[i]
        return i
    for i, a in enumerate(tespitler):
        for j in range(i):
            b = tespitler[j]
            if _iou(a[1], b[1]) >= 0.3 or _icinde(a[1], b[1]) or _icinde(b[1], a[1]):
                ana[bul(i)] = bul(j)
    kumeler = {}
    for i, t in enumerate(tespitler):
        kumeler.setdefault(bul(i), []).append(t)
    return list(kumeler.values())


def oyla(kume):
    say = Counter(t[0] for t in kume)
    en = max(say.items(), key=lambda kv: (kv[1], len(kv[0])))
    return en[0], en[1]


def cevaplar(kayit_kod, acilar, suz):
    tes = []
    for t in kayit_kod["tespitler"]:
        if t["aci"] not in acilar:
            continue
        ss = sayilar(t["metin"])
        if not ss or (suz and uydurma(ss)):
            continue
        tes.append((tuple(ss), t["kutu"], t["aci"]))
    kumeler = kumele(tes)
    secim = [oyla(k) for k in kumeler]
    return {
        "liste": [s for d, _ in secim for s in d],
        "iki_oy": [s for d, n in secim if n >= 2 for s in d],
        "aday": [s for k in kumeler for d in {t[0] for t in k} for s in d],
        "yer": len(kumeler),
    }


def main():
    kayit = json.loads(KAYIT.read_text(encoding="utf-8"))
    hepsi = ["0", "90", "180", "270"]
    cv = {}
    for kod in GERCEK:
        k0 = cevaplar(kayit[kod], ["0"], True)
        ham = cevaplar(kayit[kod], hepsi, False)
        suz = cevaplar(kayit[kod], hepsi, True)
        cv[kod] = {"karo 0°": k0["liste"], "karo 4 açı ham": ham["liste"], "karo 4 açı süzmeli": suz["liste"],
                   "≥2 oy": suz["iki_oy"], "aday (üst sınır)": suz["aday"], "_yer": suz["yer"]}
    sutunlar = ["karo 0°", "karo 4 açı ham", "karo 4 açı süzmeli", "≥2 oy", "aday (üst sınır)"]
    puanli = {kod: [o for o in ogeler(kod) if o["emin"]] for kod in GERCEK}
    kategoriler = ["hepsi"] + sorted({e for v in puanli.values() for o in v for e in o["etiketler"]})
    say = {s: Counter() for s in sutunlar}
    fazla = Counter()
    for s in sutunlar:
        for kod in GERCEK:
            okundu, _, art = eslestir(kod, cv[kod][s])
            fazla[s] += sum(art.values())
            for o in puanli[kod]:
                for e in ["hepsi", *o["etiketler"]]:
                    say[s][(e, "top")] += 1
                    say[s][(e, "dogru")] += okundu[o["i"]]

    rapor = {"onceki": ONCEKI, "kategori": {}, "fazla": dict(fazla)}
    print("Önceki (tam görsel):", ONCEKI)
    print(f"{'kategori':<26} {'n':>4}  " + "  ".join(f"{s[:13]:>13}" for s in sutunlar))
    for e in kategoriler:
        n = say[sutunlar[0]][(e, "top")]
        d = [say[s][(e, "dogru")] for s in sutunlar]
        print(f"{e:<26} {n:>4}  " + "  ".join(f"{x:>6} ({x / n:4.0%})" for x in d))
        rapor["kategori"][e] = {"n": n, **dict(zip(sutunlar, d))}
    print(f"{'fazla (listede yok)':<26} {'':>4}  " + "  ".join(f"{fazla[s]:>13}" for s in sutunlar))
    print("yer (küme) sayısı, süzmeli:", {k: cv[k]["_yer"] for k in GERCEK})

    print("\nVirgül kaybı (süzmeli):",
          [f"{k}:{v}" for k in GERCEK for v in virgul_kaybi(k, cv[k]["karo 4 açı süzmeli"])])
    print("\n07: 7'si '>' gibi (süzmeli / aday):")
    for o in ogeler("07"):
        if "'>'" in o["not"]:
            r = []
            for s in ("karo 4 açı süzmeli", "aday (üst sınır)"):
                ok, soru, _ = eslestir("07", cv["07"][s])
                r.append(("✓" if ok[o["i"]] else "✗") if o["emin"] else (soru[o["i"]] or "—"))
            print(f"  {o['deger']:<5} {'evet' if o['emin'] else '?':<5} {' / '.join(r)}")
    print("\n\"?\" sayılar (süzmeli): okunan aday")
    rapor["soru"] = []
    for kod in GERCEK:
        _, soru, _ = eslestir(kod, cv[kod]["karo 4 açı süzmeli"])
        for o in ogeler(kod):
            if not o["emin"]:
                print(f"  {kod} {o['deger']:<6} alt={'/'.join(o['alt']) or '-':<13} → {soru[o['i']] or '—'}")
                rapor["soru"].append({"kroki": kod, "taslak": o["deger"], "alt": o["alt"], "okunan": soru[o["i"]]})
    print("\nFazla (süzmeli), kroki başına:")
    for kod in GERCEK:
        art = eslestir(kod, cv[kod]["karo 4 açı süzmeli"])[2]
        print(f"  {kod}: {sum(art.values())}  " + " ".join(sorted(art.elements()))[:250])
    print("\nSüre (s):", {k: kayit[k]["sure_s"] for k in GERCEK})
    rapor["sure_s"] = {k: kayit[k]["sure_s"] for k in GERCEK}
    (KLASOR / "sonuclar" / "puan_karo.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=1),
                                                        encoding="utf-8")


if __name__ == "__main__":
    main()
