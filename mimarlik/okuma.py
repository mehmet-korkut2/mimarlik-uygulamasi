"""Qwen3-VL ile okuma: iki istem, cevap ayrıştırma ve Y2 için numaralı parça görseli.

İstemler deneylerdekiyle aynıdır (deneyler/konum_deneyi/konum_istem.py, deneyler/eslestirme/calistir_y2.py);
ölçümler bunlarla yapıldı. Ollama yalnızca `qwen_sor` çağrılınca yüklenir: testler sahte bir `sor`
fonksiyonu verir, Qwen gerekmez.
"""

import json
import random
import re

import cv2
import numpy as np

from mimarlik.eslestirme import KenarSonucu, Kutu

MODEL, NUM_CTX = "qwen3-vl:4b-instruct", 8192
KUTU_OLCEGI = 1000          # Qwen3-VL kutuları 0–1000 oranlı verir
Y2_TOHUM = 17               # P numaraları karışık sırayla (ölçüm: deneyler/eslestirme, Y2 karışık)
EN_KUCUK, EN_BUYUK = 1, 9999

ISTEM_SAYILAR = (
    "Bu fotoğraf, bir mimarın bir odanın duvarlarını elle çizdiği bir kroki. "
    "Duvarların yanına el yazısıyla ölçü sayıları (cm) yazılmış. "
    "Fotoğraftaki el yazısı ölçü sayılarının HEPSİNİ bul ve her birinin yerini kutuyla göster; "
    "aynı sayı birden fazla kez yazılmışsa her birini ayrı yaz. Okuyamadığın bir sayıyı tahmin etme, atla. "
    'Sadece bir JSON dizi döndür, başka hiçbir şey yazma. Biçim: '
    '[{"bbox_2d": [x1, y1, x2, y2], "label": "180"}]'
)
ISTEM_PARCALAR = (
    "Bu, elle çizilmiş bir mimari kroki. Duvar parçaları kırmızı çizgilerle P1, P2… diye numaralandı. "
    "Her parçanın yanına el yazısıyla yazılmış ölçü sayılarını (cm) bul. Sadece bir JSON nesnesi döndür, "
    'başka bir şey yazma. Biçim: {"P1": [180], "P2": []}. Bir parçanın sayısı yoksa boş liste yaz.'
)


def _sayi(deger) -> int | None:
    """Etiketteki ilk 1–9999 arası tam sayı ("180", 180, "1,02" -> 1); yoksa None."""
    for eslesme in re.findall(r"\d+", str(deger)):
        if EN_KUCUK <= int(eslesme) <= EN_BUYUK:
            return int(eslesme)
    return None


def _json_nesneleri(metin: str) -> list[dict]:
    """Cevaptaki JSON dizisinin nesneleri; dizi kesikse tamamlanmış nesneler tek tek kurtarılır."""
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
    nesneler = []
    for parca in re.findall(r"\{[^{}]*\}", metin[bas:]):
        try:
            nesneler.append(json.loads(parca))
        except json.JSONDecodeError:
            continue
    return nesneler


def sayilari_ayristir(metin: str, genislik: int, yukseklik: int) -> list[tuple[int, Kutu]]:
    """Qwen-1 cevabı -> [(değer, piksel kutusu)]; değeri ya da kutusu bozuk öğeler atlanır."""
    ogeler = []
    for o in _json_nesneleri(metin or ""):
        deger, kutu = _sayi(o.get("label")), o.get("bbox_2d")
        if deger is None or not (isinstance(kutu, list) and len(kutu) == 4
                                 and all(isinstance(v, (int, float)) for v in kutu)):
            continue
        x1, x2 = sorted(kutu[0::2])
        y1, y2 = sorted(kutu[1::2])
        sx, sy = genislik / KUTU_OLCEGI, yukseklik / KUTU_OLCEGI
        ogeler.append((deger, (x1 * sx, y1 * sy, x2 * sx, y2 * sy)))
    return ogeler


def parca_degerlerini_ayristir(metin: str, eslem: dict[str, str]) -> list[tuple[int, str]]:
    """Qwen-2 (Y2) cevabındaki ilk {...} nesnesi -> [(değer, parça id)]; bozuksa []."""
    bulunan = re.search(r"\{.*\}", metin or "", re.S)
    if not bulunan:
        return []
    try:
        veri = json.loads(bulunan.group(0))
    except json.JSONDecodeError:
        return []
    if not isinstance(veri, dict):
        return []
    ciftler = []
    for etiket, degerler in veri.items():
        if etiket not in eslem or not isinstance(degerler, list):
            continue
        for d in degerler:
            deger = _sayi(d)
            if deger is not None:
                ciftler.append((deger, eslem[etiket]))
    return ciftler


def parca_gorseli(bgr: np.ndarray, sonuc: KenarSonucu) -> tuple[np.ndarray, dict[str, str]]:
    """Bulunan parçalar ince kırmızı çizgi + P etiketiyle çizilmiş kopya. Döner: (görsel, {"P3": "K1.2"})."""
    resim = bgr.copy()
    parcalar = [p for k in sonuc.kenarlar for p in k.parcalar]
    numaralar = list(range(1, len(parcalar) + 1))
    random.Random(Y2_TOHUM).shuffle(numaralar)
    font, olcek, kalinlik = cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
    eslem = {}
    for n, p in zip(numaralar, parcalar):
        etiket = f"P{n}"
        eslem[etiket] = p.id
        a = tuple(int(round(v)) for v in p.bas)
        b = tuple(int(round(v)) for v in p.bit)
        cv2.line(resim, a, b, (0, 0, 230), 3)
        (g, y), taban = cv2.getTextSize(etiket, font, olcek, kalinlik)
        mx, my = (a[0] + b[0]) // 2, (a[1] + b[1]) // 2
        x1, y1 = mx - g // 2, my - y // 2
        cv2.rectangle(resim, (x1 - 3, y1 - 3), (x1 + g + 3, y1 + y + taban), (255, 255, 255), -1)
        cv2.rectangle(resim, (x1 - 3, y1 - 3), (x1 + g + 3, y1 + y + taban), (0, 0, 230), 1)
        cv2.putText(resim, etiket, (x1, y1 + y), font, olcek, (0, 0, 230), kalinlik, cv2.LINE_AA)
    return resim, eslem


def png(bgr: np.ndarray) -> bytes:
    basarili, veri = cv2.imencode(".png", bgr)
    if not basarili:
        raise ValueError("görsel PNG'ye çevrilemedi")
    return veri.tobytes()


def qwen_sor(istem: str, gorsel_png: bytes) -> str:
    """Yerel Ollama'daki Qwen3-VL'e tek görselli soru; ham cevap metni."""
    import ollama

    cevap = ollama.chat(model=MODEL, messages=[{"role": "user", "content": istem, "images": [gorsel_png]}],
                        options={"num_ctx": NUM_CTX}, keep_alive="5m")
    return cevap.message.content or ""
