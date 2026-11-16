# OCR deneyi: el yazısı ölçü sayılarını okuma

Atılabilir bir deney (spike). Ana modüle (`mimarlik/`) girmez. Tasarım:
`docs/superpowers/specs/2026-11-16-ocr-deneyi-design.md`. Sonuç: `RAPOR.md`.

Fotoğraflar `ornekler/` içinden okunur ve hiçbir yere kopyalanmaz (klasör `.gitignore`'da).
`sonuclar/` klasöründe sadece metin var.

## Kurulum (repo kökünden, Git Bash)

```bash
python -m venv deneyler/.venv
deneyler/.venv/Scripts/pip install -r deneyler/ocr_karsilastirma/requirements.txt
```

## Çalıştırma

```bash
P=deneyler/.venv/Scripts/python; D=deneyler/ocr_karsilastirma

$P -m pytest $D/test_puanlama.py            # puanlama testleri
$P $D/calistir_easyocr.py                   # -> sonuclar/easyocr.json
GEMINI_API_KEY=... $P $D/calistir_gemini.py # anahtar ortam değişkeninden okunur (koda yazma)
ollama pull qwen3-vl:4b-instruct
$P $D/calistir_qwen.py                      # -> sonuclar/qwen_4b-instruct.json
$P $D/rapor.py                              # -> olcumler.md
```

Windows konsolunda Türkçe karakterler bozuk görünürse başına `PYTHONIOENCODING=utf-8` ekle.
