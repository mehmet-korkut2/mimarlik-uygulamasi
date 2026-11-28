"""Döndürerek okuma puanı (sonuclar/dondurme_03_07.json × dogru_cevaplar_03_07.py). Model çağırmaz.

    PYTHONIOENCODING=utf-8 .venv/Scripts/python deneyler/konum_florence/puanla_dondurme.py

Eşleştirme `puanla_03_07.py` ile aynı (çoklu küme, "?" puana girmez). Sütunlar:
- 0° / 90° / 180° / 270°: tek açının okuması.
- birleşik: her değer için açılar arasındaki en büyük adet (aynı sayıyı iki açıda okumak iki kez sayılmaz;
  konum yok, bu yüzden aynı değerli iki farklı sayı da tek açıda okunmadıkça bir sayılır: temkinli).
- 2+ açı: yalnız en az iki açıda okunan değerler (çoğunluk yerine "ikinci görüş"; fazlayı azaltır mı?).
"""

import json
import sys
from collections import Counter

from puanla_03_07 import GERCEK, KLASOR, eslestir, ogeler, sayilar, virgul_kaybi

KAYIT = KLASOR / "sonuclar" / "dondurme_03_07.json"
ACILAR = ["0", "90", "180", "270"]


def birlesik(okumalar):
    toplam = Counter()
    for c in okumalar:
        toplam |= Counter(c)
    return list(toplam.elements())


def iki_aci(okumalar):
    """En az iki açıda okunan değerler; adet: o değeri okuyan açıların ikinci en büyük adedi."""
    sayac = [Counter(c) for c in okumalar]
    out = Counter()
    for d in set().union(*sayac):
        adet = sorted((c[d] for c in sayac), reverse=True)
        if adet[1]:
            out[d] = adet[1]
    return list(out.elements())


def main():
    kayit = json.loads(KAYIT.read_text(encoding="utf-8"))
    cevap = {}
    for kod in GERCEK:
        ac = [[s for m in kayit[kod][a]["metinler"] for s in sayilar(m)] for a in ACILAR]
        cevap[kod] = dict(zip(ACILAR, ac)) | {"birleşik": birlesik(ac), "2+ açı": iki_aci(ac)}
    sutunlar = [*ACILAR, "birleşik", "2+ açı"]
    puanli = {kod: [o for o in ogeler(kod) if o["emin"]] for kod in GERCEK}
    kategoriler = ["hepsi"] + sorted({e for v in puanli.values() for o in v for e in o["etiketler"]})

    say = {s: Counter() for s in sutunlar}
    fazla = Counter()
    for s in sutunlar:
        for kod in GERCEK:
            okundu, _, art = eslestir(kod, cevap[kod][s])
            fazla[s] += sum(art.values())
            for o in puanli[kod]:
                for e in ["hepsi", *o["etiketler"]]:
                    say[s][(e, "top")] += 1
                    say[s][(e, "dogru")] += okundu[o["i"]]

    rapor = {"kategori": {}, "fazla": dict(fazla)}
    print(f"{'kategori':<28} {'n':>4}  " + "  ".join(f"{s:>9}" for s in sutunlar))
    for e in kategoriler:
        n = say["0"][(e, "top")]
        d = [say[s][(e, "dogru")] for s in sutunlar]
        print(f"{e:<28} {n:>4}  " + "  ".join(f"{x:>3} ({x / n:3.0%})" for x in d))
        rapor["kategori"][e] = {"n": n, **dict(zip(sutunlar, d))}
    print(f"{'fazla (listede yok)':<28} {'':>4}  " + "  ".join(f"{fazla[s]:>9}" for s in sutunlar))

    # Hangi açı hangi yazılışı okuyor: yan sayılar 90 mı 270 mi istiyor (yazana göre değişir)
    print("\nYan / ters sayılar: okuyan açılar (puanlı)")
    rapor["yan_ters"] = []
    for kod in GERCEK:
        for o in puanli[kod]:
            if o["yazilis"] not in ("yan", "ters", "capraz"):
                continue
            okuyan = [a for a in ACILAR if eslestir(kod, cevap[kod][a])[0][o["i"]]]
            rapor["yan_ters"].append({"kroki": kod, "deger": o["deger"], "yazilis": o["yazilis"], "acilar": okuyan})
    for yaz in ("yan", "ters", "capraz"):
        sat = [r for r in rapor["yan_ters"] if r["yazilis"] == yaz]
        c = Counter(a for r in sat for a in r["acilar"])
        hic = sum(not r["acilar"] for r in sat)
        print(f"  {yaz:<7} n={len(sat):>3}  " + "  ".join(f"{a}°: {c[a]:>2}" for a in ACILAR)
              + f"  hiçbiri: {hic}")

    print("\nVirgül kaybı (birleşik):", [f"{k}:{v}" for k in GERCEK for v in virgul_kaybi(k, cevap[k]["birleşik"])])

    print("\n07: 7'si '>' gibi yazılmış (birleşik):")
    for o in ogeler("07"):
        if "'>'" in o["not"]:
            ok, soru, _ = eslestir("07", cevap["07"]["birleşik"])
            print(f"  {o['deger']:<5} {'evet' if o['emin'] else '?':<5} "
                  f"{('✓' if ok[o['i']] else '✗') if o['emin'] else (soru[o['i']] or '—')}")

    print("\n\"?\" sayılar (birleşik): okunan aday")
    rapor["soru"] = []
    for kod in GERCEK:
        _, soru, _ = eslestir(kod, cevap[kod]["birleşik"])
        for o in ogeler(kod):
            if not o["emin"]:
                print(f"  {kod} {o['deger']:<6} alt={'/'.join(o['alt']) or '-':<13} → {soru[o['i']] or '—'}")
                rapor["soru"].append({"kroki": kod, "taslak": o["deger"], "alt": o["alt"], "okunan": soru[o["i"]]})

    print("\nFazla (birleşik), kroki başına:")
    for kod in GERCEK:
        art = eslestir(kod, cevap[kod]["birleşik"])[2]
        print(f"  {kod}: {sum(art.values())}  " + " ".join(sorted(art.elements()))[:300])
    sure = {kod: {a: kayit[kod][a]["sure_s"] for a in ACILAR} for kod in GERCEK}
    print("\nSüre (s):", sure)
    rapor["sure_s"] = sure
    (KLASOR / "sonuclar" / "puan_dondurme.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=1),
                                                            encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
