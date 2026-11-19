"""Eşleştirme ölçümü: Ü (üst sınır), A (ara), G (gerçekçi) katmanları, Y3 (taban) ve varsa Y2 -> olcumler.md

Tasarım 7. Qwen girdisi yeni çağrı değil: ../konum_deneyi/sonuclar/qwen_konum.json (3 çalıştırma).
Çalıştırma (repo kökünden): PYTHONIOENCODING=utf-8 deneyler/.venv/Scripts/python deneyler/eslestirme/olcum.py
"""

import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

import cv2
from PIL import Image, ImageDraw

KLASOR = Path(__file__).resolve().parent
sys.path.insert(0, str(KLASOR))
from puanlama_eslestirme import (REPO, bolge_puani, ciftleri_cevir, eslestirme_puani, fazla_cift, gercek_ciftler,  # noqa: E402
                                 gercek_kenarlar, kenar_puani, kenara_eslestir, mimara_bagli_ciftler,
                                 parcalari_eslestir)
sys.path.insert(0, str(KLASOR.parent / "konum_deneyi"))
from ciz_bulunan import ciz as kenar_gorseli  # noqa: E402
from gercek_eslestirme import ANLAM_BILINMIYOR, ESLESME, KAPSAM_BELIRSIZ  # noqa: E402
from konum_istem import piksele_cevir  # noqa: E402
from konumlar import GERCEK  # noqa: E402
from mimarlik.bolge_bulma import bolge_olustur, bolgeleri_bul  # noqa: E402
from mimarlik.eslestirme import (EN_YAKIN_SINIRI, W_HANE, KenarSonucu, bagla, degerleri_ata,  # noqa: E402
                                 parcayi_bul)
from mimarlik.kenar_bulma import kenarlari_bul  # noqa: E402
from mimarlik.on_isleme import cizgileri_sil, karakter_yuksekligi, murekkep_maskesi  # noqa: E402
from ortak import KROKILER, _font  # noqa: E402

QWEN = KLASOR.parent / "konum_deneyi" / "sonuclar" / "qwen_konum.json"
Y2 = KLASOR / "sonuclar" / "y2.json"
Y2_KARISIK = KLASOR / "sonuclar" / "y2_karisik.json"
Y2_BULUNAN = KLASOR / "sonuclar" / "y2_bulunan_karisik.json"
GORSELLER = KLASOR / "gorseller"
KIRP = (40, 300, 1152, 1250)
YESIL, KIRMIZI, TURUNCU, GRI = (0, 150, 0), (220, 0, 0), (230, 120, 0), (170, 170, 170)


def _ortusme(kutu, bolge):
    x1, y1, x2, y2 = kutu
    bx1, by1, bx2, by2 = bolge
    g = max(0.0, min(x2, bx2) - max(x1, bx1))
    y = max(0.0, min(y2, by2) - max(y1, by1))
    return g * y / ((x2 - x1) * (y2 - y1))


def _gercek_ad(kod, kutu):
    """Bölge kutusunun en çok örtüştüğü (≥ %50) gerçek sayının adı."""
    en_iyi = max(GERCEK[kod], key=lambda g: _ortusme(g[2], kutu))
    return en_iyi[0] if _ortusme(en_iyi[2], kutu) >= 0.5 else None


