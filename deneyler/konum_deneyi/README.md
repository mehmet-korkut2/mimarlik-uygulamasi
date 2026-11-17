# Konum deneyi: Qwen3-VL'den sayı + kutu

Atılabilir bir deney (spike). Önceki OCR deneyinin (`../ocr_karsilastirma/`) `dogru_cevaplar.py` ve
`puanlama.py` modüllerini kopyalamadan kullanır. Sonuç: `RAPOR.md`.

`gorseller/` fotoğrafın üstüne çizim içerir; `.gitignore`'da, GitHub'a gitmez.

## Çalıştırma (repo kökünden, Git Bash; venv kurulumu için `../ocr_karsilastirma/README.md`)

```bash
P=deneyler/.venv/Scripts/python; D=deneyler/konum_deneyi

$P -m pytest $D/test_konum_istem.py   # ayrıştırma ve koordinat testleri
$P $D/calistir.py               # Ollama + qwen3-vl:4b-instruct -> sonuclar/qwen_konum.json (~15 dk)
$P $D/olcumler.py               # -> olcumler.md (dünkü sonuçla karşılaştırma)
$P $D/ciz.py                    # -> gorseller/*.jpg (kontrol görselleri)
```
