"""Hata analizinin bağlama matrisi: her sayının 12 denemedeki (Ü, A, G×3, Y2g×3, Y2b×3, İsk) sonucu ve sınıfı.

RAPOR.md bölüm 1.5 ve 2'deki bağlama sayıları buradan gelir.
- Ü, A, G: ../eslestirme/sonuclar/olcum.json
- Y2g, Y2b: ../eslestirme/sonuclar/y2_karisik.json, y2_bulunan_karisik.json
- İsk: sonuclar/iskelet_adim0.json (iskeletin mimar cevaplarından önceki çalıştırması)
Bulunan kenar kimlikleri gerçek parçalara, ölçümlerin yapıldığı kenar bulma koduyla eşlenir: X kuralından
önceki sürüm (`40d19d1`), `git show` ile geçici bir dosyaya alınır. Fotoğraflar (`ornekler/`) gerekir.
Sınıf ataması (SABIT, GERCEK_KENAR) analistin yargısıdır; RAPOR.md "Yöntem ve sınırlar".

Çalıştırma (repo kökünden): PYTHONIOENCODING=utf-8 .venv/Scripts/python deneyler/hata_analizi/y2_hatalar.py
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

KLASOR = Path(__file__).resolve().parent
REPO = KLASOR.parents[1]
sys.path.insert(0, str(REPO / "deneyler" / "eslestirme"))
sys.path.insert(0, str(REPO / "deneyler" / "bul_kes_okut"))
import cv2  # noqa: E402

from gercek_eslestirme import ESLESME  # noqa: E402
from konumlar import GERCEK  # noqa: E402
from puanlama_eslestirme import ciftleri_cevir, gercek_kenarlar, parcalari_eslestir  # noqa: E402

from mimarlik.on_isleme import karakter_yuksekligi, murekkep_maskesi  # noqa: E402

OLCUM_KODU = "40d19d1"   # eşleştirme ölçümlerinin ve iskeletin ilk çalıştırmasının kenar bulması (X kuralından önce)
YOL = {"01": "ornekler/01_kolay_tek_oda_180x140.jpg", "02": "ornekler/02_kolay_tek_oda_300x240.jpg"}

# --- Sınıf ataması (RAPOR.md bölüm 2) ------------------------------------------------------------
OKUMA_HATASI = {162: "S1", 96: "S1"}          # sayının içinden geçen çizgi
SABIT = {  # (kroki, sayı) -> kök sebep (bulunan kenar katmanlarında)
    ("01", "108"): "S8b", ("01", "10"): "S10", ("01", "15"): "S10", ("01", "120 sol"): "S10",
    ("01", "90"): "S11", ("01", "50"): "S8a", ("01", "40"): "S8a", ("01", "180"): "S15",
    ("02", "300"): "S10", ("02", "45 üst sol"): "S8b", ("02", "15"): "S11", ("02", "90"): "S11",
    ("02", "40 üst"): "S11", ("02", "45 alt"): "S12", ("02", "200 sol"): "S15", ("02", "102"): "S1",
}
GERCEK_KENAR = {("01", "10"): "S9", ("01", "15"): "S11", ("01", "90"): "S11", ("01", "50"): "S8a",
                ("01", "40"): "S8a", ("02", "200 sol"): "S15"}   # gerçek kenarlı katmanlarda (Ü, Y2g)


def eski_kenar_bulma():
    kaynak = subprocess.run(["git", "show", f"{OLCUM_KODU}:mimarlik/kenar_bulma.py"], cwd=REPO,
                            capture_output=True, text=True, encoding="utf-8", check=True).stdout
    dosya = Path(tempfile.mkdtemp()) / "eski_kenar_bulma.py"
    dosya.write_text(kaynak, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("eski_kenar_bulma", dosya)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def degerlendir(kod, ciftler):
    """ciftler gerçek id uzayında (çoklu küme). Döner: (yanlış sayı adları, fazla çiftler)."""
    kalan, yanlis = Counter(ciftler), []
    for ad, deger, _ in GERCEK[kod]:
        c = (deger, ESLESME[kod][ad])
        if kalan[c] > 0:
            kalan[c] -= 1
        else:
            yanlis.append(ad)
    return yanlis, sorted(kalan.elements(), key=str)


def sinif(kod, ad, katman, deger=None):
    """Değer yanlışsa okuma (S1) / değer atama (S7, G) / Y2 uydurma (S15); değer doğruysa parçanın sebebi."""
    gd = {a: d for a, d, _ in GERCEK[kod]}
    if deger is not None and deger != gd[ad]:
        return OKUMA_HATASI.get(deger, "S7" if katman.startswith("G") else "S15")
    if katman in ("Ü", "Y2g") and (kod, ad) in GERCEK_KENAR:
        return GERCEK_KENAR[(kod, ad)]
    return SABIT.get((kod, ad), "S7")   # kalanlar: değeri başka bölgeye gitmiş sayılar


def main():
    eski = eski_kenar_bulma()
    es = {}
    for kod, yol in YOL.items():
        bgr = cv2.imread(str(REPO / yol))
        maske = murekkep_maskesi(bgr)
        es[kod] = parcalari_eslestir(eski.kenarlari_bul(maske, karakter_yuksekligi(maske)), gercek_kenarlar(kod))

    matris = defaultdict(list)   # (kod, ad) -> [(katman, sınıf)]
    olcum = json.loads((REPO / "deneyler/eslestirme/sonuclar/olcum.json").read_text(encoding="utf-8"))["krokiler"]
    for kod in YOL:
        gd = {a: d for a, d, _ in GERCEK[kod]}
        for kat, ad_kat in (("U", "Ü"), ("A", "A")):
            for x in olcum[kod][kat]["ogeler"]:
                if not x["dogru"]:
                    matris[(kod, x["ad"])].append((ad_kat, sinif(kod, x["ad"], ad_kat)))
        for i, r in enumerate(olcum[kod]["G_hane"]):
            dogrular = {x["ad"] for x in r["ogeler"] if x["dogru"]}
            degerler = {x["ad"]: x["deger"] for x in r["ogeler"] if x["ad"]}
            for ad in gd:
                if ad in dogrular:
                    continue
                d = degerler.get(ad)
                if d is None and (kod, ad, i) == ("02", "90", 2):
                    d = 96                      # konum deneyi 02 #3: 90 -> 96 okundu
                if d is None and (kod, ad) == ("02", "102"):
                    d = 162
                matris[(kod, ad)].append((f"G#{i + 1}", sinif(kod, ad, "G", d)))

    print("===== Y2 ve iskelet: sayı sayı")
    for dosya, kisa, bulunan in [("y2_karisik.json", "Y2g", False), ("y2_bulunan_karisik.json", "Y2b", True)]:
        s = json.loads((REPO / "deneyler/eslestirme/sonuclar" / dosya).read_text(encoding="utf-8"))
        for kod, v in s["krokiler"].items():
            for i, c in enumerate(v["calistirmalar"]):
                ciftler = [tuple(x) for x in c["ciftler"]]
                if bulunan:
                    ciftler = ciftleri_cevir(ciftler, es[kod])
                yanlis, fazla = degerlendir(kod, ciftler)
                print(f" {kisa} {kod} #{i + 1}: doğru {len(GERCEK[kod]) - len(yanlis)}, yanlış {yanlis}, fazla {fazla}")
                for ad in yanlis:
                    d = 162 if ad == "102" else (100 if ad == "200 sol" else None)
                    matris[(kod, ad)].append((f"{kisa}#{i + 1}", sinif(kod, ad, kisa, d)))
    isk = json.loads((KLASOR / "sonuclar/iskelet_adim0.json").read_text(encoding="utf-8"))["olculer"]
    for kod, olculer in isk.items():
        ciftler = ciftleri_cevir([(o["deger"], o["parca_id"]) for o in olculer], es[kod])
        yanlis, fazla = degerlendir(kod, ciftler)
        print(f" İsk {kod}: doğru {len(GERCEK[kod]) - len(yanlis)}, yanlış {yanlis}, fazla {fazla}")
        emin = [(o["deger"], es[kod].get(o["parca_id"], "F")) for o in olculer if o["emin"]]
        print(f"   emin: {emin}")
        for ad in yanlis:
            matris[(kod, ad)].append(("İsk", sinif(kod, ad, "İsk", 162 if ad == "102" else None)))

    print("\n===== SAYI × KATMAN (12 deneme: Ü, A, G×3, Y2g×3, Y2b×3, İsk)")
    toplam = defaultdict(lambda: [set(), 0])
    for (kod, ad), lst in sorted(matris.items()):
        print(f" {kod} {ad:<11} {len(lst):>2}/12  " + ", ".join(f"{k}:{s}" for k, s in lst))
        for _, s in lst:
            toplam[s][0].add((kod, ad))
            toplam[s][1] += 1
    print("\n===== SINIF TOPLAMI (bağlama)")
    for s, (farkli, n) in sorted(toplam.items()):
        print(f" {s:<4} farklı {len(farkli)} görülme {n}")
    print(f"toplam hatalı deneme {sum(n for _, n in toplam.values())} / {24 * 12}")


if __name__ == "__main__":
    main()
