# OCR Deneyi Raporu: El Yazısı Ölçü Sayılarını Okuma

Tarih: 2026-11-16 · Tasarım: `docs/superpowers/specs/2026-11-16-ocr-deneyi-design.md` ·
Ham ölçümler ve tüm tablolar: [`olcumler.md`](olcumler.md) (`rapor.py` üretir) · Ham çıktılar: `sonuclar/`

## Kısa cevap

**Yerel model (Qwen3-VL 4B) ile bulut model (Gemini Flash) arasındaki fark küçük:** iki krokideki
24 sayıdan Gemini her çalıştırmada **24/24**, Qwen **22–23/24** okudu (6 çalıştırmanın ortalaması %95).
Qwen'in bütün hataları 02'de ve iki sayıda toplanıyor. Uydurma "gürültü" sayısı üretmedi.
EasyOCR ise 24'ten **5**'ini okudu ve 16 uydurma sayı üretti; aday değil.

Ürünün hedefi "%100 otomatik" değil, "taslak + hızlı düzeltme" (CLAUDE.md Faz 2). Kroki başına
yaklaşık bir sayının düzeltilmesi bu hedefe uyuyor. **Öneri: yerel yol (Qwen3-VL 4B).** Bu,
kullanıcının "fark küçükse yerel" tercihine de uyuyor. Ancak sonuç **2 kolay kroki ve 24 sayıya**
dayanıyor (aşağıdaki sınırlara bakın).

## Sonuçlar

İki kroki toplam 24 sayı: 01'de 10, 02'de 14. Görüntü modelleri her krokide 3 kez çalıştı.

| Yöntem | Doğru / 24 (çalıştırma başına) | Fazla / uydurma | Gerçekçi süre / kroki | Maliyet |
|---|---|---|---|---|
| EasyOCR 1.7.2 (CPU) | **5** | 16 | ~10 s | 0 |
| Gemini `gemini-3.6-flash` (ücretsiz katman) | **24 / 24 / 24** | 0 | 45–75 s | 0 (ücretli katmanda ≈ 0,7 sent) |
| Qwen3-VL 4B instruct, GPU+CPU (%40 GPU) | **23 / 22 / 22** | 1 (her çalıştırmada) | ~50 s (+ ilk yükleme 8–49 s) | 0 |
| Qwen3-VL 4B instruct, sadece CPU | **23 / 23 / 23** | 1 (yalnız 1. çalıştırmada) | ~160–180 s | 0 |

**01'in belirsiz sayıları (15, 90, 10):** Gemini ve Qwen, 9 çalıştırmanın hepsinde üçünü de okudu.
EasyOCR hiçbirini okuyamadı. Mimarın bu okumaları doğrulaması hâlâ gerekiyor.

### Qwen'in hataları (hepsi 02'de)

- **`102` → `162`:** GPU'lu üç çalıştırmanın üçünde de. CPU çalıştırmalarında doğru okudu.
  **En tehlikeli hata türü bu:** uydurma değil, makul görünen yanlış bir sayı. Geometri bundan
  yanlış kurulur. Faz 2'deki "toplamlar tutmuyorsa nerede tutmadığını göster" kontrolü ve kullanıcının
  okunan sayıları onayladığı liste, bu hatayı yakalamak için gerekli.
- **Dört `40`'tan biri eksik:** 6 çalıştırmanın 5'inde. Aynı sayının tekrarı modeli zorluyor.
- **Fazladan `45`:** CPU'daki 1. çalıştırmada bir kez.

GPU ile CPU sonuçlarının farklı olması, aynı modelin farklı donanımda küçük sayısal farklarla farklı
okuyabildiğini gösteriyor. Tek bir çalıştırmaya güvenmemek için bu da bir gerekçe.

### Tutarlılık (3 çalıştırma)

- **Gemini:** İki krokide de üç çalıştırmanın değerleri birebir aynı (sadece sıra değişti).
- **Qwen:** 01'de birebir aynı. 02'de hatalar çalıştırmalar arasında büyük ölçüde aynı kaldı;
  yalnız bir `40`'ın okunup okunmaması değişti.

## Süre ve donanım

