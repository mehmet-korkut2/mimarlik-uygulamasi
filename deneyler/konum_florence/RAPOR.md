# Değeri doğru bölgeye atamak: Set-of-Mark, Florence-2, PaddleOCR

Tarih: 2026-11-28 · Ürün kodu değişmedi. Soru: Ö2'de kalan hata, okunan değerin yanlış bölgeye gitmesi (Qwen kutuları
kayık, `../konum_kalibrasyon/RAPOR.md`). Qwen'den daha iyi konum veren ya da değeri doğrudan bölgeye bağlayan bir
yol var mı?

Gerçek: `../bul_kes_okut/konumlar.py` (24 sayı, 01: 10, 02: 14). 01–02 çizim hatalı ama bu ölçüm yazılı sayının yeri ve
değeriyle ilgili, geometriyle değil (CLAUDE.md 5.1). **Uyarı:** bölge bulucu ve Ö2 bu iki krokiye bakılarak ayarlandı;
Florence ve Paddle ayarlanmadı. Yalnız 2 kroki var: sonuçlar yön gösterir, karar için yeni krokilerle tekrar gerekli.

> **Güncelleme (aynı gün): 03–07 ile okuma deneyi (`RAPOR_03_07.md`).** 147 sayıda Florence %12, Qwen %14 okuyor;
> iki model de yan/ters yazıda ve yoğun krokide çöküyor. Aşağıdaki 01–02 sonuçları 03–07'ye taşınmıyor.

## Kısa sonuç

1. **Florence-2-large, Qwen'den hem daha doğru yer hem daha iyi okuma veriyor.** Değerleri Qwen'in yerine Ö2'ye
   verildiğinde 24 sayının **21'i doğru bölgeye, hiçbiri yanlış bölgeye** gidiyor (Ö2 + Qwen: çalıştırma başına
   ortalama 16 doğru, 2,7 yanlış). **02'deki 102'yi doğru okuyor** (Qwen her çalıştırmada 162). Kroki başına ~9 s
   (Qwen ~1–4 dk), deterministik (aynı girdi → aynı çıktı).
2. **Set-of-Mark** doğru sayısını artırıyor (56/72, Ö2 48/72) ama yanlışı da (14, Ö2 8) ve gürültü bölgelerine değer
   yazıyor (20, Ö2 4). Çağrılar arası tutarlılık düşük (01: 6/13, 02: 15/27 bölgede 3 cevap aynı). Tek başına "emin"
   işareti veremez.
