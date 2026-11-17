"""Ön işleme: mavi mürekkebi ayırma (defter çizgilerini silme) ve karakter yüksekliği tahmini.

Varsayım: mürekkep mavi (01–02 için doğru). Kırmızı ölçülü krokiler (05, 07) için renk aralığı
genişletilmeli; bu deneyde gerekmiyor.
"""

import cv2
import numpy as np

# OpenCV HSV: renk tonu 0–179, doygunluk/parlaklık 0–255. Ölçülen mürekkep: ton ~113, doygunluk ~110–125;
# kâğıt ve defter çizgileri doygunluk ~15–40 ama ton ~22–30 (sarımsı), mavi aralığın dışında.
TON_ARALIGI = (95, 135)
EN_AZ_DOYGUNLUK = 25  # soluk mürekkep 26–70'e iner; ayrımı renk tonu yapar
EN_AZ_PARLAKLIK = 40


def murekkep_maskesi(bgr):
    """Mavi mürekkep pikselleri için True olan maske."""
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    alt = np.array([TON_ARALIGI[0], EN_AZ_DOYGUNLUK, EN_AZ_PARLAKLIK], dtype=np.uint8)
    ust = np.array([TON_ARALIGI[1], 255, 255], dtype=np.uint8)
    return cv2.inRange(hsv, alt, ust) > 0


def cizgileri_sil(bgr, genislet=1):
    """Mürekkep dışındaki her pikseli beyaz yapar.

    genislet: maskeyi kaç piksel büyütüp mürekkep kenarındaki yumuşak geçişleri koruyacağı.
    """
    maske = murekkep_maskesi(bgr).astype(np.uint8)
    if genislet > 0:
        boy = 2 * genislet + 1
        maske = cv2.dilate(maske, np.ones((boy, boy), np.uint8))
    sonuc = np.full_like(bgr, 255)
    sonuc[maske > 0] = bgr[maske > 0]
    return sonuc


def karakter_yuksekligi(maske):
    """El yazısı karakter yüksekliğinin tahmini (piksel): küçük mürekkep bileşenlerinin medyan yüksekliği.

    Yüksekliği görüntünün %10'undan küçük ve alanı en az 20 piksel olan bileşenler sayılır; böylece
    duvarlar (uzun) ve tek piksellik gürültü dışarıda kalır. Eşikler bu değerin katı olarak tanımlanır.
    """
    adet, _, istatistik, _ = cv2.connectedComponentsWithStats(maske.astype(np.uint8), connectivity=8)
    sinir = 0.1 * maske.shape[0]
    yukseklikler = [istatistik[i, cv2.CC_STAT_HEIGHT] for i in range(1, adet)
                    if istatistik[i, cv2.CC_STAT_HEIGHT] < sinir and istatistik[i, cv2.CC_STAT_AREA] >= 20]
    if not yukseklikler:
        raise ValueError("mürekkep bulunamadı: karakter yüksekliği ölçülemiyor")
    return float(np.median(yukseklikler))
