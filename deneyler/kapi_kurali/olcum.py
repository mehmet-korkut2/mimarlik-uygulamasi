"""Kapı boşluğu kuralının (3. adım) 01–02'deki etkisi: kontur, bağlama doğruluğu, "emin" isabeti, kapanma.

Girdi: `python -m mimarlik.kroki ... --okuma output/<ad>_qwen.json` çıktıları (`output/`, .gitignore'da):
  adim2      : S3 = B + X kuralı, kapı kuralı yok (Y2 bir kez yeniden soruldu)
  adim3*     : + kapı kuralı (her klasörde Y2 yeniden soruldu: 3 örnek)
Bulunan parçalar, JSON'daki parça geometrisiyle (ham.parcalar_geometri) gerçek parçalara eşlenir (uçlar ≤ 25 px).
Ayrıca "ideal kapanma": gerçek sayılar gerçek dış hatta (S1 toplamı, S3 = B) olsaydı kapanma farkı.

Çalıştırma (repo kökünden): PYTHONIOENCODING=utf-8 .venv/Scripts/python deneyler/kapi_kurali/olcum.py
"""

import json
import sys
from collections import Counter
from pathlib import Path

KLASOR = Path(__file__).resolve().parent
REPO = KLASOR.parents[1]
sys.path.insert(0, str(REPO / "deneyler" / "eslestirme"))
sys.path.insert(0, str(REPO / "deneyler" / "bul_kes_okut"))
from gercek_eslestirme import ESLESME  # noqa: E402
from konumlar import GERCEK  # noqa: E402
from puanlama_eslestirme import gercek_kenarlar, parcalari_eslestir  # noqa: E402

from mimarlik.eslestirme import Kenar, KenarSonucu, Parca  # noqa: E402

ADLAR = {"01": "01_kolay_tek_oda_180x140", "02": "02_kolay_tek_oda_300x240"}
KLASORLER = ["adim2", "adim3", "adim3_2", "adim3_3"]

# Gerçek dış hat (mimarın cevaplarından sonra): kenar sırası, yön (x, y; görüntüde y aşağı), sayıları.
# 02: X'li parçalar (K1.1, K10.2) iptal; küçük odanın duvarları (K11, K12) dış hatta.
GERCEK_DIS_HAT = {
    "01": [((1, 0), ["180"]), ((0, 1), ["50"]), ((1, 0), ["40"]), ((0, 1), ["120 sağ"]), ((-1, 0), ["140"]),
           ((0, -1), ["10", "90", "15"]), ((-1, 0), ["120 sol"]), ((0, -1), ["108"])],
    "02": [((1, 0), ["300"]), ((0, 1), ["45 üst sol"]), ((1, 0), ["45 üst sağ"]), ((0, 1), ["240"]),
           ((-1, 0), ["200 alt"]), ((0, -1), ["40 sağ alt"]), ((-1, 0), ["40 orta"]), ((0, 1), ["40 sol alt"]),
           ((-1, 0), ["102"]), ((0, -1), ["200 sol"]), ((1, 0), ["45 alt"]), ((0, -1), ["15", "90", "40 üst"])],
}


def ideal_kapanma(kod):
    deger = {a: d for a, d, _ in GERCEK[kod]}
    x = sum(yon[0] * sum(deger[a] for a in adlar) for yon, adlar in GERCEK_DIS_HAT[kod])
    y = sum(yon[1] * sum(deger[a] for a in adlar) for yon, adlar in GERCEK_DIS_HAT[kod])
    return x, y


def _eslem(geometri, kod):
    """Bulunan parça id -> gerçek parça id (uçlar ≤ 25 px)."""
    parcalar = [Parca(pid, pid.split(".")[0], "duvar", tuple(a), tuple(b)) for pid, a, b in geometri.values()]
    bulunan = KenarSonucu(0.0, tuple(Kenar(p.id, "yatay", (p,), True) for p in parcalar), (), ())
    return parcalari_eslestir(bulunan, gercek_kenarlar(kod))


def degerlendir(kod, ciftler):
    kalan, yanlis = Counter(ciftler), []
    for ad, deger, _ in GERCEK[kod]:
        c = (deger, ESLESME[kod][ad])
        if kalan[c] > 0:
            kalan[c] -= 1
        else:
            yanlis.append(ad)
    return yanlis


def olc(kod, klasor):
    r = json.loads((REPO / "output" / klasor / f"{ADLAR[kod]}.json").read_text(encoding="utf-8"))
    es = _eslem(r["ham"]["parcalar_geometri"], kod)
    kontur_parcalari = [p["parca_id"] for k in r["kenarlar"] for p in k["parcalar"]]
    ciftler = [(o["deger"], es.get(o["parca_id"], "F")) for o in r["olculer"] if o["parca_id"]]
    yanlis = degerlendir(kod, ciftler)
    emin = [(o["deger"], es.get(o["parca_id"], "F")) for o in r["olculer"] if o["emin"]]
    kalan = Counter((d, ESLESME[kod][a]) for a, d, _ in GERCEK[kod])
    emin_dogru = 0
    for c in emin:
        if kalan[c] > 0:
            kalan[c] -= 1
            emin_dogru += 1
    return {"kontur": len(r["kenarlar"]),
            "kontur_eslesen": sum(p in es for p in kontur_parcalari), "kontur_parca": len(kontur_parcalari),
            "kapilar": [(k["kaynak"], k["deger"]) for k in r.get("kapilar", [])],
            "dogru": len(GERCEK[kod]) - len(yanlis), "yanlis": yanlis,
            "emin": len(emin), "emin_dogru": emin_dogru,
            "kapanma": {e: v["fark_cm"] for e, v in r["kapanma"].items()}}


def main():
    sonuc = {"ideal_kapanma": {kod: ideal_kapanma(kod) for kod in ADLAR}, "olcumler": {}}
    for kod in ADLAR:
        x, y = sonuc["ideal_kapanma"][kod]
        print(f"===== {kod}  (ideal kapanma: yatay {abs(x)}, dikey {abs(y)} cm)")
        for klasor in KLASORLER:
            if not (REPO / "output" / klasor / f"{ADLAR[kod]}.json").exists():
                continue
            o = olc(kod, klasor)
            sonuc["olcumler"].setdefault(kod, {})[klasor] = o
            print(f" {klasor:<8} kontur {o['kontur']:>2} kenar (parça {o['kontur_eslesen']}/{o['kontur_parca']} gerçeğe "
                  f"eşlendi) · kapı {o['kapilar']} · bağlama {o['dogru']}/{len(GERCEK[kod])} · emin "
                  f"{o['emin_dogru']}/{o['emin']} doğru · kapanma {o['kapanma']}")
            print(f"           yanlış: {o['yanlis']}")
    (KLASOR / "sonuclar").mkdir(exist_ok=True)
    (KLASOR / "sonuclar" / "olcum.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
