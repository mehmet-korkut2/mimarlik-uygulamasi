"""Yanlış yerleri elemek: ölçü çizgisi yakınlığı (ve karşılaştırma için oy desteği). `RAPOR_03_07.md` bölüm 11.
Model çağırmaz; karolama + döndürme kayıtları ve özgün fotoğraf (çizgi maskesi için) kullanılır.

    PYTHONIOENCODING=utf-8 .venv/Scripts/python deneyler/konum_florence/puanla_karo_cizgi.py

Birleştirme bölüm 10'un en iyi ayarı: tek hane + ASCII dışı süzme, yön ağırlıklı oylama (dik 0,2, 0° × 1,5).

Çizgi maskesi (renkten bağımsız; ürünün `on_isleme.murekkep_maskesi` yalnız mavi):
- Kâğıt: 51 px medyan bulanık gri > 140, en büyük bileşen, 20 px içeri (masa / fotoğraf kenarı dışarıda).
- Mürekkep: yerel arka plandan 50+ koyu.
- Yatay çizgi: mürekkep 3×3 genişletilip 1 × 61 çubukla açılır; dikey: 61 × 1. (El çizimi eğri çizgiye dayanıklı;
  Hough denendi, 06'da duvarların çoğunu kaçırdı, 07'de defter çizgilerini buldu.)
Yer başına çizgi yakınlığı (çeşitler: şerit 2 kat kalın; "iç": şerit kutunun içini de kapsar; ayrıca uzunluk = rakam sayısı): kazanan okumanın açısı yazı yönünü verir (0°/180° yatay, 90°/270° dikey). Kutunun iki
uzun kenarına bitişik, kalınlığı kısa kenar kadar, boyu kutudan %25 taşan şerit; şeritteki sütunların (dikeyde
satırların) ne kadarında paralel çizgi pikseli var → 0–1; iki şeridin büyüğü.
Oy desteği: kazanan değerin yön ağırlıklı oy toplamı.

Etiket (konumsuz, kaba): yerin 1. adayı listede kalan bir sayıysa "doğru", "?" adayıysa "soru", değilse "yanlış".
Eleme: eşik altındaki yer gösterilmez. Düzeltme = sil (gösterilen yanlış, 2./3. aday da yoksa) + seçim + yaz
(hiç okunmayan ya da elenen doğru).
"""

import json
from collections import Counter, defaultdict

import cv2
import numpy as np

from okuma_03_07 import gorsel
from puanla_03_07 import GERCEK, KLASOR, ogeler
from puanla_karo import KAYIT, kumele
from puanla_karo_son import sirali, tespitler
import puanla_karo_yon as yon

DIK, SIFIR = 0.2, 1.5


def cizgi_maskeleri(bgr):
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    arka = cv2.medianBlur(g, 51)
    kagit = (arka > 140).astype(np.uint8)
    _, lab, st, _ = cv2.connectedComponentsWithStats(kagit)
    kagit = cv2.erode((lab == 1 + np.argmax(st[1:, 4])).astype(np.uint8), np.ones((41, 41), np.uint8))
    murekkep = (((arka.astype(int) - g) > 50) & (kagit > 0)).astype(np.uint8)
    m = cv2.dilate(murekkep, np.ones((3, 3), np.uint8))
    yatay = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((1, 61), np.uint8))
    dikey = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((61, 1), np.uint8))
    return yatay > 0, dikey > 0


def yakinlik(kutu, yatay_yazi, maskeler, kat=1, ic=False):
    yatay, dikey = maskeler
    H, W = yatay.shape
    x0, y0, x1, y1 = (int(round(v)) for v in kutu)
    en, boy = max(1, x1 - x0), max(1, y1 - y0)
    if yatay_yazi:
        s, ux = kat * boy, int(0.25 * en)
        seritler = [(x0 - ux, y0 - s, x1 + ux, y0 if not ic else y1), (x0 - ux, y1 if not ic else y0, x1 + ux, y1 + s)]
        maske, eksen = yatay, 0   # sütunlarda çizgi var mı
    else:
        s, uy = kat * en, int(0.25 * boy)
        seritler = [(x0 - s, y0 - uy, x0 if not ic else x1, y1 + uy), (x1 if not ic else x0, y0 - uy, x1 + s, y1 + uy)]
        maske, eksen = dikey, 1
    en_iyi = 0.0
    for a0, b0, a1, b1 in seritler:
        a0, b0, a1, b1 = max(0, a0), max(0, b0), min(W, a1), min(H, b1)
        if a1 <= a0 or b1 <= b0:
            continue
        parca = maske[b0:b1, a0:a1]
        en_iyi = max(en_iyi, float(parca.any(axis=eksen).mean()))
    return en_iyi


