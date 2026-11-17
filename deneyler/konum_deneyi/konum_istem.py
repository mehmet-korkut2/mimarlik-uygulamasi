"""Sayıları konumlarıyla isteyen istem, cevap ayrıştırma ve koordinat dönüşümü."""

import json
import re
import sys
from pathlib import Path

# Dünkü deneyin puanlama/doğru cevap modülleri kopyalanmadan kullanılır (puanlama birebir aynı kalsın).
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ocr_karsilastirma"))
from puanlama import sayilari_al  # noqa: E402

ISTEM = (
    "Bu fotoğraf, bir mimarın bir odanın duvarlarını elle çizdiği bir kroki. "
    "Duvarların yanına el yazısıyla ölçü sayıları (cm) yazılmış. "
    "Fotoğraftaki el yazısı ölçü sayılarının HEPSİNİ bul ve her birinin yerini kutuyla göster; "
    "aynı sayı birden fazla kez yazılmışsa her birini ayrı yaz. Okuyamadığın bir sayıyı tahmin etme, atla. "
    'Sadece bir JSON dizi döndür, başka hiçbir şey yazma. Biçim: '
    '[{"bbox_2d": [x1, y1, x2, y2], "label": "180"}]'
)


def _kutu(deger):
    if isinstance(deger, list) and len(deger) == 4 and all(isinstance(v, (int, float)) for v in deger):
        return list(deger)
    return None


def _deger(etiket):
    sayilar = sayilari_al([etiket]) if etiket is not None else []
    return sayilar[0] if sayilar else None


def _ogeler(metin):
    """Cevaptaki JSON nesnelerini döndürür; dizi kesikse tamamlanmış nesneleri tek tek kurtarır."""
    bas = metin.find("[")
    if bas == -1:
        return []
    bit = metin.rfind("]")
    if bit > bas:
        try:
            veri = json.loads(metin[bas:bit + 1])
            if isinstance(veri, list):
                return [o for o in veri if isinstance(o, dict)]
        except json.JSONDecodeError:
            pass
    ogeler = []
    for parca in re.findall(r"\{[^{}]*\}", metin[bas:]):
        try:
            ogeler.append(json.loads(parca))
        except json.JSONDecodeError:
            continue
    return ogeler


def cevaptan_kutular(metin):
    """Model cevabı -> [{"deger": int|None, "kutu": [x1,y1,x2,y2]|None}, ...] (cevaptaki sırayla)."""
    return [{"deger": _deger(o.get("label")), "kutu": _kutu(o.get("bbox_2d"))} for o in _ogeler(metin or "")]


def piksele_cevir(kutu, genislik, yukseklik, olcek=1000):
    """0–olcek aralığındaki oranlı kutuyu fotoğraf pikseline çevirir; köşe sırasını düzeltir."""
    x1, y1, x2, y2 = kutu
    x1, x2 = sorted((x1, x2))
    y1, y2 = sorted((y1, y2))
    return [x1 / olcek * genislik, y1 / olcek * yukseklik, x2 / olcek * genislik, y2 / olcek * yukseklik]
