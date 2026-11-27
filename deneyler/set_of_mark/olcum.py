"""Set-of-Mark ile Ö2'nin (ve eski kuralın) aynı ölçütle karşılaştırması: değer doğru bölgeye gidiyor mu?

Puan (24 gerçek sayının her biri için, konumlar.GERCEK kutusuyla örtüşen bölge(ler)e bakılır):
  doğru  : örtüşen bölgelerden birine doğru değer gitti,
  yanlış : örtüşen bölgeye başka bir değer gitti (doğrusu gitmedi),
  yok    : örtüşen bölge var ama değer gitmedi,
  bölge yok: bölge bulucu bu sayı için bölge bulmadı (yöntemden bağımsız sınır).
  fazla  : gerçek sayıyla örtüşmeyen bölgeye (gürültü, kılavuz, bölünmüş sayı parçası) değer gitti.
Ö2 ve eski kural: ürün koşulundaki 3 kayıtlı Qwen-1 cevabı (deneyler/cizgi_silme/sonuclar/qwen_urun.json), aynı bölgeler.

Çalıştırma (repo kökünden): PYTHONIOENCODING=utf-8 .venv/Scripts/python deneyler/set_of_mark/olcum.py
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

KLASOR = Path(__file__).resolve().parent
REPO = KLASOR.parents[1]
sys.path[:0] = [str(REPO), str(REPO / "deneyler" / "bul_kes_okut")]
from konumlar import GERCEK  # noqa: E402

from mimarlik import okuma  # noqa: E402
from mimarlik.eslestirme import degerleri_ata  # noqa: E402

TESPIT = REPO / "deneyler" / "konum_florence" / "sonuclar" / "tespitler.json"
ADLAR = {"01": "01_kolay_tek_oda_180x140", "02": "02_kolay_tek_oda_300x240"}


def ortusuyor(a, b):
    return min(a[2], b[2]) > max(a[0], b[0]) and min(a[3], b[3]) > max(a[1], b[1])


def puanla(kod, atama):
    """atama: [(bölge kutusu, değer ya da None)] -> Counter(doğru, yanlış, yok, bölge yok, fazla) ve doğru sayılar."""
    c, dogrular = Counter(), []
    for ad, deger, gk in GERCEK[kod]:
        ilgili = [d for k, d in atama if ortusuyor(k, gk)]
        if not ilgili:
            c["bölge yok"] += 1
        elif deger in ilgili:
            c["doğru"] += 1
            dogrular.append(ad)
        elif any(d is not None for d in ilgili):
            c["yanlış"] += 1
        else:
            c["yok"] += 1
    c["fazla"] = sum(d is not None and not any(ortusuyor(k, gk) for _, _, gk in GERCEK[kod]) for k, d in atama)
    return c, dogrular


def som_cevabi(ham, eslem):
    bulunan = re.search(r"\{.*\}", ham or "", re.S)
    try:
        veri = json.loads(bulunan.group(0)) if bulunan else {}
    except json.JSONDecodeError:
        veri = {}
    return {e: (okuma._sayi(veri.get(e)) if veri.get(e) is not None else None) for e in eslem}


def _yukle(ad, yol):
    """Aynı adlı deney modülleri (olcum.py, calistir.py) çakışmasın diye dosya yoluyla yükle."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(ad, yol)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def main():
    som = _yukle("som_calistir", KLASOR / "calistir.py")
    eski_ata = _yukle("deger_atama_olcum", REPO / "deneyler" / "deger_atama" / "olcum.py").eski_ata
    kayitlar = json.loads((REPO / "deneyler/cizgi_silme/sonuclar/qwen_urun.json").read_text(encoding="utf-8"))
    som_sonuc = json.loads((KLASOR / "sonuclar" / "som.json").read_text(encoding="utf-8"))
    tablo, tutarlilik, cikti = {}, {}, {"ozet": {}, "ayrinti": {}}
    for kod, ad in ADLAR.items():
        bgr, maske, h, bl = som.bolgeler(ad)
        k = som_sonuc["krokiler"][kod]
        cevaplar = [som_cevabi(c["ham"], k["eslem"]) for c in k["calistirmalar"]]
        for n, cv in enumerate(cevaplar, 1):
            atama = [(k["eslem"][e], d) for e, d in cv.items()]
            tablo.setdefault("Set-of-Mark", []).append((kod, n, *puanla(kod, atama)))
        ayni = sum(len({cv[e] for cv in cevaplar}) == 1 for e in k["eslem"])
        tutarlilik[kod] = (ayni, len(k["eslem"]))
        cogunluk = {}
        for e in k["eslem"]:
            d, say = Counter(cv[e] for cv in cevaplar).most_common(1)[0]
            cogunluk[e] = d if say >= 2 else None
        tablo.setdefault("Set-of-Mark çoğunluk (3 çağrı)", []).append(
            (kod, 1, *puanla(kod, [(k["eslem"][e], d) for e, d in cogunluk.items()])))
        kutudan = {tuple(v): e for e, v in k["eslem"].items()}

        def hepsi(cift):
            # Değer almayan bölgeler de None ile verilir: "yok" ile "bölge yok" ayrılsın.
            degerler = {tuple(b.kutu): d for b, d in cift}
            return [(b.kutu, degerler.get(tuple(b.kutu))) for b in bl]

        # Florence-2 (ham, tam; deterministik, tek çalıştırma) değer + kutuları Qwen'in yerine Ö2'ye girer.
        flo_o2 = None
        if TESPIT.exists():
            flo = json.loads(TESPIT.read_text(encoding="utf-8"))["tespitler"]["Florence-2"][kod]["ham, tam"]
            flo_ogeler = [(d, tuple(x["kutu"])) for x in flo if (d := okuma._sayi(x["metin"])) is not None]
            flo_o2, _, _ = degerleri_ata(bl, flo_ogeler, h)
            tablo.setdefault("Ö2 + Florence-2 değerleri", []).append(
                (kod, 1, *puanla(kod, hepsi((b, d) for b, d, _ in flo_o2))))
            flo_bolge = {tuple(b.kutu): d for b, d, _ in flo_o2}
        for n, cal in enumerate(kayitlar["krokiler"][kod]["calistirmalar"], 1):
            ogeler = okuma.sayilari_ayristir(cal["ham"], 1152, 2048)
            o2, _, _ = degerleri_ata(bl, ogeler, h)
            if flo_o2 is not None:
                ortak = [(b, d) for b, d, _ in o2 if flo_bolge.get(tuple(b.kutu)) == d]
                tablo.setdefault("Florence-2 ∩ Ö2 (ikisi aynı değer)", []).append((kod, n, *puanla(kod, hepsi(ortak))))
            tablo.setdefault("Ö2 (ürün)", []).append((kod, n, *puanla(kod, hepsi((b, d) for b, d, _ in o2))))
            tablo.setdefault("Ö2, yalnız emin (≤ 0,5 h)", []).append(
                (kod, n, *puanla(kod, hepsi((b, d) for b, d, u in o2 if u <= 0.5))))
            eski = eski_ata(bl, ogeler)
            tablo.setdefault("eski kural", []).append((kod, n, *puanla(kod, hepsi((b, d) for b, d, _ in eski))))
            # SoM n. çağrı ile Ö2 n. çağrı aynı değeri veriyorsa tut (ayrı Qwen çağrıları: bağımsız iki kanıt).
            sm = cevaplar[n - 1]
            uyusan = [(b, d) for b, d, _ in o2 if sm.get(kutudan.get(tuple(b.kutu))) == d]
            tablo.setdefault("SoM ∩ Ö2 (ikisi aynı değer)", []).append((kod, n, *puanla(kod, hepsi(uyusan))))
    print(f"{'yöntem':<28} {'kroki #':<8} doğru yanlış  yok  bölge yok  fazla")
    for yontem, satirlar in tablo.items():
        top = Counter()
        for kod, n, c, _ in satirlar:
            top += c
            print(f"{yontem:<28} {kod} #{n:<4} {c['doğru']:>5} {c['yanlış']:>6} {c['yok']:>4} {c['bölge yok']:>10} "
                  f"{c['fazla']:>6}")
        print(f"{yontem:<28} {'toplam':<8} {top['doğru']:>5} {top['yanlış']:>6} {top['yok']:>4} "
              f"{top['bölge yok']:>10} {top['fazla']:>6}   ({len(satirlar) // 2} çalıştırma × 24 = {len(satirlar) * 12})\n")
        cikti["ozet"][yontem] = dict(top)
        cikti["ayrinti"][yontem] = [{"kroki": kod, "calistirma": n, **c, "dogru_sayilar": d} for kod, n, c, d in satirlar]
    for kod, (a, t) in tutarlilik.items():
        print(f"Set-of-Mark tutarlılığı {kod}: {a}/{t} bölgede 3 çalıştırmanın cevabı aynı")
    cikti["som_tutarlilik"] = {kod: {"ayni": a, "bolge": t} for kod, (a, t) in tutarlilik.items()}
    sure = [c["sure_s"] for k in som_sonuc["krokiler"].values() for c in k["calistirmalar"]]
    cikti["som_sure_s"] = sure
    print("Set-of-Mark süreleri (s):", sure)
    (KLASOR / "sonuclar" / "olcum.json").write_text(json.dumps(cikti, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
