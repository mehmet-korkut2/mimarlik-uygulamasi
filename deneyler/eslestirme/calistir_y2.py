"""Y2: gerçek parçaları P1, P2… diye fotoğrafa çizip Qwen'e "her parçanın ölçüsü ne?" diye sorar.

Tek seferlik karşılaştırma (tasarım 7.3): 01 ve 02, 3'er çalıştırma -> sonuclar/y2.json
Girdi görseli (çizgileri silinmiş fotoğraf + etiketler) gorseller/y2_girdi_*.jpg (.gitignore'da).
Çalıştırma (repo kökünden): PYTHONIOENCODING=utf-8 deneyler/.venv/Scripts/python deneyler/eslestirme/calistir_y2.py [bulunan] [karisik]

"bulunan": gerçek parçalar yerine mimarlik.kenar_bulma'nın bulduğu parçalar çizilir (gerçekçi Y2). Çiftler
bulunan parça kimliğiyle kaydedilir; olcum.py bunları ara katmandaki gibi gerçek parçalara eşleyip puanlar.

"karisik": P numaraları kontur sırası yerine sabit tohumlu rastgele sırayla verilir (kontrol: model
konuma mı bakıyor, yoksa sayıları kâğıttaki sırayla listeleyip numaralarla mı eşliyor?) -> sonuclar/y2_karisik.json
"""

import json
import re
import sys
import time
from pathlib import Path

KLASOR = Path(__file__).resolve().parent
sys.path.insert(0, str(KLASOR))
from puanlama_eslestirme import REPO  # noqa: E402  (yolları da ekler)

MODEL, TEKRAR, NUM_CTX = "qwen3-vl:4b-instruct", 3, 8192
ISTEM = ("Bu, elle çizilmiş bir mimari kroki. Duvar parçaları kırmızı çizgilerle P1, P2… diye numaralandı. "
         "Her parçanın yanına el yazısıyla yazılmış ölçü sayılarını (cm) bul. Sadece bir JSON nesnesi döndür, "
         'başka bir şey yazma. Biçim: {"P1": [180], "P2": []}. Bir parçanın sayısı yoksa boş liste yaz.')


def y2_ciftleri(metin: str, eslem: dict[str, str]) -> list[tuple[int, str]]:
    """Cevaptaki ilk {...} JSON nesnesi -> [(değer, gerçek parça id)]; bozuksa []."""
    bulunan = re.search(r"\{.*\}", metin or "", re.S)
    if not bulunan:
        return []
    try:
        veri = json.loads(bulunan.group(0))
    except json.JSONDecodeError:
        return []
    ciftler = []
    for etiket, degerler in veri.items():
        if etiket not in eslem or not isinstance(degerler, list):
            continue
        for d in degerler:
            try:
                ciftler.append((int(str(d).strip()), eslem[etiket]))
            except ValueError:
                continue
    return ciftler


def _parcalar(kod, bulunan, bgr):
    """[(parça id, tür, baş, bit)]: gerçek cevaptan ya da kenar bulmadan."""
    if not bulunan:
        from gercek_eslestirme import KENARLAR
        return [p for parcalar in KENARLAR[kod].values() for p in parcalar]
    from mimarlik.kenar_bulma import kenarlari_bul
    from mimarlik.on_isleme import karakter_yuksekligi, murekkep_maskesi
    maske = murekkep_maskesi(bgr)
    sonuc = kenarlari_bul(maske, karakter_yuksekligi(maske))
    return [(p.id, p.tur, p.bas, p.bit) for k in sonuc.kenarlar for p in k.parcalar]


def girdi_gorseli(kod, karisik=False, bulunan=False):
    """Çizgileri silinmiş fotoğraf + parçalar (ince kırmızı) + P etiketleri. Döner: (PIL resim, eşlem)."""
    import cv2
    from PIL import Image, ImageDraw

    from mimarlik.on_isleme import cizgileri_sil
    from ortak import KROKILER, _font

    bgr = cv2.imread(str(REPO / KROKILER[kod]))
    resim = Image.fromarray(cv2.cvtColor(cizgileri_sil(bgr), cv2.COLOR_BGR2RGB))
    kalem, font = ImageDraw.Draw(resim), _font(22)
    tum = _parcalar(kod, bulunan, bgr)
    numaralar = list(range(1, len(tum) + 1))
    if karisik:
        import random
        random.Random(17).shuffle(numaralar)
    eslem = {}
    for n, (pid, _, a, b) in zip(numaralar, tum):
        etiket = f"P{n}"
        eslem[etiket] = pid
        kalem.line([a, b], fill=(230, 0, 0), width=3)
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        x1, y1, x2, y2 = kalem.textbbox(m, etiket, font=font, anchor="mm")
        kalem.rectangle([x1 - 3, y1 - 2, x2 + 3, y2 + 2], fill="white", outline=(230, 0, 0))
        kalem.text(m, etiket, fill=(230, 0, 0), font=font, anchor="mm")
    return resim, eslem


def main():
    import io

    import ollama

    karisik, bulunan = "karisik" in sys.argv[1:], "bulunan" in sys.argv[1:]
    ek = ("_bulunan" if bulunan else "") + ("_karisik" if karisik else "")
    sonuc = {"model": MODEL, "num_ctx": NUM_CTX, "istem": ISTEM, "karisik": karisik,
             "parcalar": "bulunan" if bulunan else "gercek", "krokiler": {}}
    (KLASOR / "gorseller").mkdir(exist_ok=True)
    (KLASOR / "sonuclar").mkdir(exist_ok=True)
    kodlar = ["01", "02"]
    for kod in kodlar:
        resim, eslem = girdi_gorseli(kod, karisik, bulunan)
        resim.save(KLASOR / "gorseller" / f"y2{ek}_girdi_{kod}.jpg", quality=90)
        tampon = io.BytesIO()
        resim.save(tampon, format="PNG")
        calistirmalar = []
        sonuc["krokiler"][kod] = {"eslem": eslem, "calistirmalar": calistirmalar}
        for i in range(TEKRAR):
            t0 = time.perf_counter()
            cevap = ollama.chat(model=MODEL, messages=[{"role": "user", "content": ISTEM, "images": [tampon.getvalue()]}],
                                options={"num_ctx": NUM_CTX},
                                keep_alive=0 if (i < TEKRAR - 1 or kod != kodlar[-1]) else "5m")
            sure = time.perf_counter() - t0
            ciftler = y2_ciftleri(cevap.message.content, eslem)
            calistirmalar.append({"ham": cevap.message.content, "ciftler": ciftler, "sure_s": round(sure, 2)})
            (KLASOR / "sonuclar" / f"y2{ek}.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"{kod} #{i + 1}: {len(ciftler)} çift ({sure:.0f} s)", flush=True)
    print(f"Yazıldı: sonuclar/y2{ek}.json")


if __name__ == "__main__":
    main()