def yerler(kayit_kod, maskeler):
    out = []
    for k in kumele(tespitler(kayit_kod, True)):
        aday = sirali(k, DIK, SIFIR)
        kaz = [t for t in k if t[0] == aday[0]]
        eski = yon.DIK_AGIRLIK, yon.SIFIR_ONCELIK
        yon.DIK_AGIRLIK, yon.SIFIR_ONCELIK = DIK, SIFIR
        destek = sum(yon.agirlik(t[0], t[1], t[2], True) for t in kaz)
        yon.DIK_AGIRLIK, yon.SIFIR_ONCELIK = eski
        acilar = Counter(t[2] for t in kaz)
        yatay_yazi = sum(c for a, c in acilar.items() if a in ("0", "180")) >= sum(acilar.values()) / 2
        kutu = np.median(np.array([t[1] for t in kaz], float), axis=0)
        out.append({"aday": aday[:3], "destek": destek, "cizgi": yakinlik(kutu, yatay_yazi, maskeler),
                    "cizgi_2kat": yakinlik(kutu, yatay_yazi, maskeler, kat=2),
                    "cizgi_ic": yakinlik(kutu, yatay_yazi, maskeler, ic=True),
                    "cizgi_ic_2kat": yakinlik(kutu, yatay_yazi, maskeler, kat=2, ic=True),
                    "uzunluk": sum(len(x) for x in aday[0])})
    return out


def etiketle(kod, yer_listesi):
    kalan = Counter(o["deger"] for o in ogeler(kod) if o["emin"])
    soru = Counter(a for o in ogeler(kod) if not o["emin"] for a in [o["deger"], *o["alt"]] if a != "?")
    for y in yer_listesi:
        bir = Counter(y["aday"][0])
        if all(kalan[d] >= c for d, c in bir.items()):
            kalan -= bir
            y["etiket"] = "doğru"
        elif all(soru[d] >= c for d, c in bir.items()):
            soru -= bir
            y["etiket"] = "soru"
        else:
            y["etiket"] = "yanlış"


def duzeltme(yer_kod, tut):
    t = Counter()
    for kod, yl in yer_kod.items():
        kalan = Counter(o["deger"] for o in ogeler(kod) if o["emin"])
        gosterilen = [y for y in yl if tut(y)]
        yanlis = []
        for y in gosterilen:
            bir = Counter(y["aday"][0])
            if y["etiket"] == "doğru" and all(kalan[d] >= c for d, c in bir.items()):
                kalan -= bir
                t["dogru"] += sum(bir.values())
            elif y["etiket"] == "yanlış":
                yanlis.append(y)
        for y in yanlis:
            sec = next((x for x in y["aday"][1:3] if all(kalan[d] >= c for d, c in Counter(x).items())), None)
            if sec:
                kalan -= Counter(sec)
                t["secim"] += 1
            else:
                t["sil"] += 1
        t["yaz"] += sum(kalan.values())
        t["gosterilen"] += len(gosterilen)
    t["duzeltme"] = t["secim"] + t["sil"] + t["yaz"]
    return t


