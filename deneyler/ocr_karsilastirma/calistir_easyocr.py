"""EasyOCR ile 01 ve 02 krokilerindeki sayıları okur -> sonuclar/easyocr.json

Çalıştırma (repo kökünden):
    deneyler/.venv/Scripts/python deneyler/ocr_karsilastirma/calistir_easyocr.py
"""

import json
import time
from pathlib import Path

import easyocr

from dogru_cevaplar import KROKILER
from puanlama import sayilari_al

REPO = Path(__file__).resolve().parents[2]
CIKTI = Path(__file__).resolve().parent / "sonuclar" / "easyocr.json"


def main():
    t0 = time.perf_counter()
    okuyucu = easyocr.Reader(["en"], gpu=False, verbose=False)
    yukleme_s = time.perf_counter() - t0

    sonuc = {"yontem": "EasyOCR", "surum": easyocr.__version__, "cihaz": "CPU",
             "ayarlar": {"allowlist": "0123456789", "rotation_info": [90, 180, 270]},
             "model_yukleme_s": round(yukleme_s, 2), "krokiler": {}}

    for kod, yol in KROKILER.items():
        t0 = time.perf_counter()
        bulunanlar = okuyucu.readtext(
            str(REPO / yol), allowlist="0123456789", rotation_info=[90, 180, 270]
        )
        sure = time.perf_counter() - t0
        ham = [{"metin": metin, "guven": round(float(guven), 3)} for _, metin, guven in bulunanlar]
        sonuc["krokiler"][kod] = {
            "calistirmalar": [{
                "ham": ham,
                "sayilar": sayilari_al(h["metin"] for h in ham),
                "sure_s": round(sure, 2),
            }]
        }
        print(f"{kod}: {sonuc['krokiler'][kod]['calistirmalar'][0]['sayilar']} ({sure:.1f} s)")

    CIKTI.parent.mkdir(exist_ok=True)
    CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Yazıldı: {CIKTI}")


if __name__ == "__main__":
    main()