class Kroki:
    """Bir krokinin ölçüm için hazırlanmış hali."""

    def __init__(self, kod):
        self.kod = kod
        self.bgr = cv2.imread(str(REPO / KROKILER[kod]))
        self.boyut = self.bgr.shape[:2]
        t0 = time.perf_counter()
        self.maske = murekkep_maskesi(self.bgr)
        self.h = karakter_yuksekligi(self.maske)
        self.bulunan = kenarlari_bul(self.maske, self.h)
        self.bolgeler = bolgeleri_bul(self.maske, self.bulunan, self.h)
        self.bulma_s = time.perf_counter() - t0
        g = gercek_kenarlar(kod)
        self.gercek = KenarSonucu(g.eksen_acisi_derece, g.kenarlar, g.kontur_sirasi, self.bulunan.isaretler)
        self.parca_es = parcalari_eslestir(self.bulunan, self.gercek)
        self.kenar_es = kenara_eslestir(self.bulunan, self.gercek)
        self.dogru = gercek_ciftler(kod)
        self.mimara = mimara_bagli_ciftler(kod)

    def ciftler(self, tahmin, uzay):
        """tahmin [(değer, parça id)] -> (katı çiftler, gevşek çiftler) gerçek kimlik uzayında."""
        if uzay == "gercek":
            return tahmin, tahmin
        return ciftleri_cevir(tahmin, self.parca_es), ciftleri_cevir(tahmin, self.kenar_es)

    def puanla(self, tahmin, uzay):
        kati, gevsek = self.ciftler(tahmin, uzay)
        return {"kati": eslestirme_puani(kati, self.dogru),
                "gevsek": eslestirme_puani(gevsek, self.dogru, kenar_duzeyi=True),
                "kati_haric": eslestirme_puani(kati, self.dogru, haric=self.mimara),
                "gevsek_haric": eslestirme_puani(gevsek, self.dogru, kenar_duzeyi=True, haric=self.mimara),
                "fazla": fazla_cift(kati, self.dogru), "tahmin_sayisi": len(tahmin)}


def _oge(ad, deger, kutu, parca, neden, kroki, uzay):
    """Tek bir bağlamanın kaydı; doğru mu (katı) gerçek ada göre."""
    pid = parca.id if parca else None
    eslenmis = pid if uzay == "gercek" else kroki.parca_es.get(pid)
    dogru = ad is not None and deger == dict((a, v) for a, v, _ in GERCEK[kroki.kod])[ad] and \
        eslenmis == ESLESME[kroki.kod][ad]
    return {"ad": ad, "deger": deger, "kutu": list(kutu), "parca": pid, "gercek_parca": eslenmis,
            "neden": neden, "dogru": dogru,
            "mimara": ad in ANLAM_BILINMIYOR[kroki.kod] | KAPSAM_BELIRSIZ[kroki.kod] if ad else False}


def katman_kutu(kroki, uzay):
    """Ü (uzay=gercek) ya da A (uzay=bulunan): gerçek kutular + gerçek değerler -> bağlama."""
    sonuc = kroki.gercek if uzay == "gercek" else kroki.bulunan
    ogeler = []
    for ad, deger, kutu in GERCEK[kroki.kod]:
        parca, neden = bagla(bolge_olustur(kroki.maske, kutu, sonuc, kroki.h), sonuc, kroki.h)
        ogeler.append(_oge(ad, deger, kutu, parca, neden, kroki, uzay))
    return ogeler


def qwen_ogeleri(kroki, calistirma):
    yuk, gen = kroki.boyut
    return [(k["deger"], tuple(piksele_cevir(k["kutu"], gen, yuk))) for k in calistirma["kutular"]
            if k["deger"] is not None and k["kutu"] is not None]


def katman_g(kroki, ogeler, w_hane):
    t0 = time.perf_counter()
    atanmis, yok, okunmamis = degerleri_ata(kroki.bolgeler, ogeler, kroki.boyut, w_hane=w_hane)
    sonuc = []
    for bolge, deger in atanmis:
        parca, neden = bagla(bolge, kroki.bulunan, kroki.h)
        sonuc.append(_oge(_gercek_ad(kroki.kod, bolge.kutu), deger, bolge.kutu, parca, neden, kroki, "bulunan"))
    sure = time.perf_counter() - t0
    gercek_degerler = dict((a, v) for a, v, _ in GERCEK[kroki.kod])
    deger_dogru = sum(o["ad"] is not None and gercek_degerler[o["ad"]] == o["deger"] for o in sonuc)
    return sonuc, {"atanan": len(atanmis), "deger_dogru": deger_dogru, "yeri_bulunamayan": len(yok),
                   "okunmamis_bolge": len(okunmamis), "sure_s": sure}