def main():
    kayit = json.loads(KAYIT.read_text(encoding="utf-8"))
    yer_kod = {}
    for kod in GERCEK:
        yer_kod[kod] = yerler(kayit[kod], cizgi_maskeleri(gorsel(kod)))
        etiketle(kod, yer_kod[kod])
    hepsi = [y for yl in yer_kod.values() for y in yl]
    rapor = {}

    print("Yer sayısı:", Counter(y["etiket"] for y in hepsi))
    print("\nÖzellik dağılımı (medyan; çeyrekler):")
    for oz in ("cizgi", "destek"):
        for e in ("doğru", "yanlış", "soru"):
            v = np.array([y[oz] for y in hepsi if y["etiket"] == e])
            if len(v):
                q = np.percentile(v, [25, 50, 75])
                print(f"  {oz:<7} {e:<7} n={len(v):>3}  medyan {q[1]:.2f}  ({q[0]:.2f}–{q[2]:.2f})")

    def auc(oz):
        d = [y[oz] for y in hepsi if y["etiket"] == "doğru"]
        w = [y[oz] for y in hepsi if y["etiket"] == "yanlış"]
        return sum((a > b) + 0.5 * (a == b) for a in d for b in w) / (len(d) * len(w))
    print(f"\nAyırma gücü (AUC: rastgele doğru yerin özelliği rastgele yanlış yerinkinden büyük olma olasılığı; "
          f"0,5 = işe yaramaz):")
    rapor["auc"] = {}
    for oz in ("cizgi", "cizgi_2kat", "cizgi_ic", "cizgi_ic_2kat", "destek", "uzunluk"):
        rapor["auc"][oz] = auc(oz)
        print(f"  {oz:<14} {auc(oz):.2f}")

    print("\nEleme (eşik altı yer gösterilmez):")
    print(f"  {'kural':<34} {'göst.':>5} {'doğru elenen':>12} {'yanlış elenen':>13} "
          f"{'1. aday doğru':>13} {'seçim':>5} {'sil':>4} {'yaz':>4} {'düzeltme':>8}")
    kurallar = [("eleme yok (bölüm 10)", lambda y: True)]
    kurallar += [(f"çizgi ≥ {t}", (lambda t: lambda y: y["cizgi"] >= t)(t)) for t in (0.2, 0.4, 0.6, 0.8)]
    kurallar += [(f"destek ≥ {t}", (lambda t: lambda y: y["destek"] >= t)(t)) for t in (1.5, 2, 3, 4)]
    kurallar += [(f"çizgi ≥ 0,4 ya da destek ≥ {t}",
                  (lambda t: lambda y: y["cizgi"] >= 0.4 or y["destek"] >= t)(t)) for t in (2, 3)]
    kurallar += [("çizgi ≥ 0,2 ve destek ≥ 1,5", lambda y: y["cizgi"] >= 0.2 and y["destek"] >= 1.5)]
    rapor["eleme"] = {}
    for ad, tut in kurallar:
        el = Counter(y["etiket"] for y in hepsi if not tut(y))
        d = duzeltme(yer_kod, tut)
        print(f"  {ad:<34} {d['gosterilen']:>5} {el['doğru']:>12} {el['yanlış']:>13} {d['dogru']:>13} "
              f"{d['secim']:>5} {d['sil']:>4} {d['yaz']:>4} {d['duzeltme']:>8}")
        rapor["eleme"][ad] = {**dict(d), "elenen_dogru": el["doğru"], "elenen_yanlis": el["yanlış"]}
    print("  (taban: hiç okuma yok = 147 yaz)")

    print("\nKroki başına (çizgi ≥ 0,4): doğru / yanlış yerlerin çizgi değerleri")
    for kod, yl in yer_kod.items():
        d = [round(y["cizgi"], 1) for y in yl if y["etiket"] == "doğru"]
        w = [round(y["cizgi"], 1) for y in yl if y["etiket"] == "yanlış"]
        print(f"  {kod}: doğru {sorted(d)}\n      yanlış {sorted(w)}")
    rapor["yerler"] = {k: [{**y, "aday": [list(a) for a in y["aday"]]} for y in yl] for k, yl in yer_kod.items()}
    (KLASOR / "sonuclar" / "puan_karo_cizgi.json").write_text(json.dumps(rapor, ensure_ascii=False, indent=1),
                                                              encoding="utf-8")


if __name__ == "__main__":
    main()
