"""Bulunan kenarların kontrol görseli: gerçek parçalar (ince gri) + bulunan parçalar (renkli) + işaretler.

-> gorseller/bulunan_kenarlar_*.jpg (.gitignore'da)
Çalıştırma (repo kökünden): deneyler/.venv/Scripts/python deneyler/eslestirme/ciz_bulunan.py
"""

import sys
from pathlib import Path

import cv2
from PIL import Image, ImageDraw

KLASOR = Path(__file__).resolve().parent
REPO = KLASOR.parents[1]
sys.path[:0] = [str(REPO), str(KLASOR), str(KLASOR.parent / "bul_kes_okut")]
from gercek_eslestirme import KENARLAR  # noqa: E402
from mimarlik.kenar_bulma import kenarlari_bul  # noqa: E402
from mimarlik.on_isleme import cizgileri_sil, karakter_yuksekligi, murekkep_maskesi  # noqa: E402
from ortak import KROKILER, _font  # noqa: E402

RENKLER = [(230, 25, 75), (60, 140, 60), (0, 90, 200), (245, 130, 48), (145, 30, 180), (0, 150, 150),
           (200, 0, 140), (120, 90, 0), (70, 70, 70), (0, 0, 128), (170, 110, 40), (128, 0, 0)]
KIRP = (40, 300, 1152, 1250)


def ciz(kod):
    bgr = cv2.imread(str(REPO / KROKILER[kod]))
    maske = murekkep_maskesi(bgr)
    h = karakter_yuksekligi(maske)
    sonuc = kenarlari_bul(maske, h)
    resim = Image.fromarray(cv2.cvtColor(cizgileri_sil(bgr), cv2.COLOR_BGR2RGB))
    resim = Image.blend(resim, Image.new("RGB", resim.size, "white"), 0.6)
    kalem, font, kucuk = ImageDraw.Draw(resim), _font(24), _font(18)
    for parcalar in KENARLAR[kod].values():  # gerçek: kalın açık gri
        for _, _, a, b in parcalar:
            kalem.line([a, b], fill=(200, 200, 200), width=14)
    for i, kenar in enumerate(sonuc.kenarlar):
        renk = RENKLER[i % len(RENKLER)]
        for p in kenar.parcalar:
            kalem.line([p.bas, p.bit], fill=renk, width=5 if p.tur == "duvar" else 2)
            for u in (p.bas, p.bit):
                kalem.ellipse([u[0] - 5, u[1] - 5, u[0] + 5, u[1] + 5], fill=renk)
            m = ((p.bas[0] + p.bit[0]) / 2 + 8, (p.bas[1] + p.bit[1]) / 2 + 4)
            etiket = p.id + (" açıklık" if p.tur == "aciklik" else "") + ("" if kenar.konturda else " (iç)")
            kalem.text(m, etiket, fill=renk, font=kucuk, stroke_width=3, stroke_fill="white")
    for isaret in sonuc.isaretler:  # işaret: siyah, duvar ucu dolu
        kalem.line([isaret.bas, isaret.bit], fill=(0, 0, 0), width=3)
        kalem.ellipse([isaret.bas[0] - 5, isaret.bas[1] - 5, isaret.bas[0] + 5, isaret.bas[1] + 5], fill=(0, 0, 0))
    resim = resim.crop(KIRP)
    ozet = (f"{kod}: h={h:.1f}  eksen={sonuc.eksen_acisi_derece:.1f}°  kenar={len(sonuc.kenarlar)}  "
            f"parça={sum(len(k.parcalar) for k in sonuc.kenarlar)}  işaret={len(sonuc.isaretler)}  "
            f"kontur={'-'.join(sonuc.kontur_sirasi) or 'yok'}")
    ImageDraw.Draw(resim).text((10, 8), ozet, fill=(0, 0, 0), font=font, stroke_width=3, stroke_fill="white")
    ImageDraw.Draw(resim).text((10, 38), "gri kalın: gerçek parçalar · renkli: bulunan · siyah: ölçü işareti adayı",
                               fill=(0, 0, 0), font=kucuk, stroke_width=3, stroke_fill="white")
    cikti = KLASOR / "gorseller" / f"bulunan_kenarlar_{kod}.jpg"
    resim.save(cikti, quality=90)
    print(ozet)


if __name__ == "__main__":
    for k in KENARLAR:
        ciz(k)
