"""Karolama + döndürme kayıtları üzerinde son denemeler (model çağırmaz). `RAPOR_03_07.md` bölüm 10.

    PYTHONIOENCODING=utf-8 .venv/Scripts/python deneyler/konum_florence/puanla_karo_son.py

1. Duyarlılık: yön ağırlıklı oylamanın iki katsayısı (dik okuma ağırlığı, 0° önceliği) birkaç değerde. Sonuç
   katsayıya çok bağlıysa 03–07'ye aşırı uyma riski büyük.
2. Süzme: tek haneli okumalar (çizgi parçaları) ve ASCII olmayan rakamlar (Florence'in Arap–Hint rakamları).
   Listede puanlı tek haneli sayı yok (yalnız 03 "5?"); gerçek krokide 5 gibi kısa ölçü yazılabilir → risk.
3. Seçmeli düzeltme benzetimi (ana ölçüt "kaç düzeltmede doğru plan" için kaba kestirim, konumsuz):
   her yer (küme) için adaylar yön ağırlıklı puana göre sıralanır; ekranda 1. aday çizilir.
   - 1. aday listede bir sayıysa: 0 düzeltme.
   - 1. aday "?" sayının adayıysa: sayılmaz (puan dışı).
   - değilse ve 2./3. adaylardan biri listede kalan bir sayıysa: 1 düzeltme (seçim);
     değilse: 1 düzeltme (sil).
   - hiçbir yerde bulunmayan listedeki sayı: 1 düzeltme (yaz).
   Kaba çünkü değerler konumsuz eşleşiyor (doğru değer yanlış yerde okunmuş olabilir) ve sayı–duvar bağlama
   düzeltmeleri dahil değil. "Hiç okuma yok" tabanı: 147 düzeltme (hepsini yazmak).
"""

import json
from collections import Counter, defaultdict

from puanla_03_07 import GERCEK, KLASOR, eslestir, ogeler, sayilar
from puanla_karo import KAYIT, kumele, uydurma
import puanla_karo_yon as yon


def tespitler(kayit_kod, tek_hane_suz):
    tes = []
    for t in kayit_kod["tespitler"]:
        ss = sayilar(t["metin"])
        if tek_hane_suz:
            ss = [s for s in ss if s.isascii() and len(s.split(",")[0]) > 1]
        if ss and not uydurma(ss):
            tes.append((tuple(ss), t["kutu"], t["aci"]))
    return tes


def sirali(kume, dik, sifir):
    puan = defaultdict(float)
    eski = yon.DIK_AGIRLIK, yon.SIFIR_ONCELIK
    yon.DIK_AGIRLIK, yon.SIFIR_ONCELIK = dik, sifir
    for ss, kutu, aci in kume:
        puan[ss] += yon.agirlik(ss, kutu, aci, True)
    yon.DIK_AGIRLIK, yon.SIFIR_ONCELIK = eski
    return [k for k, _ in sorted(puan.items(), key=lambda kv: (-kv[1], -len(kv[0])))]


def puanla(kumeler_kod, dik, sifir):
    """→ (doğru, fazla) toplam ve kategori sayacı."""
    say, fazla = Counter(), 0
    for kod, kumeler in kumeler_kod.items():
        liste = [s for k in kumeler for s in sirali(k, dik, sifir)[0]]
        okundu, _, art = eslestir(kod, liste)
        fazla += sum(art.values())
        for o in ogeler(kod):
            if o["emin"]:
                for e in ["hepsi", *o["etiketler"]]:
                    say[(e, "top")] += 1
                    say[(e, "dogru")] += okundu[o["i"]]
    return say, fazla


def duzeltme(kumeler_kod, dik, sifir):
    toplam = Counter()
    for kod, kumeler in kumeler_kod.items():
        kalan = Counter(o["deger"] for o in ogeler(kod) if o["emin"])
        soru = Counter(a for o in ogeler(kod) if not o["emin"] for a in [o["deger"], *o["alt"]] if a != "?")
        adaylar = [sirali(k, dik, sifir) for k in kumeler]
        yanlis = []
        for a in adaylar:          # 1. tur: ekranda çizilen 1. adaylar
            bir = Counter(a[0])
            if all(kalan[d] >= c for d, c in bir.items()):
                kalan -= bir
                toplam["dogru"] += sum(bir.values())
            elif all(soru[d] >= c for d, c in bir.items()):
                soru -= bir
            else:
                yanlis.append(a)
        for a in yanlis:           # 2. tur: yanlış yerlerde 2./3. aday seçimi ya da silme
            sec = next((x for x in a[1:3] if all(kalan[d] >= c for d, c in Counter(x).items())), None)
            if sec:
                kalan -= Counter(sec)
                toplam["secim"] += 1
                toplam["secimle_dogru"] += len(sec)
            else:
                toplam["sil"] += 1
        toplam["yaz"] += sum(kalan.values())
    toplam["duzeltme"] = toplam["secim"] + toplam["sil"] + toplam["yaz"]
    return toplam


