# Konum Deneyi Raporu: Qwen3-VL 4B'den Sayı + Kutu

Tarih: 2026-11-17 · Önceki deney: [`../ocr_karsilastirma/RAPOR.md`](../ocr_karsilastirma/RAPOR.md) ·
Tablolar: [`olcumler.md`](olcumler.md) (`olcumler.py` üretir) · Ham çıktı: `sonuclar/qwen_konum.json` ·
Kontrol görselleri: `gorseller/` (**fotoğraf sayılır, `.gitignore`'da**; `ciz.py` ile yeniden üretilir)

## Kısa cevap

1. **Konum istemek okuma doğruluğunu düşürmedi, ama fazla sayıyı artırdı.** 24 sayıdan doğru:
   dün (sadece sayı) **23 / 22 / 22**, bugün (sayı + kutu) **22 / 24 / 22**. Fazla/uydurma sayı ise
   çalıştırma başına **1 → 3–5** çıktı (çoğu aynı sayının tekrarı: fazladan `40`, `45`, `200`).
2. **Süre yaklaşık iki katına çıktı:** kroki başına ~60 s → **116–177 s**. Fotoğraf işleme aynı (~43 s);
   fark, cevabın uzamasından (46–62 → 336–637 çıktı token'ı; model %60 CPU'da, üretim yavaş).
3. **Konumlar 01'de çoğunlukla kullanılabilir, 02'de zayıf.** Kutuların 01'de %58'i, 02'de %14'ü
   tam sayının üstünde. 02'nin 1. çalıştırmasında 8 kutu fotoğrafın üst kenarında, sayıların hiçbirinin
   yanında değil. **Qwen 4B'nin kutuları bu haliyle sayı–duvar eşleştirmesi için güvenilir değil;
   kaba bir ipucu olarak kullanılabilir.**

## Koordinat biçimi

Ölçek: Qwen3-VL kutuları **0–1000 oranlı** (x1, y1, x2, y2) veriyor. İlk deneme çalıştırmasında
doğrulandı. Hiçbir koordinat 1000'i geçmedi ve oranlı çizim sayılara oturdu. Fotoğraflarda EXIF yön
bilgisi yok, yani model ile çizim aynı yönü görüyor.

## Okuma doğruluğu (dünle karşılaştırma)

Aynı koşullar: `qwen3-vl:4b-instruct`, `num_ctx` 8192, her çalıştırmadan sonra model boşaltıldı,
%60 CPU / %40 GPU (dünkü GPU koşusuyla aynı). Aynı çoklu küme puanlaması.

| | 01 doğru /10 | 02 doğru /14 | Toplam /24 | Fazla (toplam) | Kroki başına süre |
|---|---|---|---|---|---|
| Dün, sadece sayı | 10 / 10 / 10 | 13 / 12 / 12 | **23 / 22 / 22** | 1 / 1 / 1 | ~60 s |
| Bugün, sayı + kutu | 10 / 10 / 10 | 12 / 14 / 12 | **22 / 24 / 22** | 5 / 5 / 3 | 116–177 s |

- 02'nin 2. çalıştırması 14 sayının hepsini buldu, ama 5 fazla sayı ekledi. "Doğru" sütunu tek başına
  yanıltıcı; fazla sayılar da kullanıcının silmesi gereken satırlar.
- Yeni bir okuma hatası çıktı: `90` → `96` (02 #3). Aynı istemle dün bu hata yoktu.
- Kutularla birlikte model aynı sayıyı farklı yerlere birden çok kez "bulma" eğiliminde (02'de dört
  `40` yerine altı–yedi `40`).

## Konum doğruluğu (gözle, görseller üzerinden)

Her kutuyu gözle üç sınıfa ayırdım:
- **doğru:** sayının çoğu kutunun içinde,
- **yakın:** kutu sayıya değiyor ya da bir sayı boyundan az kaymış,
- **yanlış:** kutu başka bir yerde, boş kâğıtta ya da başka bir sayının üstünde.

Bu benim değerlendirmem; görsellerden doğrulaman gerekiyor.

| Kroki · çalıştırma | Kutu | Doğru | Yakın | Yanlış |
|---|---|---|---|---|
| 01 · 1 | 10 | 6 | 3 | 1 |
| 01 · 2 | 10 | 6 | 3 | 1 |
| 01 · 3 | 11 | 6 | 3 | 2 |
| **01 toplam** | **31** | **18 (%58)** | **9 (%29)** | **4 (%13)** |
| 02 · 1 | 17 | 0 | 6 | 11 |
| 02 · 2 | 19 | 5 | 4 | 10 |
| 02 · 3 | 14 | 2 | 7 | 5 |
| **02 toplam** | **50** | **7 (%14)** | **17 (%34)** | **26 (%52)** |

Gözlemler:
- **01 (seyrek, büyük yazı):**
  - Sol duvar ve alttaki sayılarda (`180`, `108`, `120`, `15`, `10`) kutular tutarlı biçimde doğru.
  - Sağ üst köşedeki birbirine yakın `50` / `40` ve sağ duvardaki `120` çalıştırmadan çalıştırmaya
    kayıyor.
  - 01 #2'de `140`'ın kutusu `10`'un üstünde. Değer doğru okunmuş ama yeri yanlış; eşleştirmede bu,
    yanlış duvara yazılmak demek.
- **02 (yoğun, küçük yazı, tekrar eden sayılar):**
  - Kutular sıklıkla sola ve yukarı kaymış.
  - Etiket ile kutu karışabiliyor: 02 #2'de bir `40`'ın üstündeki kutu `45` etiketli, 02 #3'te `50`'nin
    üstündeki kutu `40` etiketli (01).
  - 02 #1'in üst sıradaki 8 kutusu, sayıları sırayla listeleyip kutuları uydurmuş gibi bir düzende.
- **Sağlam olanlar:** Büyük ve diğer sayılardan ayrı duran sayılar (`180`, `240`, sağ üst `45`, alttaki
  `200`) en iyi konumlananlar.

## `102` → `162` hatası ve kutusu

| Çalıştırma | Okunan | Kutu (0–1000) | Kutunun yeri |
|---|---|---|---|
| 02 · 1 | **162** | [231, 506, 324, 541] | **yakın:** yazının hemen üstünde, duvara inen ölçü çizgisinin üstünde; yazıyı kapsamıyor |
| 02 · 2 | 102 (doğru) | [240, 546, 340, 577] | **doğru:** `102`'yi tam kapsıyor |
| 02 · 3 | **162** | [218, 523, 282, 550] | **yakın:** yazının sol üst köşesiyle örtüşüyor, "1" ve "0"ın bir kısmı içeride |

Hata iki çalıştırmada tekrarladı. **Hatalı çalıştırmalarda kutu yazının üstüne değil, hemen yanına
düştü.** Ama yazıya yaklaşık bir sayı boyu kadar yakın ve hep aynı bölgede. Model yazıyı doğru
okuduğunda kutu da tam oturdu.

## Sonraki adım önerileri (bu deneyde denenmedi)

1. **"Kutuyu kes, büyüt, tekrar okut":** Sınırda ya da şüpheli bir sayının bölgesini kesip büyütüp
   Qwen'e tek başına okutmak. Örnek şüpheler: toplam kontrolü tutmayan sayı, iki çalıştırmada farklı
   okunan sayı. `162` örneğinde kutu yazının yanına düştüğü için **kesim kutunun kendisi değil,
   her yöne en az bir kutu boyu genişletilmiş bölge olmalı.** Küçük bir kesitte model hem daha büyük
   piksel görür hem de diğer sayılarla karışmaz.
2. **Konumu başka bir yöntemle bulmak, okumayı Qwen'e bırakmak:** Qwen 4B'nin konumu zayıf, okuması
   iyi. Konum için ayrı bir yazı bulucu düşünülebilir:
   - EasyOCR'ın yazı bulucusu (CRAFT), ya da
   - OpenCV ile mürekkep kümelerini bulmak.

   Bulunan her bölge 1. maddedeki gibi Qwen'e okutulur. Dün EasyOCR sayıları kötü **okudu**, ama
   **yerlerini** bulup bulamadığı ölçülmedi; ucuz bir deney.
3. **Sayıyı ve konumu ayrı istemek:** Fazla sayılar kutu isteyince arttı. "Önce sayılar, sonra her
   birinin yeri" gibi iki adımlı bir istem fazlaları azaltabilir. Süreyi daha da uzatır.
4. **Süre:** Çıktı uzadığı için üretim süresi baskın hale geldi. Daha önce not edilen `num_ctx` 4096
   denemesi (modelin daha büyük kısmı GPU'ya sığar) şimdi daha değerli.

## Sınırlar

- 2 kroki, 6 çalıştırma, 81 kutu. Konum değerlendirmesi tek kişinin (benim) gözüyle ve kaba sınıflarla
  yapıldı. Doğru kutu etiketi (gerçek konum) yok, bu yüzden sayısal örtüşme (IoU) ölçülmedi.
- Tek istem denendi; istem değişikliği konum kalitesini değiştirebilir.
