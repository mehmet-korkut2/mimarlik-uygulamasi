"""Defter çizgileri silinmiş fotoğrafı Qwen3-VL'e okutur (01, 02; 3'er kez) -> sonuclar/qwen_silinmis.json

Tek değişken ön işleme: istem, model ve ayarlar dünkü OCR deneyiyle birebir aynı
(ocr_karsilastirma/istem.py, num_ctx 8192, her çalıştırmadan sonra model boşaltılır).
Çalıştırma (repo kökünden): deneyler/.venv/Scripts/python deneyler/cizgi_silme/calistir.py
"""

import json
import sys
import time
from pathlib import Path

import cv2
import ollama

KLASOR = Path(__file__).resolve().parent
REPO = KLASOR.parents[1]
sys.path.insert(0, str(KLASOR.parent / "ocr_karsilastirma"))
from dogru_cevaplar import KROKILER  # noqa: E402
from istem import ISTEM, cevaptan_sayilar  # noqa: E402

from on_isleme import cizgileri_sil  # noqa: E402

MODEL, TEKRAR, NUM_CTX = "qwen3-vl:4b-instruct", 3, 8192
CIKTI = KLASOR / "sonuclar" / "qwen_silinmis.json"
GORSELLER = KLASOR / "gorseller"


def _s(ns):
    return round((ns or 0) / 1e9, 2)


def main():
    sonuc = {"yontem": "Qwen3-VL (Ollama), defter çizgileri silinmiş", "model": MODEL, "num_ctx": NUM_CTX,
             "istem": ISTEM, "krokiler": {}}
    CIKTI.parent.mkdir(exist_ok=True)
    GORSELLER.mkdir(exist_ok=True)
    son_kod = list(KROKILER)[-1]
    for kod, yol in KROKILER.items():
        t0 = time.perf_counter()
        temiz = cizgileri_sil(cv2.imread(str(REPO / yol)))
        on_isleme_s = time.perf_counter() - t0
        cv2.imwrite(str(GORSELLER / f"silinmis_{kod}.jpg"), temiz, [cv2.IMWRITE_JPEG_QUALITY, 95])
        png = cv2.imencode(".png", temiz)[1].tobytes()  # kayıpsız, modele bu gider
        calistirmalar = []
        sonuc["krokiler"][kod] = {"on_isleme_s": round(on_isleme_s, 3), "calistirmalar": calistirmalar}
        for i in range(TEKRAR):
            t0 = time.perf_counter()
            cevap = ollama.chat(model=MODEL, messages=[{"role": "user", "content": ISTEM, "images": [png]}],
                                options={"num_ctx": NUM_CTX},
                                keep_alive=0 if (i < TEKRAR - 1 or kod != son_kod) else "5m")
            sure = time.perf_counter() - t0
            calistirmalar.append({
                "ham": cevap.message.content, "sayilar": cevaptan_sayilar(cevap.message.content),
                "sure_s": round(sure, 2),
                "ollama_sureleri_s": {"toplam": _s(cevap.total_duration), "model_yukleme": _s(cevap.load_duration),
                                      "girdi_isleme": _s(cevap.prompt_eval_duration), "uretim": _s(cevap.eval_duration)},
                "token": {"girdi": cevap.prompt_eval_count, "cikti": cevap.eval_count},
            })
            CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{kod} #{i + 1}: {calistirmalar[-1]['sayilar']} ({sure:.1f} s)", flush=True)
    print(f"Yazıldı: {CIKTI}")


if __name__ == "__main__":
    main()