def katman_y3(kroki, ogeler, uzay):
    sonuc_k = kroki.gercek if uzay == "gercek" else kroki.bulunan
    tahmin = []
    for deger, kutu in ogeler:
        merkez = ((kutu[0] + kutu[2]) / 2, (kutu[1] + kutu[3]) / 2)
        p = parcayi_bul(merkez, sonuc_k.kenarlar, EN_YAKIN_SINIRI * kroki.h * 100, tercih=merkez)  # sınırsız: en yakın
        tahmin.append((deger, p.id if p else None))
    return tahmin


def _ciz_baglama(kroki, ogeler, uzay, ad, baslik):
    sonuc = kroki.gercek if uzay == "gercek" else kroki.bulunan
    parcalar = {p.id: p for k in sonuc.kenarlar for p in k.parcalar}
    resim = Image.fromarray(cv2.cvtColor(cizgileri_sil(kroki.bgr), cv2.COLOR_BGR2RGB))
    resim = Image.blend(resim, Image.new("RGB", resim.size, "white"), 0.6)
    kalem, font, kucuk = ImageDraw.Draw(resim), _font(22), _font(18)
    for p in parcalar.values():
        kalem.line([p.bas, p.bit], fill=GRI, width=6 if p.tur == "duvar" else 2)
        m = ((p.bas[0] + p.bit[0]) / 2, (p.bas[1] + p.bit[1]) / 2)
        kalem.text((m[0] + 6, m[1] + 2), p.id, fill=(120, 120, 120), font=kucuk)
    for o in ogeler:
        renk = YESIL if o["dogru"] else (TURUNCU if o["mimara"] else KIRMIZI)
        x1, y1, x2, y2 = o["kutu"]
        kalem.rectangle([x1, y1, x2, y2], outline=renk, width=3)
        if o["parca"] in parcalar:
            p = parcalar[o["parca"]]
            kalem.line([((x1 + x2) / 2, (y1 + y2) / 2), ((p.bas[0] + p.bit[0]) / 2, (p.bas[1] + p.bit[1]) / 2)],
                       fill=renk, width=2)
        etiket = f"{o['deger']}→{o['gercek_parca'] or o['parca'] or '—'} ({o['neden'] or '—'})"
        kalem.text((x1, y2 + 2), etiket, fill=renk, font=font, stroke_width=3, stroke_fill="white")
    resim = resim.crop(KIRP)
    ImageDraw.Draw(resim).text((10, 8), f"{kroki.kod} {baslik} · yeşil doğru, kırmızı yanlış, turuncu yanlış ama mimara bağlı",
                               fill=(0, 0, 0), font=font, stroke_width=3, stroke_fill="white")
    resim.save(GORSELLER / f"{ad}_{kroki.kod}.jpg", quality=90)


def _ciz_bolgeler(kroki):
    resim = Image.fromarray(cv2.cvtColor(cizgileri_sil(kroki.bgr), cv2.COLOR_BGR2RGB))
    resim = Image.blend(resim, Image.new("RGB", resim.size, "white"), 0.5)
    kalem, font = ImageDraw.Draw(resim), _font(22)
    for _, _, kutu in GERCEK[kroki.kod]:
        kalem.rectangle(kutu, outline=GRI, width=6)
    for b in kroki.bolgeler:
        renk = YESIL if _gercek_ad(kroki.kod, b.kutu) else KIRMIZI
        kalem.rectangle(b.kutu, outline=renk, width=3)
    resim = resim.crop(KIRP)
    ImageDraw.Draw(resim).text((10, 8), f"{kroki.kod} bölgeler · gri: gerçek kutu, yeşil: bir sayıyı kapsayan, kırmızı: yazı olmayan",
                               fill=(0, 0, 0), font=font, stroke_width=3, stroke_fill="white")
    resim.save(GORSELLER / f"bolgeler_{kroki.kod}.jpg", quality=90)


