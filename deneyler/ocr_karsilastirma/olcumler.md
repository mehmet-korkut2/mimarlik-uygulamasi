<!-- Bu bölüm rapor.py ile üretilir; elle düzenleme. -->

## Ölçümler

Doğru/fazla/kaçırılan çoklu küme olarak sayılır (bkz. puanlama.py). Birden fazla çalıştırmada ortalama ve parantez içinde tek tek değerler.

| Yöntem | Kroki | Çalıştırma | Doğru | Fazla/uydurma | Kaçırılan | Süre (s, ort.) |
|---|---|---|---|---|---|---|
| EasyOCR (1.7.2) | 01 (10 sayı) | 1 | 1 | 7 | 9 | 9.3 |
| EasyOCR (1.7.2) | 02 (14 sayı) | 1 | 4 | 9 | 10 | 11.4 |
| Gemini (gemini-3.6-flash) | 01 (10 sayı) | 3 | 10.0 (10/10/10) | 0.0 (0/0/0) | 0.0 (0/0/0) | 54.1 |
| Gemini (gemini-3.6-flash) | 02 (14 sayı) | 3 | 14.0 (14/14/14) | 0.0 (0/0/0) | 0.0 (0/0/0) | 71.2 |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct) | 01 (10 sayı) | 3 | 10.0 (10/10/10) | 0.0 (0/0/0) | 0.0 (0/0/0) | 94.5 |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct) | 02 (14 sayı) | 3 | 12.3 (13/12/12) | 1.0 (1/1/1) | 1.7 (1/2/2) | 60.3 |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct, sadece CPU) | 01 (10 sayı) | 3 | 10.0 (10/10/10) | 0.0 (0/0/0) | 0.0 (0/0/0) | 63.1 |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct, sadece CPU) | 02 (14 sayı) | 3 | 13.0 (13/13/13) | 0.3 (1/0/0) | 1.0 (1/1/1) | 67.9 |

## 01'in belirsiz sayıları (15, 90, 10)

| Yöntem | # | 15 | 90 | 10 |
|---|---|---|---|---|
| EasyOCR (1.7.2) | 1 | — | — | — |
| Gemini (gemini-3.6-flash) | 1 | okundu | okundu | okundu |
| Gemini (gemini-3.6-flash) | 2 | okundu | okundu | okundu |
| Gemini (gemini-3.6-flash) | 3 | okundu | okundu | okundu |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct) | 1 | okundu | okundu | okundu |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct) | 2 | okundu | okundu | okundu |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct) | 3 | okundu | okundu | okundu |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct, sadece CPU) | 1 | okundu | okundu | okundu |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct, sadece CPU) | 2 | okundu | okundu | okundu |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct, sadece CPU) | 3 | okundu | okundu | okundu |

## Tutarlılık

| Yöntem | Kroki | 3 çalıştırma birebir aynı mı? | Farklı çıkan değerler |
|---|---|---|---|
| Gemini (gemini-3.6-flash) | 01 | evet | — |
| Gemini (gemini-3.6-flash) | 02 | evet | — |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct) | 01 | evet | — |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct) | 02 | hayır | [40] |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct, sadece CPU) | 01 | evet | — |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct, sadece CPU) | 02 | hayır | [45] |

## Maliyet

- EasyOCR ve Qwen3-VL: yerel, **0 $** (elektrik hariç).
- Gemini, kroki başına ortalama 1216 girdi + 1551 çıktı/düşünme token'ı. Ücretsiz katmanda **0 $**; ücretli katmanda olsaydı ≈ **0.67 sent** / kroki (1.000 kroki ≈ 6.73 $).

## Ayrıntı: her çalıştırmada okunan sayılar

| Yöntem | Kroki | # | Okunan | Fazla değerler | Kaçırılan değerler |
|---|---|---|---|---|---|
| EasyOCR (1.7.2) | 01 | 1 | [281, 50, 81, 1, 6, 5, 198, 4] | [1, 4, 5, 6, 81, 198, 281] | [10, 15, 40, 90, 108, 120, 120, 140, 180] |
| EasyOCR (1.7.2) | 02 | 1 | [51, 9, 45, 45, 40, 24, 45, 8, 4, 8, 97, 162, 6] | [4, 6, 8, 8, 9, 24, 51, 97, 162] | [15, 40, 40, 40, 90, 102, 200, 200, 240, 300] |
| Gemini (gemini-3.6-flash) | 01 | 1 | [180, 108, 120, 15, 90, 10, 140, 50, 40, 120] | [] | [] |
| Gemini (gemini-3.6-flash) | 01 | 2 | [180, 108, 120, 15, 90, 10, 140, 120, 40, 50] | [] | [] |
| Gemini (gemini-3.6-flash) | 01 | 3 | [180, 108, 120, 15, 90, 10, 140, 120, 40, 50] | [] | [] |
| Gemini (gemini-3.6-flash) | 02 | 1 | [15, 90, 40, 300, 45, 45, 240, 200, 40, 40, 40, 102, 200, 45] | [] | [] |
| Gemini (gemini-3.6-flash) | 02 | 2 | [15, 300, 45, 45, 90, 40, 45, 200, 102, 40, 40, 40, 200, 240] | [] | [] |
| Gemini (gemini-3.6-flash) | 02 | 3 | [15, 300, 45, 45, 90, 40, 45, 200, 240, 102, 40, 40, 40, 200] | [] | [] |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct) | 01 | 1 | [180, 108, 120, 15, 90, 10, 140, 50, 40, 120] | [] | [] |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct) | 01 | 2 | [180, 108, 120, 15, 90, 10, 140, 50, 40, 120] | [] | [] |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct) | 01 | 3 | [180, 108, 120, 15, 90, 10, 140, 50, 40, 120] | [] | [] |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct) | 02 | 1 | [15, 300, 45, 45, 90, 40, 45, 200, 40, 40, 40, 200, 240, 162] | [162] | [102] |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct) | 02 | 2 | [15, 300, 45, 45, 90, 40, 45, 200, 40, 40, 162, 200, 240] | [162] | [40, 102] |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct) | 02 | 3 | [15, 300, 45, 45, 90, 40, 45, 200, 40, 40, 162, 200, 240] | [162] | [40, 102] |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct, sadece CPU) | 01 | 1 | [180, 108, 120, 15, 90, 10, 140, 50, 40, 120] | [] | [] |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct, sadece CPU) | 01 | 2 | [180, 108, 120, 15, 90, 10, 140, 50, 40, 120] | [] | [] |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct, sadece CPU) | 01 | 3 | [180, 108, 120, 15, 90, 10, 140, 50, 40, 120] | [] | [] |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct, sadece CPU) | 02 | 1 | [15, 300, 45, 45, 90, 40, 45, 200, 40, 40, 102, 200, 45, 240] | [45] | [40] |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct, sadece CPU) | 02 | 2 | [15, 300, 45, 45, 90, 40, 45, 200, 40, 40, 102, 200, 240] | [] | [40] |
| Qwen3-VL (Ollama) (qwen3-vl:4b-instruct, sadece CPU) | 02 | 3 | [15, 300, 45, 45, 90, 40, 45, 200, 40, 40, 102, 200, 240] | [] | [40] |
