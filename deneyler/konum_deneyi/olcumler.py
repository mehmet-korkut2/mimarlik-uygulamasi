"""Bugünkü (sayı + kutu) ve dünkü (sadece sayı, GPU) Qwen sonuçlarını karşılaştırır -> olcumler.md

Çalıştırma (repo kökünden): deneyler/.venv/Scripts/python deneyler/konum_deneyi/olcumler.py
"""

import json
from pathlib import Path

from konum_istem import cevaptan_kutular  # noqa: F401  (yol ekleme yan etkisi için)
from dogru_cevaplar import DOGRU
from puanlama import puanla

KLASOR = Path(__file__).resolve().parent
DUN = KLASOR.parent / "ocr_karsilastirma" / "sonuclar" / "qwen_4b-instruct.json"
BUGUN = KLASOR / "sonuclar" / "qwen_konum.json"


def _oku(yol):
    return json.loads(yol.read_text(encoding="utf-8"))


def ozet(dun, bugun):
    satirlar = ["| Kroki | İstem | # | Doğru | Fazla değerler | Kaçırılan değerler | Süre (s) | Fotoğraf işleme (s) | Üretim (s) | Çıktı token |",
                "|---|---|---|---|---|---|---|---|---|---|"]
    for kod in DOGRU:
        for ad, s in (("sadece sayı (dün)", dun), ("sayı + kutu (bugün)", bugun)):
            for i, c in enumerate(s["krokiler"][kod]["calistirmalar"], 1):
                p = puanla(c["sayilar"], DOGRU[kod])
                o = c["ollama_sureleri_s"]
                satirlar.append(f"| {kod} ({len(DOGRU[kod])}) | {ad} | {i} | {p['dogru']} | {p['fazla_degerler'] or '—'} | "
                                f"{p['kacirilan_degerler'] or '—'} | {c['sure_s']:.0f} | {o['girdi_isleme']:.0f} | "
                                f"{o['uretim']:.1f} | {c['token']['cikti']} |")
    return "\n".join(satirlar)


def toplamlar(s):
    return [sum(puanla(s["krokiler"][k]["calistirmalar"][i]["sayilar"], DOGRU[k])["dogru"] for k in DOGRU)
            for i in range(3)]


def kutular(bugun):
    satirlar = ["| Kroki | # | Okunan değer ve kutu (0–1000; x1, y1, x2, y2) |", "|---|---|---|"]
    for kod, k in bugun["krokiler"].items():
        for i, c in enumerate(k["calistirmalar"], 1):
            ogeler = ", ".join(f"{o['deger']} {o['kutu']}" for o in c["kutular"])
            satirlar.append(f"| {kod} | {i} | {ogeler} |")
    return "\n".join(satirlar)


def main():
    dun, bugun = _oku(DUN), _oku(BUGUN)
    metin = "\n\n".join([
        "<!-- Bu dosya olcumler.py ile üretilir; elle düzenleme. -->",
        "# Ölçümler: sayı + kutu istemi\n\nDoğru/fazla/kaçırılan, dünkü deneyle aynı çoklu küme puanlamasıyla "
        "(`ocr_karsilastirma/puanlama.py`). Dün: `ocr_karsilastirma/sonuclar/qwen_4b-instruct.json` (GPU).",
        f"**Toplam doğru / 24 (çalıştırma başına):** dün {'/'.join(map(str, toplamlar(dun)))}, "
        f"bugün {'/'.join(map(str, toplamlar(bugun)))}",
        "## Çalıştırma çalıştırma\n\n" + ozet(dun, bugun),
        "## Ham kutular\n\n" + kutular(bugun),
        "## `ollama ps` (bugün, son çalıştırmadan sonra)\n\n```\n" + bugun.get("ollama_ps", "").strip() + "\n```",
    ])
    (KLASOR / "olcumler.md").write_text(metin + "\n", encoding="utf-8")
    print("Yazıldı: olcumler.md")


if __name__ == "__main__":
    main()