def main():
    kayit = json.loads(KAYIT.read_text(encoding="utf-8"))
    rapor = {}
    kume = {s: {kod: kumele(tespitler(kayit[kod], s)) for kod in GERCEK} for s in (False, True)}

    print("1. Duyarlılık (süzmesiz tek hane): doğru / fazla")
    print(f"  {'dik \\ 0° önceliği':<20}" + "".join(f"{s:>12}" for s in (1.0, 1.5, 2.0, 3.0)))
    rapor["duyarlilik"] = {}
    for dik in (1.0, 0.5, 0.2, 0.0):
        hucre = []
        for sifir in (1.0, 1.5, 2.0, 3.0):
            say, fz = puanla(kume[False], dik, sifir)
            hucre.append(f"{say[('hepsi', 'dogru')]} / {fz}")
            rapor["duyarlilik"][f"{dik}|{sifir}"] = [say[("hepsi", "dogru")], fz]
        print(f"  {dik:<20}" + "".join(f"{h:>12}" for h in hucre))
    print("  (dik = 1, 0° önceliği = 1: düz çoğunluk oylaması, bölüm 8'deki 54 / 151 ile aynı olmalı)")

    print("\n2. Süzme (dik 0,2, 0° önceliği 1,5):")
    satirlar = {}
    for ad, s in (("tek hane süzmesiz", False), ("tek hane + ASCII dışı süzmeli", True)):
        say, fz = puanla(kume[s], 0.2, 1.5)
        satirlar[ad] = (say, fz)
        print(f"  {ad:<32} doğru {say[('hepsi', 'dogru')]:>3}/147   fazla {fz:>4}   yer "
              + str({k: len(v) for k, v in kume[s].items()}))
    kategoriler = ["hepsi"] + sorted({e for kod in GERCEK for o in ogeler(kod) if o["emin"] for e in o["etiketler"]})
    print(f"\n  {'kategori':<26} {'n':>4} {'süzmesiz':>9} {'süzmeli':>9}")
    rapor["suzme"] = {}
    for e in kategoriler:
        a, b = (satirlar[k][0] for k in satirlar)
        print(f"  {e:<26} {a[(e, 'top')]:>4} {a[(e, 'dogru')]:>9} {b[(e, 'dogru')]:>9}")
        rapor["suzme"][e] = {"n": a[(e, "top")], "suzmesiz": a[(e, "dogru")], "suzmeli": b[(e, "dogru")]}
    rapor["suzme_fazla"] = {k: v[1] for k, v in satirlar.items()}

    print("\n3. Seçmeli düzeltme benzetimi (kaba, konumsuz; taban: 147 sayıyı yazmak = 147 düzeltme)")
    print(f"  {'yöntem':<46} {'1. aday doğru':>13} {'seçim':>6} {'sil':>5} {'yaz':>5} {'düzeltme':>9}")
    rapor["duzeltme"] = {}
    for ad, s, dik, sifir in (("çoğunluk, süzmesiz tek hane", False, 1.0, 1.0),
                              ("yön ağırlıklı, süzmesiz tek hane", False, 0.2, 1.5),
                              ("yön ağırlıklı, tek hane + ASCII süzmeli", True, 0.2, 1.5)):
        d = duzeltme(kume[s], dik, sifir)
        print(f"  {ad:<46} {d['dogru']:>13} {d['secim']:>6} {d['sil']:>5} {d['yaz']:>5} {d['duzeltme']:>9}")
        rapor["duzeltme"][ad] = dict(d)
    (KLASOR / "sonuclar" / "puan_karo_son.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=1),
                                                            encoding="utf-8")


if __name__ == "__main__":
    main()
