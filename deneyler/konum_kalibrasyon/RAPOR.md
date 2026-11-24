# Ö1: Qwen kutularındaki x kayması — koordinat dönüşümü mü, model mi?

Tarih: 2026-11-24 · Ürün kodu değişmedi. Kaynak soru: `../sekil_01/RAPOR.md` (01'de kutu x'i gerçeğin 0,89 katı).

## Sonuç

**Koordinat dönüşümümüz doğru; düzeltilecek bir katsayı yok.** Kayma sabit değil, modelin el yazısındaki
belirsizliği. Bu yüzden çözüm kalibrasyon değil, değer atamanın kayık kutulara dayanıklı olması (Ö2).

## 1. Kayıtlı çalıştırmalar (`olcum.py`, Qwen çağrılmaz)

14 Qwen-1 cevabı (konum deneyi 3 + ürün koşulu 3, her kroki; iskelet kaydı 1). Gerçek kutuyla eşlenen ve 6 h'den
yakın çiftler (139 çift):

| | x | y |
|---|---|---|
| Çalıştırma başına oran medyanı (qwen / gerçek) | 0,83 – 1,02 | 0,98 – 1,08 |
| Çalıştırma başına doğru uyumu qwen = a · gerçek + b | a 0,74 – 1,06, b −125 … +131 px | a 0,53 – 1,10 |
| Hepsi birlikte | oran 0,937, a 0,934, b −1 px | oran 1,013, a 0,983, b 23 px |

Katsayı çalıştırmadan çalıştırmaya değişiyor; aynı krokide bile (01: 0,86 – 0,99). Ortalamada x'te ~%6 daralma
var, ama bunun üstündeki oynama (±%10, ±130 px öteleme) çok daha büyük. Sabit bir düzeltme bunu gidermez. Modelin
sıcaklığı 1 (`ollama show`), bu da çalıştırmalar arası oynamayı açıklıyor.

## 2. Denetimli test (`sentetik.py`, 3 Qwen çağrısı)

Beyaz görsele konumu bilinen 10 sayı (bütün genişliğe yayılmış), ürünün istemi ve dönüşümüyle (`okuma`):

| Görsel | Bulunan | x oranı | x uyumu (a, b) | y oranı | Sapma medyan / en çok |
|---|---|---|---|---|---|
| 1152×2048 (kroki boyutu), tohum 1 | 10/10 | 0,999 | 1,000, 0 px | 1,005 | 5 / 9 px |
| 1152×2048, tohum 2 | 10/10 | 0,996 | 0,999, −3 px | 1,007 | 9 / 17 px |
| 2048×1152 (yatay) | 8/10 | 1,002 | 0,998, 4 px | 1,014 | 8 / 13 px |

- **Qwen3-VL 0–1000 oranı veriyor** (piksel değil): oran 1'e eşit, iki en/boy oranında da.
- **Ollama'nın küçültmesi ve en/boy oranı kayma yaratmıyor**: dikey ve yatay görselde aynı sonuç.
- Temiz, basılı rakamda kutular ≤ 17 px (< 0,5 h) doğru. Krokilerde 1,7 – 16,5 h'lik kayma el yazısından,
  gürültüden ve modelin sayıyı yanlış yere koymasından (15, 90, 10 gibi: kutu tamamen başka bir sayının yanında).
