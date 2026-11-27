"""ornekler/internet/kaynaklar.txt -> deneyler/internet_krokileri/kaynaklar.txt: YALNIZ bağlantılar.

İnternetten bulunan krokiler `ornekler/internet/` altında ve `.gitignore`'da (telif başkasının). Hangi kaynakların
kullanıldığı depoda izlensin diye, kaynak listesinin yalnız bağlantıları (http/https) içeren bir kopyası
`deneyler/` altına yazılır: dosya adları, notlar ve diğer metin kopyalanmaz. Sıra korunur, tekrarlar atılır.

Kullanım (repo kökünden), kaynaklar.txt'yi her güncelledikten sonra:
    .venv/Scripts/python -m araclar.kaynak_baglantilari
"""

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KAYNAK = REPO / "ornekler" / "internet" / "kaynaklar.txt"
HEDEF = REPO / "deneyler" / "internet_krokileri" / "kaynaklar.txt"
BAGLANTI = re.compile(r"https?://[^\s<>\"'()\[\]]+")
BASLIK = ("# İnternetten bulunan krokilerin kaynak bağlantıları (yalnız bağlantılar; görseller depoda yok).\n"
          "# Üretim: python -m araclar.kaynak_baglantilari  (girdi: ornekler/internet/kaynaklar.txt)\n"
          "# Kullanım: yalnız okuma ve sağlamlık testi, geometri doğruluğu için değil (CLAUDE.md 5.1).\n")


def baglantilar(metin: str) -> list[str]:
    """Metindeki http/https bağlantıları; sıra korunur, tekrarlar ve sondaki noktalama atılır."""
    sonuc = []
    for b in BAGLANTI.findall(metin):
        b = b.rstrip(".,;:!?")
        if b not in sonuc:
            sonuc.append(b)
    return sonuc


def yaz(kaynak: Path = KAYNAK, hedef: Path = HEDEF) -> int:
    liste = baglantilar(kaynak.read_text(encoding="utf-8"))
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text(BASLIK + "".join(b + "\n" for b in liste), encoding="utf-8")
    return len(liste)


def main() -> int:
    if not KAYNAK.exists():
        print(f"Bulunamadı: {KAYNAK.relative_to(REPO)}", file=sys.stderr)
        return 1
    print(f"{yaz()} bağlantı yazıldı: {HEDEF.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
