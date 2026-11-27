"""Florence-2 (<OCR_WITH_REGION>) ve PaddleOCR ile yazı kutuları: 01–02, ham ve çizgisi silinmiş fotoğraf.

AYRI ORTAMDA çalışır (.venv-deney: torch, transformers, paddleocr; ürünün .venv'i kirlenmez). Ürün kodu
değişmez; yalnız mimarlik.on_isleme.cizgileri_sil (ürünün çizgi silmesi) kullanılır.

- Florence-2-large, fp16, GPU. Görsel modelde 768 px'e küçülüyor (rakamlar ~14 px'e iner); bu yüzden iki
  koşul: tam görsel ve bindirmeli karolar (2 sütun × 3 satır, %20 bindirme; kutular tam görsele taşınır,
  çift bulunanlar IoU > 0,5 ile tekilleşir). Üretim deterministik (ışın araması, örnekleme yok).
- PaddleOCR (PP-OCR, işlemci): tam görsel (kendi bulucusu büyük görseli kendisi ölçekliyor).
Çıktı: sonuclar/tespitler.json {model: {kroki: {koşul: [{"metin", "kutu": [x1, y1, x2, y2]}]}}} + süreler.

Çalıştırma (repo kökünden; Ollama'yı GPU'dan boşaltın: `ollama stop qwen3-vl:4b-instruct`):
    PYTHONIOENCODING=utf-8 .venv-deney/Scripts/python deneyler/konum_florence/calistir.py
"""

import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

KLASOR = Path(__file__).resolve().parent
REPO = KLASOR.parents[1]
sys.path.insert(0, str(REPO))
from mimarlik.on_isleme import cizgileri_sil  # noqa: E402

ADLAR = {"01": "01_kolay_tek_oda_180x140", "02": "02_kolay_tek_oda_300x240"}
FLORENCE = "florence-community/Florence-2-large"
GOREV = "<OCR_WITH_REGION>"


def gorseller():
    for kod, ad in ADLAR.items():
        bgr = cv2.imread(str(REPO / "ornekler" / f"{ad}.jpg"))
        yield kod, "ham", bgr
        yield kod, "çizgisiz", cizgileri_sil(bgr)


def _iou(a, b):
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    i = ix * iy
    u = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - i
    return i / u if u > 0 else 0.0


def _dortgenden_kutu(q):
    xs, ys = q[0::2], q[1::2]
    return [float(min(xs)), float(min(ys)), float(max(xs)), float(max(ys))]


class Florence:
    def __init__(self):
        import torch
        from transformers import AutoProcessor, Florence2ForConditionalGeneration
        self.torch = torch
        # transformers 5'te Microsoft'un uzak kodu çalışmıyor; aynı ağırlıkların yerleşik (trust_remote_code'suz) sürümü.
        self.model = Florence2ForConditionalGeneration.from_pretrained(FLORENCE, dtype=torch.float16).to("cuda").eval()
        self.islemci = AutoProcessor.from_pretrained(FLORENCE)

    def oku(self, bgr):
        from PIL import Image
        resim = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
        girdi = self.islemci(text=GOREV, images=resim, return_tensors="pt").to("cuda", self.torch.float16)
        with self.torch.no_grad():
            uretim = self.model.generate(input_ids=girdi["input_ids"], pixel_values=girdi["pixel_values"],
                                         max_new_tokens=1024, num_beams=3, do_sample=False)
        metin = self.islemci.batch_decode(uretim, skip_special_tokens=False)[0]
        sonuc = self.islemci.post_process_generation(metin, task=GOREV, image_size=resim.size)[GOREV]
        return [{"metin": m.replace("</s>", "").strip(), "kutu": _dortgenden_kutu(q)}
                for m, q in zip(sonuc["labels"], sonuc["quad_boxes"])]

    def karolu(self, bgr, sutun=2, satir=3, bindirme=0.2):
        yuk, gen = bgr.shape[:2]
        kw, kh = gen / (sutun - (sutun - 1) * bindirme), yuk / (satir - (satir - 1) * bindirme)
        hepsi = []
        for r in range(satir):
            for c in range(sutun):
                x0, y0 = int(c * kw * (1 - bindirme)), int(r * kh * (1 - bindirme))
                x1, y1 = min(gen, int(x0 + kw)), min(yuk, int(y0 + kh))
                for t in self.oku(bgr[y0:y1, x0:x1]):
                    k = t["kutu"]
                    hepsi.append({"metin": t["metin"], "kutu": [k[0] + x0, k[1] + y0, k[2] + x0, k[3] + y0]})
        tekil = []
        for t in sorted(hepsi, key=lambda t: -len(t["metin"])):
            if all(_iou(t["kutu"], u["kutu"]) <= 0.5 for u in tekil):
                tekil.append(t)
        return tekil


class Paddle:
    def __init__(self):
        from paddleocr import PaddleOCR
        self.ocr = PaddleOCR(lang="en", use_doc_orientation_classify=False, use_doc_unwarping=False,
                             use_textline_orientation=False, device="cpu",
                             enable_mkldnn=False)   # Windows'ta oneDNN çalıştırıcısı NotImplementedError veriyor

    def oku(self, bgr):
        sonuc = self.ocr.predict(bgr)[0]
        return [{"metin": m, "kutu": _dortgenden_kutu(np.asarray(p, float).ravel().tolist()), "guven": round(float(g), 3)}
                for m, p, g in zip(sonuc["rec_texts"], sonuc["rec_polys"], sonuc["rec_scores"])]


def main():
    cikti, sureler = {}, {}
    kurucular = [("Florence-2", Florence, {"tam": "oku", "karo 2×3": "karolu"}), ("PaddleOCR", Paddle, {"tam": "oku"})]
    for model_adi, sinif, kosullar in kurucular:
        try:
            model = sinif()
        except Exception as hata:   # bir aday kurulamazsa diğeri yine ölçülsün; hata rapora yazılır
            cikti[model_adi] = {"hata": f"{type(hata).__name__}: {hata}"}
            print(model_adi, "KURULAMADI:", hata)
            continue
        for kod, gorsel_adi, bgr in gorseller():
            for kosul, yontem in kosullar.items():
                t0 = time.perf_counter()
                tespit = getattr(model, yontem)(bgr)
                s = round(time.perf_counter() - t0, 1)
                cikti.setdefault(model_adi, {}).setdefault(kod, {})[f"{gorsel_adi}, {kosul}"] = tespit
                sureler[f"{model_adi} {kod} {gorsel_adi}, {kosul}"] = s
                print(f"{model_adi} {kod} {gorsel_adi}, {kosul}: {len(tespit)} kutu, {s} s")
        del model
    (KLASOR / "sonuclar").mkdir(exist_ok=True)
    (KLASOR / "sonuclar" / "tespitler.json").write_text(
        json.dumps({"tespitler": cikti, "sureler_s": sureler}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
