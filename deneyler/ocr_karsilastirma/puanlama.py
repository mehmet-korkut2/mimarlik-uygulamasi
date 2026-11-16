"""'Sadece sayıları al' filtresi ve tekrarları doğru sayan (çoklu küme) puanlama.

Her yöntemin çıktısı aynı filtreden geçer, böylece karşılaştırma adil olur.
"""

import re
from collections import Counter

EN_KUCUK, EN_BUYUK = 1, 9999


def sayilari_al(parcalar) -> list[int]:
    """Metin parçalarından (ya da sayılardan) 1–9999 arası tam sayıları sırayla çıkarır."""
    sayilar = []
    for parca in parcalar:
        for eslesme in re.findall(r"\d+", str(parca)):
            deger = int(eslesme)
            if EN_KUCUK <= deger <= EN_BUYUK:
                sayilar.append(deger)
    return sayilar


def puanla(okunan: list[int], dogru: list[int]) -> dict:
    """Okunan sayıları doğru cevapla çoklu küme olarak karşılaştırır.

    dogru     = her değer için min(okunan adet, gerçek adet)
    fazla     = okunan - dogru   (uydurma ya da yanlış okunan)
    kacirilan = gerçek - dogru
    """
    o, d = Counter(okunan), Counter(dogru)
    ortak = o & d  # her değer için min adet
    fazla = o - d
    kacirilan = d - o
    return {
        "dogru": sum(ortak.values()),
        "fazla": sum(fazla.values()),
        "kacirilan": sum(kacirilan.values()),
        "fazla_degerler": sorted(fazla.elements()),
        "kacirilan_degerler": sorted(kacirilan.elements()),
    }
