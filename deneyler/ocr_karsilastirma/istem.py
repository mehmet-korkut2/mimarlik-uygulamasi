"""İki görüntü modeline (Gemini, Qwen) birebir aynı verilen istem ve cevap ayrıştırma."""

import re

from puanlama import sayilari_al

ISTEM = (
    "Bu fotoğraf, bir mimarın bir odanın duvarlarını elle çizdiği bir kroki. "
    "Duvarların yanına el yazısıyla ölçü sayıları (cm) yazılmış. "
    "Fotoğraftaki el yazısı ölçü sayılarının HEPSİNİ listele; aynı sayı birden fazla kez "
    "yazılmışsa her birini ayrı yaz. Okuyamadığın bir sayıyı tahmin etme, atla. "
    "Sadece bir JSON dizi döndür, başka hiçbir şey yazma. Örnek: [180, 50, 40]"
)


def cevaptan_sayilar(metin: str) -> list[int]:
    """Cevaptaki ilk [...] dizisinden sayıları alır; dizi yoksa tüm metne aynı filtreyi uygular."""
    dizi = re.search(r"\[[^\]]*\]", metin or "")
    return sayilari_al([dizi.group(0) if dizi else (metin or "")])
