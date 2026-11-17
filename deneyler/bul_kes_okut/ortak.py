"""Bu deneyin ortak parçaları: önceki deneylerin modüllerine yol, fotoğraf yolları, kutu çizimi."""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

KLASOR = Path(__file__).resolve().parent
REPO = KLASOR.parents[1]
GORSELLER = KLASOR / "gorseller"
SONUCLAR = KLASOR / "sonuclar"
sys.path.insert(0, str(KLASOR.parent / "ocr_karsilastirma"))

from dogru_cevaplar import DOGRU, KROKILER  # noqa: E402,F401
from puanlama import puanla, sayilari_al  # noqa: E402,F401

YESIL, KIRMIZI, MAVI, TURUNCU = (0, 160, 0), (220, 0, 0), (0, 60, 220), (230, 120, 0)


def _font(boy):
    try:
        return ImageFont.truetype("arialbd.ttf", boy)
    except OSError:
        return ImageFont.load_default(boy)


def kutulari_ciz(foto, ogeler, cikti, baslik="", kirp=None):
    """ogeler: [(yazi, (x1,y1,x2,y2), renk)] -> fotoğrafın üstüne kutu + yazı çizip kaydeder."""
    resim = Image.open(foto).convert("RGB")
    kalem = ImageDraw.Draw(resim)
    font = _font(28)
    for yazi, (x1, y1, x2, y2), renk in ogeler:
        kalem.rectangle([x1, y1, x2, y2], outline=renk, width=3)
        kalem.text((x1, y2 + 2), yazi, fill=renk, font=font, stroke_width=3, stroke_fill="white")
    if kirp:
        resim = resim.crop(kirp)
    if baslik:
        ImageDraw.Draw(resim).text((10, 10), baslik, fill=MAVI, font=font, stroke_width=3, stroke_fill="white")
    Path(cikti).parent.mkdir(parents=True, exist_ok=True)
    resim.save(cikti, quality=90)
    return cikti
