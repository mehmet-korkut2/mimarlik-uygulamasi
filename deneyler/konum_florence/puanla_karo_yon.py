"""Yön ağırlıklı oylama (karolama + döndürme kayıtları üzerinde; model çağırmaz). `RAPOR_03_07.md` bölüm 9.

    PYTHONIOENCODING=utf-8 .venv/Scripts/python deneyler/konum_florence/puanla_karo_yon.py

Sorun (bölüm 8): çoğunluk oylamasında döndürülmüş karoların yanlış okuması düz sayıların doğrusunu yeniyor.
Fikir: model yazıyı doğru yönde gördüyse, kendi okuduğu (döndürülmüş) görselde kutu yatay olur (en ≥ boy).
Kutu kendi çerçevesinde dikeyse model yazıyı yan okumuş: oyu düşük.
- Kendi çerçevesinde en/boy: 0° ve 180°'de özgün kutunun en/boyu, 90° ve 270°'de tersi.
- Ağırlık: en/boy ≥ 1 → 1; < 1 → 0,2. Tek haneli okuma (doğal olarak dar) → 1.
- "+ 0° önceliği": ek olarak 0° okuması × 1,5 (düz yazı en yaygın yön).
Katsayılar tek seferde seçildi, 03–07'ye ayarlanmadı. Süzme ve kümeleme `puanla_karo.py` ile aynı.
"""

import json
from collections import Counter, defaultdict

from puanla_03_07 import GERCEK, KLASOR, eslestir, ogeler, sayilar
from puanla_karo import KAYIT, kumele, oyla, uydurma

DIK_AGIRLIK, SIFIR_ONCELIK = 0.2, 1.5


def agirlik(ss, kutu, aci, sifir):
    en, boy = max(1, kutu[2] - kutu[0]), max(1, kutu[3] - kutu[1])
    oran = en / boy if aci in ("0", "180") else boy / en
    tek_hane = len(ss) == 1 and len(ss[0]) == 1
    w = 1.0 if tek_hane or oran >= 1 else DIK_AGIRLIK
    return w * (SIFIR_ONCELIK if sifir and aci == "0" else 1.0)


def yon_oyla(kume, sifir):
    puan = defaultdict(float)
    for ss, kutu, aci in kume:
        puan[ss] += agirlik(ss, kutu, aci, sifir)
    return max(puan.items(), key=lambda kv: (kv[1], len(kv[0])))[0]


def cevaplar(kayit_kod):
    tes = []
    for t in kayit_kod["tespitler"]:
        ss = sayilar(t["metin"])
        if ss and not uydurma(ss):
            tes.append((tuple(ss), t["kutu"], t["aci"]))
    kumeler = kumele(tes)
    return {
        "çoğunluk (§8)": [s for k in kumeler for s in oyla(k)[0]],
        "yön ağırlıklı": [s for k in kumeler for s in yon_oyla(k, False)],
        "yön + 0° önceliği": [s for k in kumeler for s in yon_oyla(k, True)],
    }


def main():
    kayit = json.loads(KAYIT.read_text(encoding="utf-8"))
    cv = {kod: cevaplar(kayit[kod]) for kod in GERCEK}
    sutunlar = list(next(iter(cv.values())))
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
    rapor = {"kategori": {}, "fazla": dict(fazla)}
    print(f"{'kategori':<26} {'n':>4}  " + "  ".join(f"{s:>18}" for s in sutunlar))
    for e in kategoriler:
        n = say[sutunlar[0]][(e, "top")]
        d = [say[s][(e, "dogru")] for s in sutunlar]
        print(f"{e:<26} {n:>4}  " + "  ".join(f"{x:>11} ({x / n:4.0%})" for x in d))
        rapor["kategori"][e] = {"n": n, **dict(zip(sutunlar, d))}
    print(f"{'fazla (listede yok)':<26} {'':>4}  " + "  ".join(f"{fazla[s]:>18}" for s in sutunlar))

    # Hangi sayılar kazanıldı / kaybedildi (çoğunluğa göre)
    for s in sutunlar[1:]:
        kaz, kay = [], []
        for kod in GERCEK:
            a, b = eslestir(kod, cv[kod][sutunlar[0]])[0], eslestir(kod, cv[kod][s])[0]
            for o in puanli[kod]:
                if b[o["i"]] and not a[o["i"]]:
                    kaz.append(f"{kod}:{o['deger']}({o['yazilis']})")
                elif a[o["i"]] and not b[o["i"]]:
                    kay.append(f"{kod}:{o['deger']}({o['yazilis']})")
        print(f"\n{s}: kazanılan {len(kaz)}: {' '.join(kaz)}\n{'':>{len(s)}}  kaybedilen {len(kay)}: {' '.join(kay)}")
        rapor[f"degisim {s}"] = {"kazanilan": kaz, "kaybedilen": kay}
    (KLASOR / "sonuclar" / "puan_karo_yon.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=1),
                                                            encoding="utf-8")


if __name__ == "__main__":
    main()