def _neden_dagilimi(ogeler):
    sayac = Counter((o["neden"], o["dogru"]) for o in ogeler)
    return {n: {"adet": sayac[(n, True)] + sayac[(n, False)], "dogru": sayac[(n, True)]}
            for n in ("isaret", "temas", "en_yakin", None)}


def olc():
    qwen = json.loads(QWEN.read_text(encoding="utf-8"))
    y2 = {ad: json.loads(yol.read_text(encoding="utf-8")) for ad, yol in (("Y2", Y2), ("Y2_karisik", Y2_KARISIK), ("Y2_bulunan", Y2_BULUNAN))
          if yol.exists()}
    GORSELLER.mkdir(exist_ok=True)
    sonuc = {"krokiler": {}}
    for kod in ("01", "02"):
        k = Kroki(kod)
        kenar_gorseli(kod)
        _ciz_bolgeler(k)
        r = {"h": k.h, "eksen": k.bulunan.eksen_acisi_derece, "bulma_s": k.bulma_s,
             "kenar_puani": kenar_puani(k.bulunan, k.gercek),
             "bolge_puani": bolge_puani(k.bolgeler, [kt for _, _, kt in GERCEK[kod]]),
             "bolge_sayisi": len(k.bolgeler)}
        for katman, uzay in (("U", "gercek"), ("A", "bulunan")):
            ogeler = katman_kutu(k, uzay)
            r[katman] = {"puan": k.puanla([(o["deger"], o["parca"]) for o in ogeler], uzay),
                         "nedenler": _neden_dagilimi(ogeler), "ogeler": ogeler}
            _ciz_baglama(k, ogeler, uzay, f"bag_{katman}", f"{katman} katmanı")
        for etiket, w in (("G_hane", W_HANE), ("G_ipucusuz", 0.0)):
            r[etiket] = []
            for i, cal in enumerate(qwen["krokiler"][kod]["calistirmalar"], 1):
                ogeler, atama = katman_g(k, qwen_ogeleri(k, cal), w)
                r[etiket].append({"puan": k.puanla([(o["deger"], o["parca"]) for o in ogeler], "bulunan"),
                                  "atama": atama, "nedenler": _neden_dagilimi(ogeler), "ogeler": ogeler})
                if i == 1:
                    _ciz_baglama(k, ogeler, "bulunan", f"bag_{etiket}1", f"{etiket} 1. çalıştırma")
        for uzay in ("gercek", "bulunan"):
            r[f"Y3_{uzay}"] = [{"puan": k.puanla(katman_y3(k, qwen_ogeleri(k, cal), uzay), uzay)}
                               for cal in qwen["krokiler"][kod]["calistirmalar"]]
        for ad, veri in y2.items():
            uzay = "bulunan" if veri.get("parcalar") == "bulunan" else "gercek"
            r[ad] = [{"puan": k.puanla([tuple(c) for c in cal["ciftler"]], uzay), "sure_s": cal["sure_s"]}
                     for cal in veri["krokiler"][kod]["calistirmalar"]]
        sonuc["krokiler"][kod] = r
        print(f"{kod}: Ü {r['U']['puan']['kati']}, A {r['A']['puan']['kati']}, "
              f"G {[g['puan']['kati'] for g in r['G_hane']]}", flush=True)
    (KLASOR / "sonuclar").mkdir(exist_ok=True)
    (KLASOR / "sonuclar" / "olcum.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1, default=str),
                                                     encoding="utf-8")
    (KLASOR / "olcumler.md").write_text(rapor(sonuc), encoding="utf-8")
    print("Yazıldı: olcumler.md, sonuclar/olcum.json")


def _toplam(sonuc, anahtar, i=None, alan="kati"):
    deger = 0
    for r in sonuc["krokiler"].values():
        x = r[anahtar] if i is None else r[anahtar][i]
        deger += x["puan"][alan]
    return deger