- **Qwen, GTX 1650 4 GB:** Model bellekte 4,6 GB tutuyor (ağırlıklar + görüntü kodlayıcı +
  8192 token'lık önbellek). Karta sığmadığı için Ollama **%60 CPU / %40 GPU** çalıştırdı.
  - Kroki başına ~42 s fotoğrafı işleme, ~8–10 s cevap üretme.
  - Model her çalıştırmadan sonra bellekten boşaltıldığı için ayrıca 8 s yükleme. İlk açılışta
    bu 49 s sürdü (diskten soğuk okuma).
  - Sadece CPU'da fotoğrafı işleme 150–170 s, yani ekran kartı yaklaşık 3 kat hızlandırdı.
- **Ölçüm hatası ve düzeltmesi:** İlk (sadece CPU) koşuda 2. ve 3. çalıştırmalar fotoğrafı Ollama'nın
  önbelleğinden aldı. O satırların `olcumler.md`'deki ortalama süresi (63–68 s) bu yüzden yanıltıcı;
  gerçek süre 1. çalıştırmadır (~170–180 s). Okuma sonuçları geçerli. GPU koşusunda model her
  çalıştırmadan sonra boşaltıldı, süreleri gerçekçi.
- **Gemini:** 45–75 s. Sürenin çoğu modelin cevaptan önce düşünmesi (kroki başına ~1.200–2.100
  düşünme token'ı) ve ücretsiz katmanın gecikmesi.
- **Hızlandırma fırsatı (denenmedi):** Önbelleği 4096 token'a düşürmek (fotoğraf ~2.400 token),
  modelin daha büyük kısmını GPU'ya sığdırabilir.

## Bağımlılık, veri ve erişilebilirlik

| | EasyOCR | Gemini | Qwen3-VL (Ollama) |
|---|---|---|---|
| Kurulum | pip; PyTorch ile birlikte yüzlerce MB | pip + Google hesabı + API anahtarı | Ollama uygulaması + 3,3 GB model |
| İnternet | İlk model indirmesi dışında yok | **Her istekte gerekli** | İlk indirme dışında yok |
| Veri | Bilgisayardan çıkmaz | **Fotoğraf Google'a gider. Ücretsiz katmanda içerik Google'ın ürünlerini geliştirmek için kullanılabilir** ("Content used to improve our products"). 01–02 için kullanıcı onayladı; gerçek müşteri krokileri için uygun değil. | Bilgisayardan çıkmaz |
| Erişilebilirlik | Her zaman | **`gemini-3.8-flash` iki ayrı denemede de ücretsiz katmanda sürekli 503 ("yoğun talep") verdi;** hiç sonuç alınamadı. Ölçüm bir önceki nesil `gemini-3.6-flash` ile yapıldı. | Her zaman (makine açıksa) |
| Donanım | CPU yeter | Yok | GPU'suz makinede kroki başına ~3 dakika |

## Sınırlar (sonucu okurken)

- **Örneklem çok küçük:** 2 kroki, 24 sayı, ikisi de "kolay". Qwen ile Gemini arasındaki 1–2 sayılık
  fark istatistiksel olarak güvenilir bir ayrım değil, sadece bir işaret.
- **Gemini'nin en yeni Flash'ı ölçülemedi:** 3.8 yerine 3.6 kullanıldı.
- **Sıra önemsizdi:** Deney sadece "hangi sayılar okundu"yu ölçtü. Faz 2'nin asıl işi sayıyı doğru
  duvarla eşleştirmek; bu ölçülmedi.
- **Ön işleme ve istem iyileştirme yapılmadı:** Her yöntem ham fotoğrafı aldı. Daha fazla iyileştirme
  her üç yöntemin sonucunu da değiştirebilir.

## Önerilen sonraki adımlar

1. **Faz 2'de sayı okuma için Qwen3-VL 4B ile devam et.** Modelden yalnız sayıları değil, her sayının
   fotoğraftaki **konumunu** da iste (Qwen3-VL konum/kutu döndürebiliyor); sayı–duvar eşleştirmesine
   böyle bağlanır.
2. **Hataları yakalayacak kontrolleri ürüne koy:** Her duvar için bir sayı var mı (eksik `40`) ve
   karşılıklı duvar toplamları tutuyor mu (`162` gibi yanlış okuma).
3. **03–07 krokileriyle aynı deneyi tekrarla** (doğru cevapları mimardan aldıktan sonra). Fark büyürse
   karar yeniden açılır.
4. **Mimara:** 01'deki 15/90/10 okumalarını doğrulat.
