"""Ollama + Qwen3-VL ile 01 ve 02'yi 3'er kez okur -> sonuclar/qwen.json

Önce: Ollama çalışıyor olmalı ve model indirilmiş olmalı:
    ollama pull qwen3-vl:4b-instruct
Çalıştırma (repo kökünden):
    deneyler/.venv/Scripts/python deneyler/ocr_karsilastirma/calistir_qwen.py [model]
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import ollama

from dogru_cevaplar import KROKILER
from istem import ISTEM, cevaptan_sayilar

MODEL = sys.argv[1] if len(sys.argv) > 1 else "qwen3-vl:4b-instruct"
TEKRAR = 3
NUM_CTX = 8192  # fotoğraf ~2.300 görüntü token'ı; kesilmesin diye pay bırakıldı
REPO = Path(__file__).resolve().parents[2]
CIKTI = Path(__file__).resolve().parent / "sonuclar" / f"qwen_{MODEL.split(':')[-1]}.json"


def _ns_to_s(ns):
    return round((ns or 0) / 1e9, 2)


def main():
    sonuc = {"yontem": "Qwen3-VL (Ollama)", "model": MODEL, "num_ctx": NUM_CTX,
             "istem": ISTEM, "krokiler": {}}

    for kod, yol in KROKILER.items():
        calistirmalar = []
        for i in range(TEKRAR):
            t0 = time.perf_counter()
            cevap = ollama.chat(
                model=MODEL,
                messages=[{"role": "user", "content": ISTEM, "images": [str(REPO / yol)]}],
                options={"num_ctx": NUM_CTX},
                # Her çalıştırmadan sonra modeli boşalt: yoksa 2. ve 3. çalıştırma fotoğrafı
                # önbellekten alır, süre gerçekçi olmaz (yükleme süresi ayrıca ölçülüyor).
                keep_alive=0 if i < TEKRAR - 1 or kod != list(KROKILER)[-1] else "5m",
            )
            sure = time.perf_counter() - t0
            metin = cevap.message.content
            calistirmalar.append({
                "ham": metin,
                "sayilar": cevaptan_sayilar(metin),
                "sure_s": round(sure, 2),
                "ollama_sureleri_s": {
                    "toplam": _ns_to_s(cevap.total_duration),
                    "model_yukleme": _ns_to_s(cevap.load_duration),
                    "girdi_isleme": _ns_to_s(cevap.prompt_eval_duration),
                    "uretim": _ns_to_s(cevap.eval_duration),
                },
                "token": {"girdi": cevap.prompt_eval_count, "cikti": cevap.eval_count},
            })
            print(f"{kod} #{i + 1}: {calistirmalar[-1]['sayilar']} ({sure:.1f} s)")
        sonuc["krokiler"][kod] = {"calistirmalar": calistirmalar}

    # Modelin ne kadarının GPU'da, ne kadarının CPU'da çalıştığı (ör. "25%/75% CPU/GPU").
    sonuc["ollama_ps"] = subprocess.run(["ollama", "ps"], capture_output=True, text=True).stdout

    CIKTI.parent.mkdir(exist_ok=True)
    CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(sonuc["ollama_ps"])
    print(f"Yazıldı: {CIKTI}")


if __name__ == "__main__":
    main()
