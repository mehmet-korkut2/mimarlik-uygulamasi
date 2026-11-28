# Okuma deneyi 03–07: Florence-2 ve Qwen3-VL

Tarih: 2026-11-28 · Ürün kodu değişmedi · **Yalnız okuma ölçüldü; 03–07 plana çevrilmedi.**

Doğru cevap: `dogru_cevaplar_03_07.py` (taslak, kullanıcı onayladı; 177 sayı, 30'u "?"). **Puan "?" olmayan 147
sayıyla**; "?" sayılar ayrı tabloda. Liste mimarla düzeltilirse yalnız `puanla_03_07.py` yeniden çalıştırılır
(modeller yeniden çalıştırılmaz). Okuma konumsuz: modelin okuduğu sayılar listeyle çoklu küme olarak eşleştirilir;
listede karşılığı olmayan her okuma "fazla".

Koşul: ham fotoğraf, tam görsel (01–02'de Florence için en iyi koşul). Florence-2-large 1 kez (deterministik),
Qwen3-VL 4B 3 kez, ürünün istemi (`okuma.ISTEM_SAYILAR`); tek fark cevap sınırı 2500 token (aşağıda).

> **Güncelleme (aynı gün, bölüm 7–10):** döndürme, örtüşen karolama, yön ağırlıklı oylama ve tek hane süzme ile
> Florence-2 **18 → 65/147 (%44), fazla 290 → 77**. Ama seçmeli düzeltme benzetiminde düzeltme sayısı (147) hepsini
> elle yazmakla aynı. Özet tablo: bölümlerin sonunda.

## Kısa sonuç

1. **İki model de 03–07'de çöküyor.** 147 sayının Florence **18'ini (%12)**, Qwen çalıştırma başına ortalama
   **20'sini (%14)** okuyor; fazla okuma 230–290. 01–02'de (24 sayı) Florence 20, Qwen 22–23 okuyordu. 01–02'deki
   sonuçlar 03–07'ye taşınmıyor; **A/B ürün kararı için Florence de Qwen de bu koşulda yeterli değil.**
2. **En büyük etken yazılış yönü:** sayıların **%46'sı yan (68), %14'ü ters (21)** yazılmış. Düz sayılarda Florence
   %29, Qwen %26; yanlarda %3 / %8, terslerde %0 / %5. Kutu içi (9) ve yakın/sıkışık (7) sayıları hiçbiri okumuyor.
3. **İki model de kendini tekrarlayan çıktıya düşüyor.** Qwen 15 çağrının 10'unda sınıra kadar aynı değeri yazdı
   (04'te "180" × 68, 06'da "298" × 73, 07'de "26" × 76); kesilmeyen iki çağrı ise 4 ve 10 etiketle erken durdu.
   Florence 04'te `1.5 2.5 3.5 … 99.5 …` diye sayı dizisi uydurdu, 07'de "-" tekrarladı.
4. **Florence ∩ Qwen uyuşması 01–02'deki kadar güvenli değil:** ikisinin aynı okuduğu 8–17 değerin 1–7'si listede
   yok (01–02'de 0). Bir kısmı sayım yapaylığı (aynı sayıyı iki model de birden çok okuyor), bir kısmı **listenin
   kendisi yanlış olabilir** (aşağıda, mimara gösterilecek).
5. **Ürün bulgusu:** sınırsız Qwen çağrısı yoğun krokide 27–28 dk takılıyor (ilk deneme); ürün `num_predict`
   koymuyor. Sınırla bile çağrı ortalaması ~7 dk.

## 1. Kategorilere göre okunan (147 puanlı sayı)

Florence 1 çalıştırma; Qwen #1 / #2 / #3 ve ortalama yüzde.

| Kategori | n | Florence-2 | Qwen #1 / #2 / #3 | Qwen ort. |
|---|---|---|---|---|
| **Hepsi** | 147 | 18 (%12) | 17 / 13 / 30 | %14 |
| Kroki 03 (çizgili, orta) | 13 | 9 (%69) | 7 / 6 / 8 | %54 |
| Kroki 04 (noktalı) | 26 | 2 (%8) | 0 / 0 / 6 | %8 |
| Kroki 05 (noktalı, zor) | 30 | 3 (%10) | 8 / 7 / 6 | %23 |
| Kroki 06 (noktalı, zor) | 44 | 3 (%7) | 0 / 0 / 2 | %2 |
| Kroki 07 (çizgili, kırmızı, yan çekilmiş) | 34 | 1 (%3) | 2 / 0 / 8 | %10 |
| Yazılış: düz | 52 | 15 (%29) | 12 / 9 / 20 | %26 |
| Yazılış: yan | 68 | 2 (%3) | 5 / 4 / 7 | %8 |
| Yazılış: ters | 21 | 0 | 0 / 0 / 3 | %5 |
| Yazılış: çapraz | 6 | 1 (%17) | 0 / 0 / 0 | %0 |
| Virgüllü | 18 | 3 (%17) | 0 / 4 / 0 | %7 |
| Yakın / sıkışık | 7 | 0 | 0 / 0 / 0 | %0 |
| Kâğıt: noktalı (04–06) | 100 | 8 (%8) | 8 / 7 / 14 | %10 |
| Kâğıt: çizgili (03, 07) | 47 | 10 (%21) | 9 / 6 / 16 | %22 |
| Renk: kırmızı (07) | 32 | 1 (%3) | 2 / 0 / 7 | %9 |
| Renk: mavi (07) | 2 | 0 | 0 / 0 / 1 | %17 |
| 7'si ">" gibi (07) | 2 | 0 | 1 / 0 / 1 | %33 |
| **Fazla** (listede yok) | — | 290 | 230 / 280 / 254 | — |

**Ayrı satırlar: tür**

| Tür | n | Florence-2 | Qwen #1 / #2 / #3 | Qwen ort. |
|---|---|---|---|---|
| Ölçü | 127 | 18 (%14) | 17 / 12 / 27 | %15 |
| Yükseklik notu (`H=`, `h1:`, `K.H=`) | 11 | 0 | 0 / 1 / 3 | %12 |
| Kutu içindeki sayı | 9 | 0 | 0 / 0 / 0 | %0 |

Yorum ve sınırlar:
- **Kâğıt ve renk etkisi ayrılamıyor:** noktalı kâğıt = 04–06 (en yoğun krokiler), kırmızı kalem = 07'nin hepsi
  (ayrıca yan çekilmiş). Bu satırlar kâğıdın/rengin değil kroki zorluğunun etkisini de taşıyor.
- **Virgül kaybı:** Florence 1 (05: 158,5 → 1585), Qwen #1 4 (25,5 → 255, 41,5 → 41, 105,5 → 105, 158,5 → 158),
  #3 2. Qwen'in ürün yolu (`okuma._sayi`) zaten ondalığı atıyor; burada ham etiket puanlandı.
- Yükseklik notlarında öneki sayıdan ayırmak gerekti ("h1.217" → 217, "1,217" değil); puanlama betiğinde yapıldı.

## 2. 07: 7'si ">" gibi yazılmış sayılar

| Sayı | Listede | Florence | Qwen #1 / #2 / #3 | Not |
|---|---|---|---|---|
| 267 | emin | ✗ | ✗ / ✗ / ✗ | |
| 107 | emin | ✗ | ✓ / ✗ / ✓ | |
| 137 | ? | — | — / — / — | 133 olabilir |
| 67 | ? | — | — / — / — | sol kapı; 63 olabilir |
| 157 | ? | — | — / — / — | |

07'de Florence yalnız 1 sayı okuyor; ">" biçimini ayrı ölçmek için önce 07'nin okunması gerekiyor (yan çekilmiş).

## 3. "?" sayılar (puana girmez)

Okunan aday: taslak değer ya da nottaki alternatif; — = hiçbiri okunmadı. 30 sayının yalnız 3'ünde Florence bir
aday okudu; Qwen'in okuduğu 8'i var.

| Kroki | Taslak | Alternatif | Florence | Qwen #1 / #2 / #3 | Uyuşma |
|---|---|---|---|---|---|
| 03 | 57 | 7 / 52 | 52 | 52 / 52 / 52 | 3/3 aynı (**52**) |
| 03 | 97 | 98 | — | — / — / — | |
| 03 | 5 | 55 | — | 55 / — / 5 | |
| 04 | ? | 675 / 67,5 | 67,5 | — / — / — | |
| 05 | 94,5 | 95,5 / 96,5 | — | — / 95,5 / — | |
| 05 | 98 | 90 | — | — / — / — | |
| 05 | 60 | 160 | — | 160 / — / — | |
| 05 | 73 | 23 | — | — / — / — | |
| 05 | 269 (`H=`) | 279 | — | — / — / — | |
| 05 | ? | 88 | — | 88 / — / — | |
| 06 | 26,6 | 26,10 / 26,5 | — | — / — / — | |
| 06 | 15 | | — | — / — / — | |
| 06 | 518 | | — | — / — / — | |
| 06 | 868 (kutu) | 898 | — | — / — / — | |
| 06 | 195 | | — | — / — / — | |
| 06 | 259 (`H=`) | 250 / 253 | — | — / — / — | |
| 06 | 88 | 48 | — | — / — / — | |
| 06 | 45 | | — | — / — / — | |
| 06 | 24 | | — | — / — / — | |
| 06 | 38 | 24 | — | — / — / — | |
| 07 | 27 | 112 | — | — / — / — | |
| 07 | 137 | 133 | — | — / — / — | |
| 07 | 104 | 107 | — | 107 / — / 107 | |
| 07 | 15 | | — | — / — / — | |
| 07 | 22,5 | 12,5 | — | — / — / — | |
| 07 | 50,5 | | — | — / — / — | |
| 07 | 23 | 25 | 25 | — / — / 23 | ayrışıyor |
| 07 | 67 | 63 | — | — / — / — | |
| 07 | 157 | | — | — / — / — | |
| 07 | 107 | | — | — / — / 107 | |

Mimara gösterirken: **03'teki "57?" için iki model de 4 okumada 52 diyor**; 07'deki "104?" için Qwen iki kez 107.

## 4. Florence ∩ Qwen: ikisinin uyuştuğu değerlerde hata

Her Qwen çalıştırması Florence ile değer kümesi olarak kesiştirildi (konum yok).

| Qwen | Ortak | Listede doğru | "?" adayı | Ortak hata | Hatalı değerler |
|---|---|---|---|---|---|
| #1 | 10 | 7 | 1 | 2 | 03: 56, 28 |
| #2 | 8 | 6 | 1 | 1 | 03: 56 |
| #3 | 17 | 8 | 2 | 7 | 03: 212, 56, 25, 28 · 05: 1585 · 06: 101, 101 |

- **Sayım yapaylığı:** 03'te 56 bir kez, 06'da 101 bir kez yazılı; iki model de bunları birden çok okuyor, fazlası
  "ortak hata" sayılıyor (56, 101 × 2). Konumla eşleştirmede bunlar aynı sayıya düşer.
- **Gerçek ortak hata:** 05'te 158,5 → 1585 (ikisi de virgülü kaybetti).
- **Listeye bakılacak (mimar):** 03'te iki model de **212** (listede `h2:217`), **25** (listede 24) ve **28**
  (listede yok) okuyor. Bağımsız iki model aynı değeri okuyorsa liste yanlış olabilir.
- Sonuç: 01–02'deki "uyuşmada yanlış 0" 03–07'de tekrarlanmadı, ama örnek çok küçük (ortak 8–17 değer, çoğu 03'ten).

## 5. Süre ve Qwen'in takılması

| | Süre / kroki | Not |
|---|---|---|
| Florence-2-large | 12–48 s (ort. ~34 s) | 01–02'de ~9 s; yoğun krokide uzun (tekrarlı) çıktı |
| Qwen3-VL 4B | 57–606 s (ort. ~7 dk) | 15 çağrının 10'u 2500 token sınırında kesildi |

- Sınırsız ilk denemede bazı çağrılar **27–28 dk** sürdü (58 dk'da 15 çağrının 3'ü bitmişti); çalıştırma
  durduruldu, sınırla yeniden yapıldı. Kesik cevaplarda tamamlanmış nesneler kurtarıldı; kesik cevaplar neredeyse
  tamamen aynı değerin tekrarı.
- **Ürün için:** `mimarlik/okuma.py` `num_predict` koymuyor; yoğun bir krokide kullanıcı 30 dk bekleyebilir. Bir
  sınır (ve tekrar algılayınca kesme) ürüne alınmalı (karar kullanıcının; uygulanmadı).

## 6. Neden ve sonraki adım önerisi

Ham gözlemler: fotoğraflar 2048 × 945 (03: 1152, 07 yatay); Florence görseli 768 × 768'e küçültüyor, bu yoğun
krokilerde rakamları birkaç piksele indiriyor. Sayıların %60'ı yan ya da ters. İki olası sebep, ikisi de ucuz test:

1. **Döndürerek okuma:** görseli 0° / 90° / 180° / 270° döndürüp dört kez okutmak, okunanları birleştirmek. Yan ve
   ters sayılar (89 / 147) için doğrudan hedef. Florence'le kroki başına ~2 dk.
2. **Karolama** (bölerek okuma): 01–02'de yardım etmedi (rakam karo sınırında bölünüyor), ama orada görsel seyrekti;
   03–07'de çözünürlük kaybı asıl sorun olabilir. Örtüşen karolarla denenmeli.

Ürün kararı (A: Florence, B: Florence + Qwen) bu iki test yapılmadan verilmemeli: bugünkü haliyle 03–07 düzeyindeki
bir krokide okuma, kullanıcıya ~130 düzeltme bırakıyor; "kaç düzeltmede doğru plan" ölçütünde mimarın elle ~1 saatlik
aktarımından iyi olmaz.

## 7. Döndürerek okuma (Florence-2, öneri 1)

Her kroki saat yönünde 0° / 90° / 180° / 270° döndürülüp Florence'e okutuldu (`dondurme_03_07.py`, puan
`puanla_dondurme.py`). 0° önceki çalıştırmayla birebir aynı (deterministik). **Birleşik:** her değer için açılar
arasındaki en büyük adet (aynı sayıyı iki açıda okumak bir kez sayılır). **2+ açı:** en az iki açıda okunan değerler.

| Kategori | n | 0° | 90° | 180° | 270° | **Birleşik** | 2+ açı |
|---|---|---|---|---|---|---|---|
| **Hepsi** | 147 | 18 (%12) | 17 | 3 | 21 | **43 (%29)** | 11 |
| Kroki 03 | 13 | 9 | 7 | 0 | 7 | 11 (%85) | 7 |
| Kroki 04 | 26 | 2 | 1 | 0 | **11** | 13 (%50) | 1 |
| Kroki 05 | 30 | 3 | 3 | 0 | 1 | 7 (%23) | 0 |
| Kroki 06 | 44 | 3 | 3 | 0 | 2 | 6 (%14) | 2 |
| Kroki 07 | 34 | 1 | 3 | 3 | 0 | 6 (%18) | 1 |
| Yazılış: düz | 52 | 15 | 8 | 0 | 9 | 19 (%37) | 8 |
| Yazılış: yan | 68 | 2 | 6 | 1 | 10 | 18 (%26) | 1 |
| Yazılış: ters | 21 | 0 | 2 | 2 | 1 | 4 (%19) | 1 |
| Yazılış: çapraz | 6 | 1 | 1 | 0 | 1 | 2 | 1 |
| Ölçü | 127 | 18 | 17 | 3 | 18 | 40 (%31) | 11 |
| Yükseklik notu | 11 | 0 | 0 | 0 | 1 | 1 | 0 |
| Kutu içi | 9 | 0 | 0 | 0 | 2 | 2 | 0 |
| Virgüllü | 18 | 3 | 0 | 0 | 1 | 4 | 0 |
| Yakın / sıkışık | 7 | 0 | 1 | 1 | 2 | 3 | 1 |
| 07 kırmızı | 32 | 1 | 3 | 3 | 0 | 6 | 1 |
| 7'si ">" gibi (07) | 2 | 0 | 1 | 0 | 0 | 1 (267 ✓, 107 ✗) | 0 |
| **Fazla** | — | 290 | 326 | 182 | 391 | **968** | 202 |

Bulgular:
- **Okunan 2,4 katına çıkıyor (18 → 43), ama fazla 3,3 katına (290 → 968).** Konum olmadan birleşik liste ürüne
  girmez: 43 doğru sayının yanında ~970 uydurma değer var. "2+ açı" fazlayı azaltıyor (202) ama doğruyu da (11).
- **Yan sayılar hâlâ çoğunlukla okunmuyor:** 68 yan sayının 50'si hiçbir açıda okunmadı (ters: 21'in 17'si). Döndürmek
  yönü düzeltiyor ama okumayı kurtarmıyor: asıl sorun yön değil, çözünürlük/yoğunluk gibi görünüyor.
- **04 belirgin istisna:** 270°'de 26 sayının 11'i (0°'de 2). 04'ün sayılarının çoğu aynı yöne yan yazılmış.
- **Tekrar döngüsü sürüyor:** 20 okumanın 7'si 48 s'de (1024 token sınırı) kesildi; fazlaların çoğu `100 101 102 …`,
  `1,5 2,5 3,5 …`, `198 198 198 …` gibi uydurma diziler. Bu dizileri süzmek fazlayı çok azaltır ama doğru sayıyı
  artırmaz.
- **"?" sayılar (birleşik):** 03'te "57?" bir açıda 57 okundu (0°'de iki model de 52 demişti); 07 "137?" 137;
  05 `H=269?` 279; 04 "?" 67,5. 06'daki "259?" → 1 ve "45?" → 2 eşleşmeleri puanlama yapaylığı (nottaki "Oda 1",
  "2/2" alternatif sanıldı); dikkate alınmamalı.
- Süre: kroki başına 4 açı ~1,5–3 dk.

Sonuç: **döndürme tek başına yetmiyor.** Okunanların neredeyse tamamı 03 ve 04'ten; zor krokilerde (05–07) en iyi
açı bile %10'un altında. Sıradaki deney **örtüşen karolama + döndürme** (rakamları büyütmek); ürün kararı hâlâ
beklemede.

## 8. Örtüşen karolama + döndürme (Florence-2)

Her fotoğraf 640 px kare, %30 örtüşen karolara bölündü (03 ve 07: 15, diğerleri: 10 karo); her karo 4 açıda okundu
(240 çağrı; `karo_dondurme_03_07.py`). Kutular özgün fotoğraf koordinatına geri çevrildi (dönüşüm sentetik testle
doğrulandı). Birleştirme (`puanla_karo.py`): (1) **süzme**: 4'ten çok sayı ya da aynı değeri 3+ kez içeren okuma =
uydurma dizi, atılır; (2) **kümeleme**: kutular örtüşüyorsa (IoU ≥ 0,3 ya da merkez içeride) aynı yer;
(3) **oylama**: yerde en çok okunan değer. Süzme ve kümeleme eşikleri tek denemede seçildi, ayarlanmadı.

| Kategori | n | Tam 0° (§1) | Tam 4 açı (§7) | Karo 0° | Karo 4 açı, süzmesiz | **Karo 4 açı, süzmeli** | ≥ 2 oy | Aday (üst sınır) |
|---|---|---|---|---|---|---|---|---|
| **Hepsi** | 147 | 18 (%12) | 43 (%29) | 37 (%25) | 53 (%36) | **54 (%37)** | 47 (%32) | 98 (%67) |
| Kroki 03 | 13 | 9 | 11 | 7 | 8 | 6 | 6 | 11 |
| Kroki 04 | 26 | 2 | 13 | 5 | 10 | 10 | 8 | 17 |
| Kroki 05 | 30 | 3 | 7 | 13 | 12 | 12 | 11 | 20 |
| Kroki 06 | 44 | 3 | 6 | 6 | 11 | 14 | 11 | 29 |
| Kroki 07 | 34 | 1 | 6 | 6 | 12 | 12 | 11 | 21 |
| Yazılış: düz | 52 | 15 | 19 | **27** | 22 | 20 | 18 | 41 |
| Yazılış: yan | 68 | 2 | 18 | 7 | 23 | **26** | 21 | 44 |
| Yazılış: ters | 21 | 0 | 4 | 2 | 7 | 7 | 7 | 11 |
| Yazılış: çapraz | 6 | 1 | 2 | 1 | 1 | 1 | 1 | 2 |
| Ölçü | 127 | 18 | 40 | 30 | 46 | 47 | 41 | 86 |
| Yükseklik notu | 11 | 0 | 1 | 4 | 4 | 4 | 3 | 7 |
| Kutu içi | 9 | 0 | 2 | 3 | 3 | 3 | 3 | 5 |
| Virgüllü | 18 | 3 | 4 | 3 | 3 | 3 | 3 | 10 |
| Yakın / sıkışık | 7 | 0 | 3 | 2 | 2 | 4 | 2 | 6 |
| Kâğıt: noktalı | 100 | 8 | 26 | 24 | 33 | 36 | 30 | 66 |
| 07 kırmızı | 32 | 1 | 6 | 6 | 12 | 12 | 11 | 21 |
| 7'si ">" gibi (07) | 2 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| **Fazla** | — | 290 | 968 | 146 | 328 | **151** | 74 | 1091 |

"Aday": bir yerde okunan bütün farklı değerler; doğru değer adaylar arasında mı (düzeltme ekranı yerin adaylarını
gösterse kullanıcının seçebileceği üst sınır). Kroki başına yer (küme) sayısı: 18 / 28 / 40 / 34 / 39.

Bulgular:
- **Okunan 3 katına çıkıyor (18 → 54), fazla yarıya iniyor (290 → 151).** İlk kez hem doğru artıyor hem fazla
  azalıyor: konumla birleştirme, döndürmenin getirdiği tekrarları topluyor; süzme uydurma dizileri atıyor (328 → 151).
- **Karolama tek başına (0°) zor krokilerde etkili:** 05'te 3 → 13, yükseklik notu 0 → 4, kutu 0 → 3. Çözünürlük
  sorunu doğrulandı.
- **Döndürme yan ve ters yazıyı açıyor:** karo 0° → 4 açı yan 7 → 26, ters 2 → 7.
- **Ama oylama düz sayılarda zarar veriyor:** düz 27 (karo 0°) → 20. Döndürülmüş karolar düz sayıyı yanlış okuyup
  oylamada doğruyu yeniyor. Oylamayı yazı yönüne göre ağırlıklandırmak (ör. kutunun en/boy oranına uyan açıyı
  tercih etmek) ucuz bir sonraki adım.
- **Aday listesi 98/147 (%67):** doğru değer çoğu yerde adaylar arasında. Düzeltme ekranında "bu yerde 160 mı 180
  mi?" gibi seçmeli soru olursa düzeltme yazmaktan hızlı olabilir.
- **Kalan fazlanın çoğu tek haneli** (`1`, `2`, `3`, `4` …: çizgi parçaları) ve birkaç **Arap–Hint rakamı**
  (`١٠٢٠`, Florence'in çıktısı). Tek haneleri atmak fazlayı belirgin azaltır; ama listede 5, 11, 12 gibi kısa
  ölçüler de var, bu yüzden uygulanmadı (yeni krokilerle karar).
- **Hâlâ zayıf:** virgüllü (3/18; 158,5 → 1585, 236,5 → 2365, 42,5 → 42), 07'deki ">" gibi 7'ler (0/2),
  çapraz (1/6).
- **"?" sayılar:** 06 "868?" 868, 07 "15?" 15, 07 "23?" 23 okundu; 06 "26,6?" → 26,10 (alternatif). 06 "259?" → 1
  ve "45?" → 2 yine puanlama yapaylığı (§7).
- **Süre:** kroki başına 4,7–8,7 dk (40–60 çağrı, GTX 1650). Qwen'in ~7 dk/çağrısından hızlı ama tam görselden
  (~35 s) çok yavaş. Açı sayısını yazı yönüne göre azaltmak ya da yalnız sayı olabilecek bölgeleri okutmak süreyi
  düşürür.

Sonuç: **03–07'de en iyi okuma bu (%37, fazla 151); ama ürün için hâlâ yetersiz** (147 sayının 93'ü okunmuyor ya da
yanlış). Ürün kararı (A/B) yine bekliyor. Sıradaki ucuz adımlar: (1) yön ağırlıklı oylama, (2) tek hane süzme,
(3) aday listesini düzeltme ekranına seçenek olarak vermek. Hepsi yeni krokilerle doğrulanmalı (bu eşikler 03–07'ye
bakılarak konursa aynı aşırı uyma riski).

## 9. Yön ağırlıklı oylama (aynı kayıtlar, model çağrılmadı)

Fikir: model yazıyı doğru yönde gördüyse kutu **kendi okuduğu (döndürülmüş) görselde** yatay olur. Kendi
çerçevesinde dikey kutulu okumanın oyu 0,2 (tek haneli okuma hariç, doğal olarak dar); ayrıca 0° okumasına × 1,5
öncelik denendi (`puanla_karo_yon.py`).

| Kategori | n | Çoğunluk (§8) | Yön ağırlıklı | Yön + 0° önceliği |
|---|---|---|---|---|
| **Hepsi** | 147 | 54 | **59 (%40)** | **59 (%40)** |
| Düz | 52 | 20 | 21 | 22 |
| Yan | 68 | 26 | 29 | 28 |
| Ters | 21 | 7 | 8 | 8 |
| 07 (kırmızı, yan çekilmiş) | 34 | 12 | 16 | 16 |
| **Fazla** | — | 151 | 131 | 125 |

Çoğunluğa göre 6 sayı kazanıldı (06: 11, 158; 07: 27/260, 211, 306, 246), 1 kaybedildi (05: 303). Düz sayılardaki
kayıp (karo 0°'de 27) yalnız kısmen geri geldi.

## 10. Duyarlılık, tek hane süzme, seçmeli düzeltme benzetimi (`puanla_karo_son.py`)

**Duyarlılık** (doğru / fazla; dik ağırlığı × 0° önceliği):

| Dik ağırlığı \ 0° önceliği | 1,0 | 1,5 | 2,0 | 3,0 |
|---|---|---|---|---|
| 1,0 (çoğunluk) | 54 / 151 | 57 / 136 | 53 / 152 | 49 / 163 |
| 0,5 | 60 / 130 | 59 / 124 | 59 / 131 | 54 / 137 |
| 0,2 | 59 / 131 | 59 / 125 | 61 / 126 | 58 / 133 |
| 0,0 | 59 / 136 | 59 / 129 | 60 / 131 | 58 / 136 |

Dik ağırlığı ≤ 0,5 olduğu sürece sonuç 58–61 doğru, 124–137 fazla: **kazanç katsayıya bağlı değil** (aşırı uyma
riski düşük). 0° önceliğini büyütmek (3,0) zararlı: düz sayıyı öne alırken yan sayıyı yanlış 0° okumasına
kaptırıyor.

**Tek hane + ASCII dışı süzme** (dik 0,2, 0° önceliği 1,5): tek haneli okumalar ve Arap–Hint rakamları atılır.

| | Doğru /147 | Fazla |
|---|---|---|
| Süzmesiz | 59 | 125 |
| **Süzmeli** | **65 (%44)** | **77** |

Doğru da artıyor (05: 11 → 16, düz: 22 → 26): tek haneli gürültü bazı yerlerde oylamayı bozuyormuş. Risk: listede
puanlı tek haneli sayı yok (yalnız 03 "5?"); gerçek krokide 5 gibi kısa ölçüler (basamak, girinti) olabilir. Ürüne
alınırsa tek haneli okuma atılmamalı, "emin değil" işaretlenmeli. Kalanlar: virgüllü 4/18, ">" gibi 7 0/2, çapraz
1/6.

**Seçmeli düzeltme benzetimi** (ana ölçüt "kaç düzeltmede doğru plan" için kaba kestirim): her yerde yön ağırlıklı
puana göre sıralı adaylar; ekranda 1. aday çizilir. Yanlış yerde 2./3. aday listedeki bir sayıysa 1 düzeltme
(seçim), değilse 1 düzeltme (sil); hiç bulunmayan sayı 1 düzeltme (yaz). Konumsuz (doğru değer yanlış yerde okunmuş
olabilir) ve sayı–duvar bağlama düzeltmeleri dahil değil.

| Yöntem | 1. aday doğru | Seçim | Sil | Yaz | **Düzeltme** |
|---|---|---|---|---|---|
| Çoğunluk | 47 | 13 | 90 | 87 | 190 |
| Yön ağırlıklı | 50 | 17 | 83 | 80 | 180 |
| **Yön ağırlıklı + süzme** | 58 | 15 | 58 | 74 | **147** |
| Taban: hiç okuma yok (hepsini yaz) | 0 | 0 | 0 | 147 | 147 |

("1. aday doğru" 58: yer başına bütün sayı dizisi doğru olmalı; "45 45" gibi tek kutuda iki sayı yarım doğruysa
sayılmaz, bu yüzden §10 süzme tablosundaki 65'ten az.)

**Bu en önemli sonuç:** en iyi okuma ayarında bile 03–07'de düzeltme sayısı (147) hepsini elle yazmakla aynı:
okunan her doğru sayıya karşılık bir yanlış yer silinmek zorunda. Silme ve seçim yazmaktan hızlı olduğu için **süre**
yine kısalabilir, ama yalnız düzeltme sayısıyla bakılınca kazanç yok. Ürün için iki şart: (1) yanlış yerleri azaltmak
(sayı olmayan kutuyu baştan elemek: ör. tik/ölçü çizgisine yakın olmayan kutu düşük güven), (2) her yerin "emin /
emin değil" ayrımı, böylece emin olmayan yerler sorulur, silinmez.

## Bütün denemelerin özeti (03–07, 147 puanlı sayı, Florence-2-large)

| Deneme | Doğru | Fazla | Süre / kroki |
|---|---|---|---|
| Tam görsel 0° (§1) | 18 (%12) | 290 | ~35 s |
| Qwen3-VL tam görsel, 3 çağrı ort. (§1) | 20 (%14) | 230–280 | ~7 dk |
| Tam görsel 4 açı (§7) | 43 (%29) | 968 | ~2 dk |
| Karo 0° (§8) | 37 (%25) | 146 | ~1,5 dk |
| Karo 4 açı, çoğunluk (§8) | 54 (%37) | 151 | 4,7–8,7 dk |
| Karo 4 açı, yön ağırlıklı (§9) | 59 (%40) | 125 | aynı |
| **Karo 4 açı, yön ağırlıklı + tek hane süzme (§10)** | **65 (%44)** | **77** | aynı |

## Dosyalar

- `dogru_cevaplar_03_07.py`: doğru cevap listesi (taslak, onaylı).
- `okuma_03_07.py`: Florence (`.venv-deney`) ve Qwen (`.venv`) ham cevapları → `sonuclar/okuma_03_07.json`.
- `puanla_03_07.py`: bu rapordaki tablolar → `sonuclar/puan_03_07.json` (yalnız bu betik yeniden çalıştırılır).
- `dondurme_03_07.py` + `puanla_dondurme.py`: bölüm 7.
- `karo_dondurme_03_07.py` (`.venv-deney`) + `puanla_karo.py`: bölüm 8 → `sonuclar/karo_dondurme_03_07.json`.
- `puanla_karo_yon.py`: bölüm 9; `puanla_karo_son.py`: bölüm 10. Liste düzelince bütün `puanla_*` betikleri model çağırmadan yeniden çalışır.
