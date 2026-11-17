"""Gerçek "sayı -> kenar parçası" cevabının kontrol görseli -> gorseller/gercek_eslestirme_*.jpg (.gitignore'da)

Çalıştırma (repo kökünden): deneyler/.venv/Scripts/python deneyler/eslestirme/ciz_gercek.py
"""

import sys
from pathlib import Path

import cv2
from PIL import Image, ImageDraw

KLASOR = Path(__file__).resolve().parent
sys.path[:0] = [str(KLASOR), str(KLASOR.parent / "bul_kes_okut"), str(KLASOR.parent / "cizgi_silme")]
from gercek_eslestirme import ANLAM_BILINMIYOR, ESLESME, KAPSAM_BELIRSIZ, KENARLAR  # noqa: E402
from konumlar import GERCEK  # noqa: E402
from on_isleme import cizgileri_sil  # noqa: E402
from ortak import KROKILER, REPO, _font  # noqa: E402

RENKLER = [(230, 25, 75), (60, 140, 60), (0, 90, 200), (245, 130, 48), (145, 30, 180), (0, 150, 150),
           (200, 0, 140), (120, 90, 0), (70, 70, 70), (0, 0, 128), (170, 110, 40), (128, 0, 0)]
KESIN, MIMARA = (0, 0, 0), (230, 120, 0)
KIRP = (40, 300, 1152, 1250)


def ciz(kod):
    parcalar = {p[0]: p for ps in KENARLAR[kod].values() for p in ps}
    bgr = cizgileri_sil(cv2.imread(str(REPO / KROKILER[kod])))
    resim = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    resim = Image.blend(resim, Image.new("RGB", resim.size, "white"), 0.55)  # mürekkep soluk arka plan
    kalem, font, kucuk = ImageDraw.Draw(resim), _font(26), _font(20)
    for i, parca_listesi in enumerate(KENARLAR[kod].values()):
        renk = RENKLER[i % len(RENKLER)]
        for pid, tur, a, b in parca_listesi:
            kalem.line([a, b], fill=renk, width=7 if tur == "duvar" else 3)
            for u in (a, b):
                kalem.ellipse([u[0] - 6, u[1] - 6, u[0] + 6, u[1] + 6], fill=renk)
            orta = ((a[0] + b[0]) // 2 + 8, (a[1] + b[1]) // 2 + 4)
            kalem.text(orta, pid + (" (açıklık)" if tur == "aciklik" else ""), fill=renk, font=kucuk,
                       stroke_width=3, stroke_fill="white")
    for ad, deger, (x1, y1, x2, y2) in GERCEK[kod]:
        pid = ESLESME[kod][ad]
        _, _, a, b = parcalar[pid]
        anlam, kapsam = ad in ANLAM_BILINMIYOR[kod], ad in KAPSAM_BELIRSIZ[kod]
        renk = MIMARA if (anlam or kapsam) else KESIN
        kalem.rectangle([x1, y1, x2, y2], outline=renk, width=3)
        kalem.line([((x1 + x2) / 2, (y1 + y2) / 2), ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)], fill=renk, width=2)
        etiket = f"{deger}→{pid}" + (" ?anlam" if anlam else "") + (" ?kapsam" if kapsam else "")
        kalem.text((x1, y2 + 2), etiket, fill=renk, font=font, stroke_width=3, stroke_fill="white")
    resim = resim.crop(KIRP)
    ImageDraw.Draw(resim).text((10, 8), f"{kod}: gerçek sayı → kenar parçası (siyah: kesin, turuncu: mimara bağlı)",
                               fill=KESIN, font=font, stroke_width=3, stroke_fill="white")
    cikti = KLASOR / "gorseller" / f"gercek_eslestirme_{kod}.jpg"
    cikti.parent.mkdir(exist_ok=True)
    resim.save(cikti, quality=90)
    print(f"Yazıldı: {cikti}")


if __name__ == "__main__":
    for k in KENARLAR:
        ciz(k)
