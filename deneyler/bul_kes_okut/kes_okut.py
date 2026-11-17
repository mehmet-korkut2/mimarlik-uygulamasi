"""Bölgeyi genişlet -> kes -> büyüt -> Qwen'e "bu sayı ne?" diye sor."""

import io
import time

from ortak import sayilari_al

MODEL = "qwen3-vl:4b-instruct"
NUM_CTX = 8192  # dünkü deneylerle aynı (karşılaştırma adil olsun)
PAY_ORANI, EN_AZ_PAY = 0.5, 15  # her yöne: kutu yüksekliğinin yarısı, en az 15 px
KISA_KENAR = 224  # küçük kesitler bu boya büyütülür

ISTEM = (
    "Bu görüntü, elle çizilmiş bir mimari krokiden kesilmiş küçük bir parça. "
    "İçinde el yazısıyla yazılmış bir ölçü sayısı (cm) var mı? "
    "Varsa sadece o sayıyı yaz (ör. 120). Sayı yoksa ya da okunamıyorsa sadece YOK yaz. "
    "Kenarlarda yarım kalmış başka yazılar varsa onları dikkate alma."
)


def genislet(kutu, genislik, yukseklik, oran=PAY_ORANI, en_az=EN_AZ_PAY):
    """Kutuyu her yöne max(oran*kutu yüksekliği, en_az) kadar büyütür, fotoğraf sınırında kırpar."""
    x1, y1, x2, y2 = kutu
    pay = max(round(oran * (y2 - y1)), en_az)
    return (max(0, x1 - pay), max(0, y1 - pay), min(genislik, x2 + pay), min(yukseklik, y2 + pay))


def kes(resim, kutu, kisa_kenar=KISA_KENAR):
    """Genişletilmiş bölgeyi keser; kısa kenarı kisa_kenar'dan küçükse oranı koruyarak büyütür."""
    kesit = resim.crop(genislet(kutu, *resim.size))
    g, y = kesit.size
    if min(g, y) < kisa_kenar:
        k = kisa_kenar / min(g, y)
        kesit = kesit.resize((round(g * k), round(y * k)), resample=3)  # 3 = BICUBIC
    return kesit


def cevaptan_deger(metin):
    """Cevaptaki ilk 1–9999 sayısı; yoksa (ör. "YOK") None."""
    sayilar = sayilari_al([metin or ""])
    return sayilar[0] if sayilar else None


def oku(kesit, keep_alive="5m"):
    """Kesiti Qwen'e okutur. Döner: (değer|None, ham cevap, süre_s, ollama süreleri)."""
    import ollama  # testler Ollama'sız çalışsın

    tampon = io.BytesIO()
    kesit.save(tampon, format="PNG")
    t0 = time.perf_counter()
    cevap = ollama.chat(model=MODEL, messages=[{"role": "user", "content": ISTEM, "images": [tampon.getvalue()]}],
                        options={"num_ctx": NUM_CTX}, keep_alive=keep_alive)
    sure = time.perf_counter() - t0
    sureler = {"model_yukleme": round((cevap.load_duration or 0) / 1e9, 2),
               "girdi_isleme": round((cevap.prompt_eval_duration or 0) / 1e9, 2),
               "uretim": round((cevap.eval_duration or 0) / 1e9, 2),
               "girdi_token": cevap.prompt_eval_count}
    return cevaptan_deger(cevap.message.content), cevap.message.content, round(sure, 2), sureler
