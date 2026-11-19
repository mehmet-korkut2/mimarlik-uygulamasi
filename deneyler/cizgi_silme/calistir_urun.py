"""Ürünün kullandığı koşulu ölçer: çizgileri silinmiş fotoğraf + KONUMLU istem (01, 02; 3'er kez).

`python -m mimarlik.kroki`'nin Qwen-1 adımıyla birebir aynı kod: mimarlik.on_isleme.cizgileri_sil,
mimarlik.okuma.ISTEM_SAYILAR / png / sayilari_ayristir. Puanlanan, ürünün eline geçen değerler
(kutusu bozuk öğeyi ürün de atar; atılanlar ayrıca sayılır). Puanlama dünkü OCR deneyiyle aynı.
Süre ölçümü önceki deneylerle karşılaştırılabilsin diye model her çalıştırmadan sonra boşaltılır.
Çalıştırma (repo kökünden): PYTHONIOENCODING=utf-8 deneyler/.venv/Scripts/python deneyler/cizgi_silme/calistir_urun.py
-> sonuclar/qwen_urun.json
"""

import json
import sys
import time
from pathlib import Path

import cv2
import ollama

KLASOR = Path(__file__).resolve().parent
REPO = KLASOR.parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(KLASOR.parent / "ocr_karsilastirma"))
from dogru_cevaplar import DOGRU, KROKILER  # noqa: E402
from puanlama import puanla  # noqa: E402

from mimarlik import okuma  # noqa: E402
from mimarlik.on_isleme import cizgileri_sil  # noqa: E402

TEKRAR = 3
CIKTI = KLASOR / "sonuclar" / "qwen_urun.json"


def main():
    sonuc = {"yontem": "Ürün koşulu: çizgileri silinmiş fotoğraf + konumlu istem (mimarlik.okuma)",
             "model": okuma.MODEL, "num_ctx": okuma.NUM_CTX, "istem": okuma.ISTEM_SAYILAR, "krokiler": {}}
    son_kod = list(KROKILER)[-1]
    for kod, yol in KROKILER.items():
        bgr = cv2.imread(str(REPO / yol))
        png = okuma.png(cizgileri_sil(bgr))
        calistirmalar = []
        sonuc["krokiler"][kod] = {"calistirmalar": calistirmalar}
        for i in range(TEKRAR):
            t0 = time.perf_counter()
            cevap = ollama.chat(model=okuma.MODEL,
                                messages=[{"role": "user", "content": okuma.ISTEM_SAYILAR, "images": [png]}],
                                options={"num_ctx": okuma.NUM_CTX},
                                keep_alive=0 if (i < TEKRAR - 1 or kod != son_kod) else "5m")
            sure = time.perf_counter() - t0
            ham = cevap.message.content or ""
            sayilar = [d for d, _ in okuma.sayilari_ayristir(ham, bgr.shape[1], bgr.shape[0])]
            p = puanla(sayilar, DOGRU[kod])
            calistirmalar.append({"ham": ham, "sayilar": sayilar, "puan": p, "sure_s": round(sure, 2),
                                  "atilan_oge": len(okuma._json_nesneleri(ham)) - len(sayilar)})
            CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
            print(f"{kod} #{i + 1}: doğru {p['dogru']}/{len(DOGRU[kod])}, fazla {p['fazla']}, "
                  f"atılan {calistirmalar[-1]['atilan_oge']} ({sure:.0f} s)", flush=True)
    for i in range(TEKRAR):
        k = [sonuc["krokiler"][kod]["calistirmalar"][i]["puan"] for kod in KROKILER]
        print(f"Çalıştırma {i + 1}: toplam doğru {sum(x['dogru'] for x in k)}/24, fazla {sum(x['fazla'] for x in k)}")
    print(f"Yazıldı: {CIKTI}")


if __name__ == "__main__":
    main()
