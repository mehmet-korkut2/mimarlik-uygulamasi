"""Qwen3-VL'den 01 ve 02'deki sayıları kutularıyla 3'er kez ister -> sonuclar/qwen_konum.json

Koşullar dünkü OCR deneyiyle aynı (model, num_ctx, her çalıştırmadan sonra modeli boşaltma),
böylece okuma doğruluğu deneyler/ocr_karsilastirma/sonuclar/qwen_4b-instruct.json ile karşılaştırılabilir.
Çalıştırma (repo kökünden): deneyler/.venv/Scripts/python deneyler/konum_deneyi/calistir.py
"""

import json
import subprocess
import time
from pathlib import Path

import ollama

from konum_istem import ISTEM, cevaptan_kutular
from dogru_cevaplar import KROKILER  # ocr_karsilastirma'dan (konum_istem.py yolu ekledi)

MODEL = "qwen3-vl:4b-instruct"
TEKRAR = 3
NUM_CTX = 8192
OLLAMA = Path.home() / "AppData/Local/Programs/Ollama/ollama.exe"
KLASOR = Path(__file__).resolve().parent
REPO = KLASOR.parents[1]
CIKTI = KLASOR / "sonuclar" / "qwen_konum.json"


def _s(ns):
    return round((ns or 0) / 1e9, 2)


def main():
    sonuc = {"yontem": "Qwen3-VL (Ollama), sayı + kutu", "model": MODEL, "num_ctx": NUM_CTX,
             "koordinat": "0-1000 oranlı (x1, y1, x2, y2)", "istem": ISTEM, "krokiler": {}}
    CIKTI.parent.mkdir(exist_ok=True)
    son_kod = list(KROKILER)[-1]
    for kod, yol in KROKILER.items():
        calistirmalar = []
        sonuc["krokiler"][kod] = {"calistirmalar": calistirmalar}
        for i in range(TEKRAR):
            t0 = time.perf_counter()
            cevap = ollama.chat(
                model=MODEL,
                messages=[{"role": "user", "content": ISTEM, "images": [str(REPO / yol)]}],
                options={"num_ctx": NUM_CTX},
                # Son çalıştırma hariç modeli boşalt (önbellek süreyi yanıltmasın); sonda `ollama ps` için tut.
                keep_alive=0 if (i < TEKRAR - 1 or kod != son_kod) else "5m",
            )
            sure = time.perf_counter() - t0
            kutular = cevaptan_kutular(cevap.message.content)
            calistirmalar.append({
                "ham": cevap.message.content,
                "kutular": kutular,
                "sayilar": [k["deger"] for k in kutular if k["deger"] is not None],
                "sure_s": round(sure, 2),
                "ollama_sureleri_s": {"toplam": _s(cevap.total_duration), "model_yukleme": _s(cevap.load_duration),
                                      "girdi_isleme": _s(cevap.prompt_eval_duration),
                                      "uretim": _s(cevap.eval_duration)},
                "token": {"girdi": cevap.prompt_eval_count, "cikti": cevap.eval_count},
            })
            CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{kod} #{i + 1}: {calistirmalar[-1]['sayilar']} ({sure:.1f} s)", flush=True)

    sonuc["ollama_ps"] = subprocess.run([str(OLLAMA), "ps"], capture_output=True, text=True).stdout
    CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(sonuc["ollama_ps"], f"Yazıldı: {CIKTI}", sep="\n")


if __name__ == "__main__":
    main()
