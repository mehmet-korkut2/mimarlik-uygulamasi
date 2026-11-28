# Okuma deneyi 03–07: Florence-2 ve Qwen3-VL

Tarih: 2026-11-28 · Ürün kodu değişmedi · **Yalnız okuma ölçüldü; 03–07 plana çevrilmedi.**

Doğru cevap: `dogru_cevaplar_03_07.py` (taslak, kullanıcı onayladı; 177 sayı, 30'u "?"). **Puan "?" olmayan 147
sayıyla**; "?" sayılar ayrı tabloda. Liste mimarla düzeltilirse yalnız `puanla_03_07.py` yeniden çalıştırılır
(modeller yeniden çalıştırılmaz). Okuma konumsuz: modelin okuduğu sayılar listeyle çoklu küme olarak eşleştirilir;
listede karşılığı olmayan her okuma "fazla".

Koşul: ham fotoğraf, tam görsel (01–02'de Florence için en iyi koşul). Florence-2-large 1 kez (deterministik),
Qwen3-VL 4B 3 kez, ürünün istemi (`okuma.ISTEM_SAYILAR`); tek fark cevap sınırı 2500 token (aşağıda).

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

## Dosyalar

- `dogru_cevaplar_03_07.py`: doğru cevap listesi (taslak, onaylı).
- `okuma_03_07.py`: Florence (`.venv-deney`) ve Qwen (`.venv`) ham cevapları → `sonuclar/okuma_03_07.json`.
- `puanla_03_07.py`: bu rapordaki tablolar → `sonuclar/puan_03_07.json` (yalnız bu betik yeniden çalıştırılır).