def rapor(sonuc):
    kr = sonuc["krokiler"]
    payda = sum(len(GERCEK[k]) for k in kr)
    payda_h = payda - sum(len(mimara_bagli_ciftler(k)) for k in kr)
    s = ["<!-- olcum.py üretir; elle düzenleme. -->", "# Eşleştirme ölçümleri", ""]
    s += ["## Kenar bulma", "", "| Kroki | h (px) | Eksen (°) | Gerçek parça | Bulunan (eşleşen) | Kaçırılan | Fazla | Tür doğru | Kontur doğru |",
          "|---|---|---|---|---|---|---|---|---|"]
    for kod, r in kr.items():
        kp = r["kenar_puani"]
        s.append(f"| {kod} | {r['h']:.1f} | {r['eksen']:.1f} | {kp['bulunan'] + kp['kaciran']} | {kp['bulunan']} | "
                 f"{kp['kaciran']} | {kp['fazla']} | {kp['tur_dogru']} | {'evet' if kp['kontur_dogru'] else 'hayır'} |")
    s += ["", "## Bölge bulma (gerçekçi katman)", "",
          "| Kroki | Gerçek sayı | Bulunan (≥ %50 kapsanan) | Bölge sayısı | Yazı olmayan | Bölünmüş | Birleşmiş |",
          "|---|---|---|---|---|---|---|"]
    for kod, r in kr.items():
        bp = r["bolge_puani"]
        s.append(f"| {kod} | {len(GERCEK[kod])} | {bp['bulunan']} | {r['bolge_sayisi']} | {bp['yazi_olmayan']} | "
                 f"{bp['bolunmus']} | {bp['birlesmis']} |")
    s += ["", f"## Eşleştirme (01 + 02; katı/gevşek /{payda}, mimara bağlılar hariç /{payda_h})", "",
          "Çalıştırmalı satırlarda değerler çalıştırma başına (1/2/3).", "",
          "Fazla: doğru olmayan bağlama sayısı (yanlış parça, uydurma ya da fazla okunan değer); "
          "tasarım 7.3'e göre fazla değerin bir yere bağlanması hatadır.", "",
          "| Katman | Kenarlar | Yerler | Değerler | Katı | Gevşek | Katı (hariç) | Gevşek (hariç) | Fazla |",
          "|---|---|---|---|---|---|---|---|---|"]

    def satir(ad, kenar, yer, deger, anahtar, cok):
        hucre = []
        for alan in ("kati", "gevsek", "kati_haric", "gevsek_haric", "fazla"):
            if cok:
                n = len(next(iter(kr.values()))[anahtar])
                hucre.append("/".join(str(_toplam(sonuc, anahtar, i, alan)) for i in range(n)))
            else:
                hucre.append(str(_toplam(sonuc, anahtar, None, alan)))
        s.append(f"| {ad} | {kenar} | {yer} | {deger} | " + " | ".join(hucre) + " |")

    satir("**Ü** üst sınır", "gerçek", "gerçek kutu", "gerçek", "U", False)
    satir("**A** ara", "bulunan", "gerçek kutu", "gerçek", "A", False)
    satir("**G** gerçekçi, hane ipuçlu", "bulunan", "bulunan bölge", "Qwen", "G_hane", True)
    satir("**G** gerçekçi, ipuçsuz", "bulunan", "bulunan bölge", "Qwen", "G_ipucusuz", True)
    satir("Y3 taban", "gerçek", "Qwen kutusu", "Qwen", "Y3_gercek", True)
    satir("Y3 taban", "bulunan", "Qwen kutusu", "Qwen", "Y3_bulunan", True)
    if all("Y2" in r for r in kr.values()):
        satir("Y2 numaralı parçalar (kontur sırası)", "gerçek", "—", "Qwen", "Y2", True)
    if all("Y2_karisik" in r for r in kr.values()):
        satir("Y2 numaralı parçalar (karışık sıra)", "gerçek", "—", "Qwen", "Y2_karisik", True)
    if all("Y2_bulunan" in r for r in kr.values()):
        satir("**Y2 numaralı parçalar (karışık sıra)**", "bulunan", "—", "Qwen", "Y2_bulunan", True)

    s += ["", "### Kroki kroki (katı)", "", "| Katman | 01 /10 | 02 /14 |", "|---|---|---|"]
    for anahtar in ("U", "A", "G_hane", "G_ipucusuz", "Y3_gercek", "Y3_bulunan", "Y2", "Y2_karisik", "Y2_bulunan"):
        if not all(anahtar in r for r in kr.values()):
            continue
        hucre = []
        for r in kr.values():
            x = r[anahtar]
            hucre.append(str(x["puan"]["kati"]) if isinstance(x, dict) else "/".join(str(c["puan"]["kati"]) for c in x))
        s.append(f"| {anahtar} | " + " | ".join(hucre) + " |")

    s += ["", "## Değer atama (G; doğru değeri alan bölge / atanan, çalıştırma başına)", "",
          "| Kroki | Hane ipuçlu | İpuçsuz | Yeri bulunamayan (ipuçlu) | Okunmamış bölge (ipuçlu) |", "|---|---|---|---|---|"]
    for kod, r in kr.items():
        f = lambda e: "/".join(f"{g['atama']['deger_dogru']}÷{g['atama']['atanan']}" for g in r[e])  # noqa: E731
        s.append(f"| {kod} | {f('G_hane')} | {f('G_ipucusuz')} | "
                 f"{'/'.join(str(g['atama']['yeri_bulunamayan']) for g in r['G_hane'])} | "
                 f"{'/'.join(str(g['atama']['okunmamis_bolge']) for g in r['G_hane'])} |")

    s += ["", "## Bağlama nedeni (adet / doğru)", "", "| Katman | işaret | temas | en yakın | bağlanamadı |", "|---|---|---|---|---|"]
    for anahtar in ("U", "A"):
        t = Counter()
        for r in kr.values():
            for n, v in r[anahtar]["nedenler"].items():
                t[(n, "a")] += v["adet"]
                t[(n, "d")] += v["dogru"]
        s.append(f"| {anahtar} | " + " | ".join(f"{t[(n, 'a')]} / {t[(n, 'd')]}" for n in ("isaret", "temas", "en_yakin", None)) + " |")
    t = Counter()
    for r in kr.values():
        for g in r["G_hane"]:
            for n, v in g["nedenler"].items():
                t[(n, "a")] += v["adet"]
                t[(n, "d")] += v["dogru"]
    s.append("| G ipuçlu (3 çalıştırma toplamı) | " + " | ".join(f"{t[(n, 'a')]} / {t[(n, 'd')]}" for n in ("isaret", "temas", "en_yakin", None)) + " |")

    s += ["", "## Süre (kroki başına, Qwen hariç)", ""]
    for kod, r in kr.items():
        atama = sum(g["atama"]["sure_s"] for g in r["G_hane"]) / len(r["G_hane"])
        s.append(f"- {kod}: kenar + bölge bulma {r['bulma_s']:.2f} s, atama + bağlama {atama * 1000:.0f} ms")
    for ad in ("Y2", "Y2_karisik", "Y2_bulunan"):
        if all(ad in r for r in kr.values()):
            s.append(f"- {ad} (Qwen, kroki başına): {', '.join(f'{c['sure_s']:.0f}' for r in kr.values() for c in r[ad])} s")

    s += ["", "## Ayrıntı: Ü ve A katmanında her sayı", "", "| Kroki | Sayı | Gerçek parça | Ü | Ü nedeni | A | A nedeni |", "|---|---|---|---|---|---|---|"]
    for kod, r in kr.items():
        for u, a in zip(r["U"]["ogeler"], r["A"]["ogeler"]):
            isaret = lambda o: ("✓ " if o["dogru"] else "✗ ") + str(o["gercek_parca"] or o["parca"])  # noqa: E731
            s.append(f"| {kod} | {u['ad']}{' (mimara)' if u['mimara'] else ''} | {ESLESME[kod][u['ad']]} | "
                     f"{isaret(u)} | {u['neden']} | {isaret(a)} | {a['neden']} |")
    return "\n".join(s) + "\n"


if __name__ == "__main__":
    olc()