3. **İki bağımsız kaynağın uyuşması güçlü bir "emin" işareti:** SoM ∩ Ö2 ve Florence ∩ Ö2'de, ikisinin aynı değeri
   verdiği bölgelerde **yanlış 0/72**. Bugünkü "emin" kuralının (≤ 0,5 h) 8 yanlışı var (02'deki 162 dahil).
4. **PaddleOCR** yer bulmada iyi (merkez hatası ~0,2 h) ama el yazısı okuması zayıf (17/24; "—120", "740", "—g") ve
   çizgisiz görselde 02'de sayıların yarısını kaybediyor. Florence'in gerisinde.

## 1. Değer → bölge (ürünün asıl sorusu)

Aynı bölgeler (bizim bölge bulucu, 01: 13, 02: 27 bölge). Her gerçek sayı için kutusuyla örtüşen bölgelere bakılır:
**doğru** (doğru değer gitti), **yanlış** (başka değer gitti), **boş** (değer gitmedi → kullanıcıya sorulur),
**fazla** (gerçek sayı olmayan bölgeye — gürültü, kılavuz çizgisi, bölünmüş sayı — değer gitti). Bölge bulucu 24
sayının hepsinde bölge buldu. Qwen satırları: ürün koşulundaki 3 kayıtlı cevap (`../cizgi_silme/sonuclar/qwen_urun.json`);
Set-of-Mark: 3 yeni çağrı. Betik: `../set_of_mark/olcum.py`.

| Yöntem | Ölçüm | Doğru | Yanlış | Boş | Fazla |
|---|---|---|---|---|---|
| Eski kural (köşegen sınırı) | 3 × 24 | 56 | 13 | 3 | 11 |
| Ö2 (ürün, Qwen kutuları) | 3 × 24 | 48 | 8 | 16 | 4 |
| Ö2, yalnız "emin" (≤ 0,5 h) | 3 × 24 | 47 | 8 | 17 | 2 |
| Set-of-Mark (çağrı #1 / #2 / #3) | 24 / 24 / 24 | 15 / 21 / 20 | 8 / 3 / 3 | 1 / 0 / 1 | 5 / 10 / 5 |
| Set-of-Mark, toplam | 3 × 24 | 56 | 14 | 2 | 20 |
| Set-of-Mark, çoğunluk oyu (3 çağrı → 1 cevap) | 1 × 24 | 19 | 3 | 2 | 4 |
| **SoM ∩ Ö2** (ikisi aynı değer) | 3 × 24 | 41 | **0** | 31 | 3 |
| **Ö2 + Florence-2 değerleri** | 1 × 24 | **21** | **0** | 3 | **0** |
| **Florence-2 ∩ Ö2** (ikisi aynı değer) | 3 × 24 | 41 | **0** | 31 | 0 |

- Set-of-Mark tutarlılığı: 01'de 13 bölgenin 6'sında, 02'de 27'nin 15'inde 3 çağrı aynı cevabı verdi. Hatalar
  komşu etiketlere kayma (01 #1'de 50/40/120 yer değiştiriyor) ve "-90" gibi işaretli değerler. Süre 20–87 s/çağrı.
- Ö2 + Florence'in boş bıraktıkları: 01 "40" (Florence 50 ile birleştirip `-50-0` okuyor), 02 "45 üst sağ" (`45 45`
  tek kutu) ve "90". Üçü de kullanıcıya soru olur; yanlış değer olarak çizilmez.
- Florence ∩ Ö2'de boş 31: Florence haklı ama Qwen farklı/yerinde değilken de "emin değil" düşüyor; bu ölçüt temkinli.

## 2. Yer bulma ve okuma (kutu kaynağına göre)

Bir gerçek kutu "bulundu": bir tespit kutusunun merkezi içinde (0,5 h pay) ya da IoU ≥ 0,3. Merkez hatası h cinsinden
(h ≈ rakam yüksekliği). Betik: `olcum.py`; tespitler `calistir.py` (`.venv-deney`).

| Kaynak | 01 bulunan /10 | 01 merkez hata medyan / en çok | 02 bulunan /14 | 02 merkez hata | Okunan (01 + 02) |
|---|---|---|---|---|---|
| Bölge bulucumuz (okumaz) | 10 | 0,17 / 1,01 | 14 | 0,19 / 1,44 | — |
| Qwen kutuları (6 kayıt) | 6–7 | 0,60–1,00 / ≤ 1,91 | 3–9 | 0,68–1,45 / ≤ 1,96 | 9–14 / 24 |
| **Florence-2 (ham, tam)** | 9 | 0,35 / 0,84 | 11 | 0,20 / 0,78 | **20 / 24** |
| Florence-2 (ham, karo 2×3) | 9 | 0,13 / 0,85 | 11 | 0,20 / 0,76 | 17 / 24 |
| Florence-2 (çizgisiz, tam) | 9 | 0,25 / 0,78 | 11 | 0,23 / 1,83 | 19 / 24 |
| PaddleOCR (ham, tam) | 9 | 0,18 / 0,89 | 12 | 0,46 / 0,72 | 17 / 24 |
| PaddleOCR (çizgisiz, tam) | 9 | 0,15 / 0,82 | 6 | 0,31 / 0,63 | 11 / 24 |

- "Okunan": konumla birlikte doğru okunan. Qwen'in okuması (konumsuz) 22–23/24; ama Qwen'de doğru değer çoğu zaman
  yanlış yerde — sorunun kendisi bu.
- Karolama (2×3) Florence'e yardım etmiyor: yer biraz iyileşiyor, okuma kötüleşiyor (rakamlar karo sınırında
  bölünüyor). Defter çizgisi silmek de yardım etmiyor (Paddle'da çok zararlı).
- Florence'in kendi kutuları bölge yerine kullanılınca da 22/24 doğru, 0 fazla ("kendi okuması" satırı, `olcum.py`);
  ama ürün için anlamlı olan, değerin **bizim** bölgemize (tik / duvar bağlaması onun üzerinden) gitmesi: bölüm 1.
- Florence/Paddle kutuları + Qwen değerleri (Macar eşleştirme, `olcum.py` "birleştirme"): Florence ile 58/72 doğru,
  7 yanlış. Florence'in kendi değerini kullanmaktan kötü; bu yol gereksiz.

## 3. Maliyet ve kurulum

| | Florence-2-large | PaddleOCR 3.7 (PP-OCRv6 medium) | Qwen3-VL 4B (Ollama) |
|---|---|---|---|
| Süre / kroki (GTX 1650 4 GB) | ~8–10 s (GPU, fp16) | ~40 s (CPU) | ~1–4 dk |
| Deterministik | evet (ışın arama) | evet | hayır (sıcaklık 1) |
| Bağımlılık | torch + transformers (~2,5 GB tekerlek + 1,5 GB model) | paddlepaddle + paddlex | Ollama |
| Lisans | MIT | Apache-2.0 | Apache-2.0 |

Sürüm notları: transformers 5.24 ile Microsoft'un uzak kodu çalışmıyor (`forced_bos_token_id`); aynı ağırlıkların
yerleşik sürümü kullanıldı (`florence-community/Florence-2-large`, `Florence2ForConditionalGeneration`). Paddle 3.3
Windows'ta oneDNN ile `NotImplementedError` veriyor; `enable_mkldnn=False` gerekli. Qwen ile aynı anda 4 GB GPU'ya
sığmıyorlar; sırayla çalıştırıldı.

## 4. Ürüne alma için seçenekler (karar kullanıcının; uygulanmadı)

| Seçenek | Ne olur | Artı | Eksi / risk |
|---|---|---|---|
| **A. Florence okuma + konum, Qwen yerine** | Ö2'ye Florence'in (değer, kutu) listesi girer | 02'de 102 doğru, yanlış 0, ~20 kat hızlı, deterministik | Yalnız 2 krokide ölçüldü; ters/yan yazı, virgül, kutu içi sayı, renkli kalem denenmedi. Florence `40`'ı `50` ile birleştiriyor: yakın sayılar riskli. torch bağımlılığı büyük |
| **B. Florence + Qwen, uyuşma = "emin"** | İkisi de çalışır; aynı değeri veren bölge "emin", ayrışan "emin değil" ve iki aday kullanıcıya sorulur | Yanlış "emin" 0/72; ayrışma bir düzeltme sorusuna dönüşür | Süre Qwen kadar; boş/soru sayısı artar (31/72) → düzeltme sayısı ölçütü yükselebilir |
| C. Set-of-Mark | Ek model yok | Ek bağımlılık yok | Tutarsız, fazla değer çok; tek başına önerilmez. Ancak B'deki gibi ikinci görüş olabilir |

Önerim: **önce yeni krokilerle (mimarın yeni test krokileri ve `ornekler/internet/`, yalnız okuma) A ve B'yi
ölçmek**; ürün kararını o ölçüme bırakmak. Ölçüt "kaç düzeltmede doğru plan": A'nın boşları (3) ile B'nin soruları
(31/72 ≈ 10/kroki) bu ölçütte doğrudan karşılaştırılabilir.

## Dosyalar

- `../set_of_mark/calistir.py`: R etiketli görsel + 3 Qwen çağrısı → `../set_of_mark/sonuclar/som.json`
  (görseller `gorseller/`, depoda değil).
- `../set_of_mark/olcum.py`: bölüm 1 tablosu → `../set_of_mark/sonuclar/olcum.json`.
- `calistir.py` (`.venv-deney/Scripts/python`): Florence-2 ve PaddleOCR tespitleri → `sonuclar/tespitler.json`.
- `olcum.py`: bölüm 2 → `sonuclar/olcum.json`.
