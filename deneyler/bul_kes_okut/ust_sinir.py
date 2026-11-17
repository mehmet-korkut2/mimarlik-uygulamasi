"""Üst sınır: gerçek kutulardan kes -> Qwen'e tek tek okut (3 çalıştırma) -> sonuclar/ust_sinir.json

Bulucu hatası olmadan, kesitten okumanın ne kadar iyi olduğunu ölçer.
Model bir çalıştırma boyunca bellekte kalır; her çalıştırmanın sonunda boşaltılır, böylece her
çalıştırmanın ilk kesiti model yükleme süresini içerir (ayrıca raporlanır).
Çalıştırma (repo kökünden): deneyler/.venv/Scripts/python deneyler/bul_kes_okut/ust_sinir.py
"""

import json
import time

from PIL import Image, ImageDraw

from kes_okut import ISTEM, MODEL, NUM_CTX, kes, oku
from konumlar import GERCEK
from ortak import GORSELLER, KROKILER, REPO, SONUCLAR, _font

TEKRAR = 3
CIKTI = SONUCLAR / "ust_sinir.json"


def kesit_paftasi(kesitler, cikti, sutun=5, boy=260):
    """Kesitleri ızgara halinde, altlarına 'beklenen -> okunan' yazarak tek görsele dizer."""
    satir = (len(kesitler) + sutun - 1) // sutun
    pafta = Image.new("RGB", (sutun * boy, satir * (boy + 40)), "white")
    kalem, font = ImageDraw.Draw(pafta), _font(24)
    for i, (resim, yazi, dogru_mu) in enumerate(kesitler):
        k = resim.copy()
        k.thumbnail((boy - 10, boy - 10))
        x, y = (i % sutun) * boy, (i // sutun) * (boy + 40)
        pafta.paste(k, (x + 5, y + 5))
        kalem.text((x + 5, y + boy - 2), yazi, fill=(0, 140, 0) if dogru_mu else (220, 0, 0), font=font)
    cikti.parent.mkdir(parents=True, exist_ok=True)
    pafta.save(cikti, quality=90)


def main():
    sonuc = {"deney": "üst sınır: gerçek kutulardan kesit", "model": MODEL, "num_ctx": NUM_CTX,
             "istem": ISTEM, "krokiler": {}}
    SONUCLAR.mkdir(exist_ok=True)
    son = (list(GERCEK)[-1], TEKRAR - 1)
    for kod, kutular in GERCEK.items():
        resim = Image.open(REPO / KROKILER[kod]).convert("RGB")
        calistirmalar = []
        sonuc["krokiler"][kod] = {"calistirmalar": calistirmalar}
        for i in range(TEKRAR):
            t0 = time.perf_counter()
            okumalar, pafta = [], []
            for j, (ad, beklenen, kutu) in enumerate(kutular):
                kesit = kes(resim, kutu)
                bosalt = j == len(kutular) - 1 and (kod, i) != son
                deger, ham, sure, sureler = oku(kesit, keep_alive=0 if bosalt else "5m")
                okumalar.append({"ad": ad, "beklenen": beklenen, "okunan": deger, "ham": ham,
                                 "sure_s": sure, "ollama": sureler, "kesit_boyu": kesit.size})
                pafta.append((kesit, f"{beklenen} -> {deger}", deger == beklenen))
            toplam = time.perf_counter() - t0
            calistirmalar.append({"okumalar": okumalar, "sayilar": [o["okunan"] for o in okumalar if o["okunan"]],
                                  "toplam_sure_s": round(toplam, 2)})
            CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
            hatalar = [f"{o['ad']}: {o['beklenen']}->{o['okunan']}" for o in okumalar if o["okunan"] != o["beklenen"]]
            print(f"{kod} #{i + 1}: {sum(o['okunan'] == o['beklenen'] for o in okumalar)}/{len(okumalar)} "
                  f"({toplam:.1f} s) hatalar: {hatalar or '—'}", flush=True)
            kesit_paftasi(pafta, GORSELLER / f"ust_sinir_{kod}_calistirma{i + 1}.jpg")
    print(f"Yazıldı: {CIKTI}")


if __name__ == "__main__":
    main()
