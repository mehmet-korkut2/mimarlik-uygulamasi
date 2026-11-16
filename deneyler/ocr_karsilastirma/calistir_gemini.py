"""Gemini (ücretsiz katman) ile 01 ve 02'yi 3'er kez okur -> sonuclar/gemini.json

Anahtar koda yazılmaz; GEMINI_API_KEY ortam değişkeninden okunur.
Çalıştırma (repo kökünden):
    deneyler/.venv/Scripts/python deneyler/ocr_karsilastirma/calistir_gemini.py
"""

import json
import os
import sys
import time
from importlib.metadata import version
from pathlib import Path

from google import genai
from google.genai import errors, types

from dogru_cevaplar import KROKILER
from istem import ISTEM, cevaptan_sayilar

MODEL = sys.argv[1] if len(sys.argv) > 1 else "gemini-3.8-flash"
TEKRAR = 3
BEKLEME_S = 5  # ücretsiz katmanın dakikalık sınırına takılmamak için istekler arası
REPO = Path(__file__).resolve().parents[2]
CIKTI = Path(__file__).resolve().parent / "sonuclar" / f"{MODEL}.json"


YENIDEN_DENEME = 6  # 503 (yoğunluk) / 429 (sınır) için


def _iste(istemci, resim):
    """İsteği atar; geçici hatalarda artan beklemeyle yeniden dener.

    Döner: (cevap, son denemenin süresi, kaç kez yeniden denendi). Bekleme süreye dahil değil.
    """
    for deneme in range(YENIDEN_DENEME + 1):
        t0 = time.perf_counter()
        try:
            cevap = istemci.models.generate_content(model=MODEL, contents=[resim, ISTEM])
            return cevap, time.perf_counter() - t0, deneme
        except errors.APIError as hata:
            if hata.code not in (429, 503) or deneme == YENIDEN_DENEME:
                raise
            bekle = 15 * (deneme + 1)
            print(f"  {hata.code}, {bekle} s sonra yeniden denenecek", flush=True)
            time.sleep(bekle)


def main():
    anahtar = os.environ.get("GEMINI_API_KEY")
    if not anahtar:
        sys.exit("GEMINI_API_KEY ortam değişkeni ayarlı değil.")
    istemci = genai.Client(api_key=anahtar)

    sonuc = {"yontem": "Gemini", "model": MODEL, "paket": f"google-genai {version('google-genai')}",
             "katman": "ücretsiz", "istem": ISTEM, "krokiler": {}}

    CIKTI.parent.mkdir(exist_ok=True)
    for kod, yol in KROKILER.items():
        resim = types.Part.from_bytes(data=(REPO / yol).read_bytes(), mime_type="image/jpeg")
        calistirmalar = []
        sonuc["krokiler"][kod] = {"calistirmalar": calistirmalar}
        for i in range(TEKRAR):
            cevap, sure, yeniden = _iste(istemci, resim)
            kullanim = cevap.usage_metadata
            calistirmalar.append({
                "ham": cevap.text,
                "sayilar": cevaptan_sayilar(cevap.text),
                "sure_s": round(sure, 2),
                "yeniden_deneme": yeniden,
                "token": {
                    "girdi": kullanim.prompt_token_count,
                    "cikti": kullanim.candidates_token_count,
                    "dusunme": kullanim.thoughts_token_count,
                },
            })
            # Her istekten sonra yaz: yarıda kesilirse elde edilenler kaybolmasın.
            CIKTI.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{kod} #{i + 1}: {calistirmalar[-1]['sayilar']} ({sure:.1f} s)", flush=True)
            time.sleep(BEKLEME_S)

    print(f"Yazıldı: {CIKTI}")


if __name__ == "__main__":
    main()
