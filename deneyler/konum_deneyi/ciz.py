"""sonuclar/qwen_konum.json + fotoğraflar -> gorseller/ altında kontrol görselleri.

Görseller fotoğraf sayılır; gorseller/ .gitignore'da, GitHub'a gitmez.
Çalıştırma (repo kökünden): deneyler/.venv/Scripts/python deneyler/konum_deneyi/ciz.py
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from konum_istem import piksele_cevir

KLASOR = Path(__file__).resolve().parent
REPO = KLASOR.parents[1]
GORSELLER = KLASOR / "gorseller"
RENK_DOGRU, RENK_FAZLA = (0, 170, 0), (220, 0, 0)


def _font(boy):
    try:
        return ImageFont.truetype("arialbd.ttf", boy)
    except OSError:
        return ImageFont.load_default(boy)


def ciz(foto, kutular, cikti, dogru_degerler=None, baslik=""):
    """Her kutuyu ve okunan değeri fotoğrafın üstüne çizer.

    dogru_degerler verilirse doğru cevapta olmayan (fazla) değerler kırmızı çizilir.
    """
    resim = Image.open(foto).convert("RGB")
    g, y = resim.size
    kalem = ImageDraw.Draw(resim)
    font, kucuk = _font(max(18, g // 30)), _font(max(14, g // 45))
    kalan = list(dogru_degerler) if dogru_degerler is not None else None
    for sira, k in enumerate(kutular, 1):
        if k["kutu"] is None:
            continue
        renk = RENK_DOGRU
        if kalan is not None:
            if k["deger"] in kalan:
                kalan.remove(k["deger"])
            else:
                renk = RENK_FAZLA
        x1, y1, x2, y2 = piksele_cevir(k["kutu"], g, y)
        kalem.rectangle([x1, y1, x2, y2], outline=renk, width=4)
        yazi = f"{k['deger']}"
        kalem.text((x2 + 6, y1 - 4), yazi, fill=renk, font=font, stroke_width=3, stroke_fill="white")
        kalem.text((x1, y2 + 2), f"#{sira}", fill=renk, font=kucuk, stroke_width=2, stroke_fill="white")
    if baslik:
        kalem.text((10, 10), baslik, fill=(0, 0, 200), font=font, stroke_width=3, stroke_fill="white")
    Path(cikti).parent.mkdir(parents=True, exist_ok=True)
    resim.save(cikti, quality=90)
    return cikti


def main():
    from dogru_cevaplar import DOGRU, KROKILER  # ocr_karsilastirma'dan (konum_istem.py yolu ekledi)

    sonuc = json.loads((KLASOR / "sonuclar" / "qwen_konum.json").read_text(encoding="utf-8"))
    for kod, k in sonuc["krokiler"].items():
        for i, c in enumerate(k["calistirmalar"], 1):
            cikti = GORSELLER / f"{kod}_calistirma{i}.jpg"
            ciz(REPO / KROKILER[kod], c["kutular"], cikti, DOGRU[kod],
                baslik=f"{kod} #{i}  yesil=dogru cevapta var, kirmizi=fazla")
            print(f"Yazıldı: {cikti}")


if __name__ == "__main__":
    main()
