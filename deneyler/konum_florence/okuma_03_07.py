"""03–07 okuma: Florence-2 (1 kez, deterministik) ve Qwen3-VL (3 kez, ürünün istemi). Yalnız ham cevaplar kaydedilir;
puanlama ayrı (`puanla_03_07.py`), böylece doğru cevap listesi düzelince modeller yeniden çalıştırılmaz.

Görsel: ham fotoğraf (01–02 deneyinde Florence için en iyi koşul). 03–07 plana çevrilmez.

Çalıştırma (repo kökünden, sırayla; ikisi 4 GB GPU'ya birlikte sığmaz):
    PYTHONIOENCODING=utf-8 .venv-deney/Scripts/python deneyler/konum_florence/okuma_03_07.py florence
    ollama stop qwen3-vl:4b-instruct  (Florence'ten önce, gerekirse)
    PYTHONIOENCODING=utf-8 .venv/Scripts/python deneyler/konum_florence/okuma_03_07.py qwen
Çıktı: sonuclar/okuma_03_07.json {"florence": {kod: [{"metinler": [...], "sure_s"}]},
                                  "qwen": {kod: [{"ham", "etiketler": [...], "sure_s"}] × 3}}
"""

import json
import sys
import time
from pathlib import Path

import cv2

KLASOR = Path(__file__).resolve().parent
REPO = KLASOR.parents[1]
sys.path[:0] = [str(REPO), str(KLASOR)]

ADLAR = {"03": "03_orta_egik_duvar", "04": "04_orta_oda2_wc", "05": "05_zor_oda3_balkon",
         "06": "06_zor_salon_balkon", "07": "07_zor_sauna_yan_cekilmis"}
CIKTI = KLASOR / "sonuclar" / "okuma_03_07.json"
QWEN_TEKRAR = 3
QWEN_SINIR = 2500   # token; 06'nın 54 sayısı ~1400 token tutar


def gorsel(kod):
    return cv2.imread(str(REPO / "ornekler" / f"{ADLAR[kod]}.jpg"))


def florence():
    from calistir import Florence
    model, sonuc = Florence(), {}
    for kod in ADLAR:
        t0 = time.perf_counter()
        tespit = model.oku(gorsel(kod))
        s = round(time.perf_counter() - t0, 1)
        sonuc[kod] = [{"metinler": [t["metin"] for t in tespit], "kutular": [t["kutu"] for t in tespit], "sure_s": s}]
        print(f"florence {kod}: {len(tespit)} metin, {s} s", flush=True)
    return sonuc


def qwen(kaydet):
    """Ürünün istemi ve modeli; tek fark cevap sınırı (QWEN_SINIR token). Sınırsız ilk denemede bazı çağrılar 27–28 dk
    sürdü (model kendini tekrarlayıp bağlam sonuna kadar yazıyor). Kesik cevapta tamamlanmış nesneler kurtarılır."""
    import ollama
    from mimarlik import okuma
    sonuc = {}
    for kod in ADLAR:
        png = okuma.png(gorsel(kod))
        for n in range(1, QWEN_TEKRAR + 1):
            t0 = time.perf_counter()
            cevap = ollama.chat(model=okuma.MODEL,
                                messages=[{"role": "user", "content": okuma.ISTEM_SAYILAR, "images": [png]}],
                                options={"num_ctx": okuma.NUM_CTX, "num_predict": QWEN_SINIR}, keep_alive="5m")
            ham = cevap.message.content or ""
            s = round(time.perf_counter() - t0, 1)
            etiketler = [str(o.get("label")) for o in okuma._json_nesneleri(ham) if o.get("label") is not None]
            kesik = getattr(cevap, "done_reason", None) == "length"
            sonuc.setdefault(kod, []).append({"ham": ham, "etiketler": etiketler, "sure_s": s, "kesik": kesik})
            print(f"qwen {kod} #{n}: {len(etiketler)} etiket, {s} s{', KESİK' if kesik else ''}", flush=True)
            kaydet(sonuc)
    return sonuc


def main():
    model = sys.argv[1]
    veri = json.loads(CIKTI.read_text(encoding="utf-8")) if CIKTI.exists() else {}
    CIKTI.parent.mkdir(exist_ok=True)

    def kaydet(kismi):
        veri[model] = kismi
        CIKTI.write_text(json.dumps(veri, ensure_ascii=False, indent=1), encoding="utf-8")

    kaydet(florence() if model == "florence" else qwen(kaydet))


if __name__ == "__main__":
    main()
