"""Set-of-Mark: bölge bulucunun her bölgesine R etiketi, Qwen'e "her R'de hangi sayı yazıyor?" (ürün kodu değişmez).

Amaç (deneyler/sekil_01/RAPOR.md, H1): değeri doğrudan bölgeye bağlamak. Qwen tam görseli görür (bağlam
korunur); değer, kutu koordinatı üzerinden değil etiket üzerinden bölgeye gider.

- Bölgeler: kenar bulma 1. geçiş + bolge_bulma (deneyler/deger_atama ile aynı).
- Görsel: ürünle aynı, defter çizgileri silinmiş fotoğraf. Her bölgenin çevresine 4 px pay bırakılarak ince kırmızı
  çerçeve; yanına, mürekkebe ve başka bölgelere binmeyen ilk yere "R<n>" etiketi. Numaralar karışık (tohum 17).
- 01 ve 02, 3'er çalıştırma (model sıcaklığı ürünle aynı). Ham cevaplar sonuclar/som.json'a; etiketli görseller
  gorseller/ altına (.gitignore: fotoğraf sayılır).

Çalıştırma (repo kökünden, Ollama açık): PYTHONIOENCODING=utf-8 .venv/Scripts/python deneyler/set_of_mark/calistir.py
"""

import json
import random
import sys
import time
from pathlib import Path

import cv2
import numpy as np

KLASOR = Path(__file__).resolve().parent
REPO = KLASOR.parents[1]
sys.path.insert(0, str(REPO))
from mimarlik import okuma  # noqa: E402
from mimarlik.bolge_bulma import bolgeleri_bul  # noqa: E402
from mimarlik.kenar_bulma import kenarlari_bul  # noqa: E402
from mimarlik.on_isleme import cizgileri_sil, karakter_yuksekligi, murekkep_maskesi  # noqa: E402

ADLAR = {"01": "01_kolay_tek_oda_180x140", "02": "02_kolay_tek_oda_300x240"}
CALISTIRMA = 3
TOHUM = 17
PAY = 4
KIRMIZI = (0, 0, 230)
ISTEM = (
    "Bu, elle çizilmiş bir mimari kroki. Bazı el yazılarının çevresine ince kırmızı çerçeve çizildi ve her "
    "çerçevenin yanına R1, R2… diye bir etiket kondu. Her R etiketinin çerçevesinin İÇİNDEKİ el yazısı ölçü "
    "sayısını (cm) oku. Çerçevenin içinde sayı yoksa ya da okuyamıyorsan null yaz; tahmin etme. "
    'Sadece bir JSON nesnesi döndür, başka bir şey yazma. Biçim: {"R1": 180, "R2": null}'
)


def bolgeler(ad):
    bgr = cv2.imread(str(REPO / "ornekler" / f"{ad}.jpg"))
    maske = murekkep_maskesi(bgr)
    h = karakter_yuksekligi(maske)
    return bgr, maske, h, bolgeleri_bul(maske, kenarlari_bul(maske, h), h)


def _kesisir(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def etiketli_gorsel(bgr, maske, bolgelist):
    """Döner: (görsel, {"R3": bölge kutusu}). Etiket, çerçevenin dışında mürekkebe ve diğer çerçevelere binmeyen ilk yere."""
    resim = cizgileri_sil(bgr).copy()
    yuk, gen = maske.shape[:2]
    numaralar = list(range(1, len(bolgelist) + 1))
    random.Random(TOHUM).shuffle(numaralar)
    font, olcek, kal = cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
    cerceveler = [(int(b.kutu[0]) - PAY, int(b.kutu[1]) - PAY, int(b.kutu[2]) + PAY, int(b.kutu[3]) + PAY)
                  for b in bolgelist]
    dolu = list(cerceveler)
    eslem = {}
    for n, b, c in zip(numaralar, bolgelist, cerceveler):
        etiket = f"R{n}"
        (g, y), taban = cv2.getTextSize(etiket, font, olcek, kal)
        w, hh = g + 6, y + taban + 6
        x1, y1, x2, y2 = c
        adaylar = [(x2 + 3, y1), (x1 - w - 3, y1), (x1, y1 - hh - 3), (x1, y2 + 3),
                   (x2 + 3, y2 - hh), (x1 - w - 3, y2 - hh), (x2 - w, y1 - hh - 3), (x2 - w, y2 + 3)]
        en_iyi = None
        for ax, ay in adaylar:
            r = (ax, ay, ax + w, ay + hh)
            if r[0] < 0 or r[1] < 0 or r[2] >= gen or r[3] >= yuk:
                continue
            murekkep = int(np.count_nonzero(maske[r[1]:r[3], r[0]:r[2]]))
            carpisma = sum(_kesisir(r, d) for d in dolu)
            puan = (carpisma, murekkep)
            if en_iyi is None or puan < en_iyi[0]:
                en_iyi = (puan, r)
        r = en_iyi[1]
        dolu.append(r)
        cv2.rectangle(resim, (x1, y1), (x2, y2), KIRMIZI, 1)
        cv2.rectangle(resim, (r[0], r[1]), (r[2], r[3]), (255, 255, 255), -1)
        cv2.rectangle(resim, (r[0], r[1]), (r[2], r[3]), KIRMIZI, 1)
        cv2.putText(resim, etiket, (r[0] + 3, r[1] + 3 + y), font, olcek, KIRMIZI, kal, cv2.LINE_AA)
        eslem[etiket] = [round(float(v), 1) for v in b.kutu]
    return resim, eslem


def main():
    (KLASOR / "gorseller").mkdir(exist_ok=True)
    sonuc = {"istem": ISTEM, "model": okuma.MODEL, "krokiler": {}}
    for kod, ad in ADLAR.items():
        bgr, maske, h, bl = bolgeler(ad)
        resim, eslem = etiketli_gorsel(bgr, maske, bl)
        cv2.imwrite(str(KLASOR / "gorseller" / f"{kod}_som.png"), resim)
        k = sonuc["krokiler"][kod] = {"h": round(h, 1), "eslem": eslem, "calistirmalar": []}
        for n in range(1, CALISTIRMA + 1):
            t0 = time.perf_counter()
            ham = okuma.qwen_sor(ISTEM, okuma.png(resim))
            k["calistirmalar"].append({"ham": ham, "sure_s": round(time.perf_counter() - t0, 1)})
            print(f"{kod} #{n}: {time.perf_counter() - t0:.0f} s  {ham[:160]!r}")
    (KLASOR / "sonuclar").mkdir(exist_ok=True)
    (KLASOR / "sonuclar" / "som.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
