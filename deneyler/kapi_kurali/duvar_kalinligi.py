"""Deneme: ideal kapanma farkı, konturdaki iç duvar geçişi sayısı × duvar kalınlığı (10/20/25 cm) ile açıklanır mı?

Kapanma kontrolü değişmez (mimarın cevabı bekleniyor); bu yalnızca bir hesap.
- Fark: gerçek sayılar gerçek dış hatta (olcum.GERCEK_DIS_HAT, S1 toplamı, S3 = B) yerleştirilince kalan açık.
- Krokide görülen geçiş sayısı (fotoğraftan elle sayıldı): 01'de iç duvar çizilmemiş (tek oda, girinti/çıkıntılar
  duvar yüzü, geçiş değil) → 0; 02'de dış hat X'li küçük odanın iki duvarını (sağ duvar: kapılı 15/90/40, alt duvar: 45)
  birer kez geçiyor olabilir → eksen başına en çok 1.
- n × t'nin farka 5 cm (KAPANMA_TOLERANSI) içinde uyduğu bütün (n ≤ 6, t) çiftleri listelenir.

Çalıştırma (repo kökünden): PYTHONIOENCODING=utf-8 .venv/Scripts/python deneyler/kapi_kurali/duvar_kalinligi.py
"""

import importlib.util
import json
from pathlib import Path

KLASOR = Path(__file__).resolve().parent
_s = importlib.util.spec_from_file_location("kapi_olcum", KLASOR / "olcum.py")
olcum = importlib.util.module_from_spec(_s)
_s.loader.exec_module(olcum)

KALINLIKLAR = (10, 20, 25)
TOLERANS = 5
GORULEN_GECIS = {"01": {"yatay": 0, "dikey": 0}, "02": {"yatay": 1, "dikey": 1}}


def main():
    sonuc = {}
    for kod in olcum.ADLAR:
        x, y = olcum.ideal_kapanma(kod)
        for eksen, fark in (("yatay", abs(x)), ("dikey", abs(y))):
            uyan = [(n, t, n * t - fark) for t in KALINLIKLAR for n in range(1, 7) if abs(n * t - fark) <= TOLERANS]
            g = GORULEN_GECIS[kod][eksen]
            sonuc.setdefault(kod, {})[eksen] = {"fark_cm": fark, "uyan_n_t": uyan, "krokide_gecis": g,
                                                "gecis_basina_gereken_cm": fark / g if g else None}
            print(f"{kod} {eksen}: fark {fark} cm · uyan (n×t, sapma): "
                  f"{', '.join(f'{n}×{t} ({s:+d})' for n, t, s in uyan) or 'yok'} · krokide geçiş {g}"
                  + (f" → geçiş başına {fark / g:.0f} cm gerekir" if g else " → kalınlıkla açıklanamaz"))
        tek = [t for t in KALINLIKLAR if all(any(tt == t for _, tt, _ in sonuc[kod][e]["uyan_n_t"]) for e in ("yatay", "dikey"))]
        sonuc[kod]["iki_eksende_ayni_t"] = tek
        print(f"{kod}: iki eksende aynı kalınlıkla uyan t: {tek or 'yok'}")
    (KLASOR / "sonuclar" / "duvar_kalinligi.json").write_text(json.dumps(sonuc, ensure_ascii=False, indent=1),
                                                               encoding="utf-8")


if __name__ == "__main__":
    main()
