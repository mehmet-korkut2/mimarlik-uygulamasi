"""03–07 okuma puanı: kayıtlı cevaplar (sonuclar/okuma_03_07.json) × doğru cevap listesi (dogru_cevaplar_03_07.py).

Model çağırmaz; liste düzelince yalnız bunu yeniden çalıştırın:
    PYTHONIOENCODING=utf-8 .venv/Scripts/python deneyler/konum_florence/puanla_03_07.py

Yöntem (yalnız okuma; 03–07'de gerçek kutu yok, konum ölçülmez):
- Her cevaptan sayılar çıkarılır: "\\d+([.,]\\d+)?", nokta virgüle çevrilir ("25.5" = "25,5"); "H=248" → 248,
  "45 45" → iki sayı. Virgül kaybı ("1645" ya da "164" ↔ "164,5") yanlış sayılır, ayrıca gösterilir.
- Çoklu küme eşleşmesi: kâğıtta 160 dört kez yazıyorsa cevapta dört 160 gerekir. Önce "?" olmayan sayılar
  (puan), sonra kalan cevaplar "?" sayılarına (taslak ya da nottaki alternatif) bakılır; artakalan = fazla.
- "?" sayılar puana girmez (kullanıcı kararı 2026-11-28); ayrı tabloda.
- Uyuşma: Florence ile Qwen'in n. çağrısının ortak sayıları (çoklu küme kesişimi). Konum olmadığı için "aynı yerde"
  değil, "ikisi de bu değeri okudu" demek. Ortak sayı listede yoksa = ikisinin ortak hatası.
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

KLASOR = Path(__file__).resolve().parent
sys.path.insert(0, str(KLASOR))
from dogru_cevaplar_03_07 import GERCEK  # noqa: E402

KAYIT = KLASOR / "sonuclar" / "okuma_03_07.json"
SAYI = re.compile(r"\d+(?:[.,]\d+)?")
# Yükseklik öneki (h1:, h2., h11., H=, K.H=): öneki sayıya karışmasın ("h1.217" → 217, "1,217" değil)
ONEK = re.compile(r"[hH]\s*\d{0,2}\s*[.:=]\s*")
NOKTALI, CIZGILI = ("04", "05", "06"), ("03", "07")


def sayilar(metin):
    out = []
    for s in SAYI.findall(ONEK.sub(" ", str(metin))):
        s = s.replace(".", ",")
        tam = s.split(",")[0]
        if 1 <= int(tam) <= 9999 and not (s.startswith("0") and "," not in s):
            out.append(s)
    return out


def kayit_sayilari(kayit, model):
    """{kod: [çalıştırma başına sayı listesi]}"""
    sonuc = {}
    for kod, calismalar in kayit.get(model, {}).items():
        for c in calismalar:
            metinler = c["metinler"] if model == "florence" else c["etiketler"]
            sonuc.setdefault(kod, []).append([s for m in metinler for s in sayilar(m)])
    return sonuc


def ogeler(kod):
    """Her öğe: dict(deger, tur, yazilis, emin, not, alt: alternatifler, etiketler: kategori kümesi)."""
    k = GERCEK[kod]
    sonuc = []
    for i, (d, tur, yaz, emin, notu) in enumerate(k["sayilar"]):
        et = {f"tür: {tur}", f"yazılış: {yaz}", f"kroki {kod}",
              "kâğıt: noktalı" if kod in NOKTALI else "kâğıt: çizgili"}
        if "," in d:
            et.add("virgüllü")
        if "'>'" in notu:
            et.add("7 '>' gibi (07)")
        if "yakın" in notu or "sıkışık" in notu:
            et.add("yakın / sıkışık sayılar")
        if kod == "07":
            et.add("renk: mavi (07)" if "MAVİ" in notu else "renk: kırmızı (07)")
        alt = [s for s in sayilar(notu) if s != d] if not emin else []
        sonuc.append({"i": i, "deger": d, "tur": tur, "yazilis": yaz, "emin": emin, "not": notu, "alt": alt,
                      "etiketler": et})
    return sonuc


def eslestir(kod, cevap):
    """cevap: sayı listesi -> (puanlı öğe i -> okundu mu, "?" öğe i -> okunan aday ya da None, fazla Counter)."""
    kalan = Counter(cevap)
    okundu, soru = {}, {}
    for o in ogeler(kod):
        if o["emin"]:
            okundu[o["i"]] = kalan[o["deger"]] > 0
            if okundu[o["i"]]:
                kalan[o["deger"]] -= 1
    for o in ogeler(kod):
        if not o["emin"]:
            aday = next((a for a in [o["deger"], *o["alt"]] if a != "?" and kalan[a] > 0), None)
            soru[o["i"]] = aday
            if aday:
                kalan[aday] -= 1
    return okundu, soru, +kalan


def virgul_kaybi(kod, cevap):
    """Virgüllü doğru sayı okunmadı ama virgülsüz hali ("1645") ya da tam kısmı ("164") cevapta var."""
    okundu, _, _ = eslestir(kod, cevap)
    c = Counter(cevap)
    kayip = []
    for o in ogeler(kod):
        if o["emin"] and "," in o["deger"] and not okundu[o["i"]]:
            bitisik, tam = o["deger"].replace(",", ""), o["deger"].split(",")[0]
            if c[bitisik] or c[tam]:
                kayip.append(f'{o["deger"]}→{bitisik if c[bitisik] else tam}')
    return kayip


def main():
    kayit = json.loads(KAYIT.read_text(encoding="utf-8"))
    modeller = {"Florence-2": kayit_sayilari(kayit, "florence"), "Qwen3-VL": kayit_sayilari(kayit, "qwen")}
    puanli = {kod: [o for o in ogeler(kod) if o["emin"]] for kod in GERCEK}
    toplam = sum(len(v) for v in puanli.values())
    rapor = {"toplam_puanli": toplam}

    # 1. Kategori tablosu: her model, her çalıştırma -> kategori başına doğru / toplam
    kategoriler = sorted({e for v in puanli.values() for o in v for e in o["etiketler"]})
    kategoriler = ["hepsi"] + kategoriler
    tablo = {}
    for ad, krokiler in modeller.items():
        n_cal = min(len(v) for v in krokiler.values())
        for n in range(n_cal):
            say = Counter()
            fazla = 0
            for kod in GERCEK:
                okundu, _, art = eslestir(kod, krokiler[kod][n])
                fazla += sum(art.values())
                for o in puanli[kod]:
                    for e in ["hepsi", *o["etiketler"]]:
                        say[(e, "top")] += 1
                        say[(e, "dogru")] += okundu[o["i"]]
            tablo.setdefault(ad, []).append((say, fazla))
    print(f"Puanlı sayı: {toplam} (\"?\" olanlar hariç)\n")
    baslik = f"{'kategori':<28} {'n':>4}  {'Florence-2':>10}  {'Qwen #1':>8} {'Qwen #2':>8} {'Qwen #3':>8}  {'Qwen ort.':>9}"
    print(baslik)
    rapor["kategori"] = {}
    for e in kategoriler:
        n = tablo["Florence-2"][0][0][(e, "top")]
        if not n:
            continue
        f = tablo["Florence-2"][0][0][(e, "dogru")]
        q = [s[(e, "dogru")] for s, _ in tablo["Qwen3-VL"]]
        print(f"{e:<28} {n:>4}  {f:>4} ({f / n:4.0%})  " + " ".join(f"{x:>8}" for x in q)
              + f"  {sum(q) / len(q) / n:>8.0%}")
        rapor["kategori"][e] = {"n": n, "florence": f, "qwen": q}
    fz = tablo["Florence-2"][0][1]
    qz = [z for _, z in tablo["Qwen3-VL"]]
    print(f"{'fazla (listede yok)':<28} {'':>4}  {fz:>10}  " + " ".join(f"{x:>8}" for x in qz))
    rapor["fazla"] = {"florence": fz, "qwen": qz}

    # 2. Virgül kaybı
    print("\nVirgül kaybı (virgüllü sayı virgülsüz ya da tam kısmıyla okunmuş):")
    rapor["virgul_kaybi"] = {}
    for ad, krokiler in modeller.items():
        for n, _ in enumerate(krokiler["03"]):
            kayip = [f"{kod}:{k}" for kod in GERCEK for k in virgul_kaybi(kod, krokiler[kod][n])]
            print(f"  {ad} #{n + 1}: {len(kayip)}  {', '.join(kayip)}")
            rapor["virgul_kaybi"][f"{ad} #{n + 1}"] = kayip

    # 3. 07'de '>' gibi yazılmış 7'ler (puanlı ve "?" hepsi)
    print("\n07: 7'si '>' gibi yazılmış sayılar")
    print(f"  {'sayı':<8} {'emin':<5} {'Florence':<10} {'Qwen #1/#2/#3':<16} not")
    rapor["yedi"] = []
    for o in ogeler("07"):
        if "'>'" not in o["not"]:
            continue
        satir = {"deger": o["deger"], "emin": o["emin"]}
        def okunan(cevap):
            ok, soru, _ = eslestir("07", cevap)
            if o["emin"]:
                return "✓" if ok[o["i"]] else "✗"
            return soru[o["i"]] or "—"
        satir["florence"] = okunan(modeller["Florence-2"]["07"][0])
        satir["qwen"] = [okunan(c) for c in modeller["Qwen3-VL"]["07"]]
        rapor["yedi"].append(satir)
        print(f"  {o['deger']:<8} {'evet' if o['emin'] else '?':<5} {satir['florence']:<10} "
              f"{'/'.join(satir['qwen']):<16} {o['not']}")
    print("  (✓/✗: puanlı sayı okundu mu; \"?\" sayılarda okunan aday ya da —)")

    # 4. "?" sayılar: her model hangi adayı okudu, uyuşuyorlar mı
    print("\n\"?\" sayılar (puana girmez): okunan aday (taslak ya da nottaki alternatif), — = hiçbiri")
    print(f"  {'kroki':<5} {'taslak':<7} {'alternatif':<14} {'Florence':<9} {'Qwen #1/#2/#3':<20} uyuşma")
    rapor["soru"] = []
    for kod in GERCEK:
        for o in ogeler(kod):
            if o["emin"]:
                continue
            f = eslestir(kod, modeller["Florence-2"][kod][0])[1][o["i"]]
            q = [eslestir(kod, c)[1][o["i"]] for c in modeller["Qwen3-VL"][kod]]
            uy = [bool(f) and f == x for x in q]
            durum = f"{sum(uy)}/3 aynı" if f else "Florence okumadı"
            print(f"  {kod:<5} {o['deger']:<7} {'/'.join(o['alt']) or '-':<14} {f or '—':<9} "
                  f"{'/'.join(x or '—' for x in q):<20} {durum}")
            rapor["soru"].append({"kroki": kod, "taslak": o["deger"], "alt": o["alt"], "florence": f, "qwen": q,
                                  "not": o["not"]})

    # 5. Florence ∩ Qwen: ortak okunan sayılarda hata var mı?
    print("\nFlorence ∩ Qwen (ikisinin de okuduğu değerler, çoklu küme kesişimi):")
    print(f"  {'Qwen':<6} {'ortak':>6} {'listede doğru':>14} {'\"?\" adayı':>10} {'ortak hata':>11}  hatalar")
    rapor["uyusma"] = []
    for n, _ in enumerate(modeller["Qwen3-VL"]["03"]):
        top = Counter()
        hatalar = []
        for kod in GERCEK:
            ortak = Counter(modeller["Florence-2"][kod][0]) & Counter(modeller["Qwen3-VL"][kod][n])
            liste = Counter(o["deger"] for o in ogeler(kod) if o["emin"])
            soru = Counter(a for o in ogeler(kod) if not o["emin"] for a in [o["deger"], *o["alt"]] if a != "?")
            for d, c in ortak.items():
                dogru = min(c, liste[d])
                aday = min(c - dogru, soru[d])
                hata = c - dogru - aday
                top["ortak"] += c
                top["dogru"] += dogru
                top["aday"] += aday
                top["hata"] += hata
                hatalar += [f"{kod}:{d}"] * hata
        print(f"  #{n + 1:<5} {top['ortak']:>6} {top['dogru']:>14} {top['aday']:>10} {top['hata']:>11}  {', '.join(hatalar)}")
        rapor["uyusma"].append({**top, "hatalar": hatalar})
    # Yalnız birinin okuduğu: karşılaştırma için Florence'ın ve Qwen'in tek başına hatası
    print("\nTek başına hata (listede de \"?\" adaylarında da olmayan okumalar = fazla):")
    for ad, krokiler in modeller.items():
        for n, _ in enumerate(krokiler["03"]):
            f = {kod: sorted(eslestir(kod, krokiler[kod][n])[2].elements()) for kod in GERCEK}
            print(f"  {ad} #{n + 1}: " + "; ".join(f"{k}: {' '.join(v)}" for k, v in f.items() if v))
    sure = {ad: [c["sure_s"] for k in kayit[m].values() for c in k] for ad, m in (("Florence-2", "florence"),
                                                                                 ("Qwen3-VL", "qwen"))}
    print("\nSüre (s):", {k: v for k, v in sure.items()})
    rapor["sure_s"] = sure
    (KLASOR / "sonuclar" / "puan_03_07.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=1),
                                                          encoding="utf-8")


if __name__ == "__main__":
    main()
