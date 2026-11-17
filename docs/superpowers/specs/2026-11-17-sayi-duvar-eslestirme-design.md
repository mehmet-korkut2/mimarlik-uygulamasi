# Sayı–Duvar Eşleştirme: Tasarım

Tarih: 2026-11-17 · Faz 2 · Durum: **onaylandı (2026-11-17)**

İlgili:
- OCR sonuçları:
  - `deneyler/ocr_karsilastirma/RAPOR.md`
  - `deneyler/konum_deneyi/RAPOR.md`
  - `deneyler/bul_kes_okut/RAPOR.md`
  - `deneyler/cizgi_silme/RAPOR.md`
- Gerçek sayı kutuları: `deneyler/bul_kes_okut/konumlar.py`. Kullanıcı tarafından doğrulandı.
- Gerçek kenar parçaları ve eşleştirme: `deneyler/eslestirme/gercek_eslestirme.py`. Görsel `gorseller/gercek_eslestirme_*.jpg`; **kullanıcı onayı bekliyor**.

## 1. Amaç ve neden

Faz 2'de geometri krokideki yazılı sayılardan kurulacak (CLAUDE.md, 2026-11-16 yaklaşım değişikliği).
Qwen3-VL 4B sayıları iyi **okuyor** (24 sayıdan 23), ama sayının hangi duvara ait olduğunu
söyleyemiyor; kutuları güvenilmez (02'de yarısı yanlış yerde). Bu tasarım, her sayıyı fotoğraftan
bulunan **kenar parçasına** bağlayan adımı tanımlar ve ölçer.

Çıktı, bir sonraki adımın (geometri kurma + toplam kontrolü + kullanıcı onayı) girdisidir. O adım
mimarın cevaplarına bağlı olduğu için bu tasarımın dışında. Ama bu tasarım o adımın ihtiyaç duyacağı
çıktı biçimini şimdiden tanımlar (bölüm 6).

## 2. Hedefler, hedef dışı, anti-hedefler

**Hedefler**
1. Fotoğraftan kenarları ve kenar parçalarını bulmak (duvar parçaları ve açıklıklar).
2. Her okunan sayıyı bir kenar parçasına bağlamak; bağlamanın nedenini kaydetmek.
3. Hatanın hangi adımdan geldiğini ayırabilecek, katmanlı bir ölçüm.
4. Üç yaklaşımın aynı ölçütle karşılaştırılması: ana yol, model karşılaştırması, taban çizgisi.

**Hedef dışı**
- Geometri kurma, toplam kontrolü, DXF yazma, kullanıcı arayüzü.
- Eğik duvarlar, çift çizgili ya da taralı duvarlar, 03–07 krokileri.
- OCR iyileştirmesi. Kararla bırakıldı; okunan değerler olduğu gibi kullanılır.

**Anti-hedefler**
- Ölçüm sonucunu güzel göstermek için kuralları 01–02'deki tek tek sayılara göre ayarlamak.
  Eşikler genel ilkelerle seçilir (ör. karakter yüksekliğinin katı), ayarlama gerekçeleriyle raporlanır.
- Mimara bağlı bir anlamı sessizce varsaymak. Örneğin `90`'ı "kapı" diye işaretlemek: anlamı
  bilinmeyen sayı "bilinmiyor" olarak kalır.

## 3. Mimara bağlı kısımlar (bu tasarım bunları çözmez, işaretler)

Gerçek cevapta (`gercek_eslestirme.py`) bu sayılar bir parçaya **bağlandı** ama `ANLAM_BILINMIYOR`
ya da `KAPSAM_BELIRSIZ` olarak işaretlendi. Görselde turuncu.

| # | Soru | Nerede | Neden önemli |
|---|---|---|---|
| M1 | Bir kenar üstünde arka arkaya yazılan üç sayı "duvar parçası – açıklık (kapı) – duvar parçası" mı? Açıklık sayısı kapı genişliği mi, kasa dahil mi? | 01: `15/90/10` (K6). 02: `15/9-0/40` (K12). | Aynı desen iki krokide de var. Geometri kurarken parçalar toplanacak mı, açıklık ayrı mı çizilecek? |
| M2 | Bir T-birleşimin yanındaki sayı tüm kenarı mı, sadece o parçayı mı ölçüyor? | 02: `300` (K1), `200` (K10) | 02'de yatay toplam ancak `300` tüm üst kenar sayılınca tutuyor (300+45 ≈ 200+40+102; 345'e karşı 342). |
| M3 | 01'in toplamları bu okumalarla tutmuyor: yatay 180+40 ≠ 140+120, dikey 50+120 ≠ (10+90+15)+108. Okuma mı yanlış, yorum mu? | 01 | `15/90/10` belirsizliğiyle (CLAUDE.md) aynı yerde. |
| M4 | `X` işaretleri ne anlama geliyor? | 02: K1.1, K10.2 | Eşleştirmeyi etkilemez; parça türünü etkileyebilir. |
| M5 | Ölçüler iç ölçü mü, dış ölçü mü? (Tek çizgide duvar kalınlığı yok.) | Hepsi | Bir sonraki adım için gerekli. Burada sadece not. |

Bu tasarımdaki kural: Bir sayı **açıklık parçasına** ya da **birden fazla parçalı bir kenarın bir
parçasına** bağlanırsa `anlam = "bilinmiyor"` olur. Tek parçalı bir kenara bağlanırsa
`anlam = "uzunluk"` olur.

## 4. Yaklaşımlar

Eşleştirmenin dört alt adımı var:
1. kenarları bul,
2. sayıların yerini bul,
3. okunan değeri o yere ata,
4. yeri bir kenar parçasına bağla.

| | Nasıl | Artı | Eksi | Rol |
|---|---|---|---|---|
| **Y1: Geometrik** | Mürekkepten kenarlar bulunur. Kalan mürekkep sayı bölgeleri olur. Değer bölgeye Qwen kutusu + hane ipucuyla atanır. Bölge parçaya **ölçü işaretiyle**, yoksa en yakın mesafeyle bağlanır. | Hızlı, açıklanabilir, adım adım ölçülebilir. Kâğıttaki ölçü işaretini kullanır. | Kurallar 2 krokiye göre ayarlanır; 03–07'de yeniden ele alınmalı. Değer atama hâlâ Qwen kutusuna dayanır. | **Ana yol** (kullanıcı seçimi) |
| **Y2: Numaralı parçalar** | Parçalar fotoğrafın üstüne P1, P2… diye çizilir. Qwen'e "her parçanın yanındaki ölçü ne?" diye sorulur. | Model bağlamı kullanır. Sayının yerini bulmaya gerek yok. | Qwen 4B'nin uzamsal becerisi zayıf. Etiketler sayıların üstüne binebilir. Hatanın nereden geldiği ayrılamaz. | **Tek seferlik karşılaştırma:** tek istem, 3'er çalıştırma |
| **Y3: Qwen kutusu → en yakın parça** | Qwen'in kutusu sayının yeri kabul edilir, en yakın parçaya bağlanır. | En basit. Yeni Qwen çağrısı gerekmez. | 02'de kutuların yarısı yanlış yerde. | **Taban çizgisi** |

## 5. Y1'in tasarımı (ana yol)

Girdi: fotoğraf + Qwen'in "sayı + kutu" cevabı. Bütün koordinatlar orijinal fotoğraf pikselinde.

### 5.1 Ön işleme
`deneyler/cizgi_silme/on_isleme.py` ürüne taşınır (`mimarlik/on_isleme.py`): mavi mürekkep maskesi.
Renk varsayımı (mavi) belgelenir. Kırmızı/çok renkli krokiler hedef dışı.

### 5.2 Kenar bulma (`mimarlik/kenar_bulma.py`)
1. Mürekkep maskesinde düz çizgi parçaları bulunur (olasılıksal Hough ya da eşdeğeri).
2. **Eksen açısı:** Parçaların uzunlukla ağırlıklı açı dağılımından fotoğrafın eğikliği (θ₀) bulunur.
   θ₀'a ya da θ₀+90°'ye ±15° içindeki parçalar yatay ya da dikey sayılır. Gerisi bu fazda eğik diye
   ayrılır ve kullanılmaz.
3. **Doğrudaşları birleştirme:** Aynı yöndeki, dik uzaklığı birbirine yakın ve üst üste binen ya da
   arası çok küçük olan parçalar tek çizgi olur.
4. **Duvar mı, ölçü işareti mi?** Kısa duvarlar (01'de K6.1 ≈ 33 px, 02'de K12.1 ≈ 20 px) ölçü
   işaretleriyle aynı boyda. Bu yüzden ayrım yalnız uzunlukla yapılmaz. Bir çizgi, iki ucu da başka
   duvarlara bağlanıyorsa (köşe ya da T-birleşim), ya da uzunsa, ya da bir açıklıkla bölünmüş bir
   duvarın doğrudaş devamıysa **duvardır**. Bir ucu bir duvara değip diğer ucu boşta olan kısa çizgi
   **ölçü işareti adayıdır**.
5. **Açıklık:** Aynı doğru üstünde, arasında mürekkep olmayan iki duvar parçası, aradaki boşluk makul
   bir aralıktaysa (eşik karakter yüksekliğine göre) tek kenarın parçalarıdır; boşluk `aciklik`
   parçası olur.
6. **Köşeler ve parçalar:** Yatay ve dikey çizgilerin kesişimleri ya da uç uca yakınlıkları köşedir.
   Köşeden köşeye bir **kenar** oluşur. Kenar, T-birleşimlerde ve açıklık uçlarında **parçalara**
   bölünür.
7. **Dış kontur:** Köşe grafiğindeki en büyük kapalı döngü saat yönünde sıralanır (`kontur_sirasi`).
   İç duvarlar konturda yer almaz.

### 5.3 Sayı bölgelerini bulma (`mimarlik/bolge_bulma.py`)
1. Bulunan duvarlar maskeden çizgi kalınlığı + küçük bir payla silinir.
2. Kalan mürekkebin bağlı bileşenleri bulunur. Çok küçük gürültü atılır.
3. Yatay yakınlıktaki bileşenler (bir rakam aralığı kadar) birleştirilip **bölge** olur.
4. Ölçü işareti adayları bölgelerden ayrı tutulur (5.5'te kullanılır).
5. Kapı yayı ve `X` gibi yazı olmayan bölgeler de bölge olarak çıkar. Değer atamada eşsiz kalmaları
   beklenir.

### 5.4 Değeri bölgeye atama (`mimarlik/eslestirme.py`)
- Qwen'in her (değer, kutu) öğesi ile her bölge arasında bir maliyet hesaplanır:
  - **mesafe:** bölge merkezi ile kutu merkezi arası, fotoğraf köşegenine bölünmüş;
  - **hane ipucu** (kullanıcı eklemesi): bölgenin genişlik/yükseklik oranından hane tahmini ile
    değerin hane sayısı arasındaki fark, ağırlık `w_hane` ile. Oran → hane katsayısı gerçek
    kutulardan bir kez kalibre edilir.
- **Bire bir atama:** toplam maliyeti en küçük olan atama (Macar yöntemi, `scipy.optimize.linear_sum_assignment`).
  Mesafe üst sınırını aşan çiftler yasaklanır.
- Eşsiz kalan değerler `yeri_bulunamayan` listesine gider (kullanıcı onayında gösterilecek). Eşsiz
  kalan bölgeler `okunmamis_bolgeler` olur.
- Ölçüm, hane ipucuyla (`w_hane > 0`) ve ipucusuz (`w_hane = 0`) ayrı ayrı yapılır.

### 5.5 Bölgeyi parçaya bağlama (`mimarlik/eslestirme.py`)
Sırayla:
1. **`isaret`:** Bir ölçü işareti adayının bir ucu bölgeye, diğer ucu bir parçaya değiyorsa, değdiği
   noktanın parçası seçilir.
2. **`temas`:** Bölgenin kendi mürekkebi bir parçaya değiyorsa (ör. `-108`'deki tire duvara bitişik),
   değme noktasının parçası seçilir.
3. **`en_yakin`:** Bölge merkezine dik mesafesi en küçük parça seçilir. İzdüşüm parçanın dışına
   düşerse uç noktaya olan mesafe kullanılır.

Bağlamanın nedeni kaydedilir. Raporda işaret, temas ve en yakın paylarıyla her birinin doğruluğu ayrı
gösterilir.

## 6. Çıktı biçimi (geometri adımı için sözleşme)

`mimarlik/eslestirme.py` içinde dataclass'lar. JSON'a çevrilebilir. Koordinatlar fotoğraf pikseli.

```
Parca:  id ("K3.2"), kenar_id ("K3"), tur ("duvar" | "aciklik"), bas (x, y), bit (x, y)
Kenar:  id, yon ("yatay" | "dikey"), parcalar [Parca], konturda (bool)
Olcu:   deger (int), bolge (x1, y1, x2, y2), parca_id (str | None),
        neden ("isaret" | "temas" | "en_yakin" | None), anlam ("uzunluk" | "bilinmiyor")
Kroki:  eksen_acisi_derece, kenarlar [Kenar], kontur_sirasi [kenar id, saat yönü],
        olculer [Olcu], yeri_bulunamayan [int], okunmamis_bolgeler [(x1, y1, x2, y2)]
```

Geometri adımı bunlarla şunları yapabilmeli:
- konturu sırayla dolaşıp her kenarın yönünü (yatay/dikey, θ₀'a göre) ve uzunluk sayısını almak,
- parçalı kenarlarda parçaların sırasını ve türünü görmek,
- anlamı bilinmeyen sayıları kullanıcıya sormak.

## 7. Ölçüm

### 7.1 Gerçek cevap
- `gercek_eslestirme.py`:
  - 01: 8 kenar, 10 parça (1'i açıklık).
  - 02: 12 kenar, 16 parça (1'i açıklık).
  - 24 sayının her biri bir parçaya bağlı. Mimara bağlı olanlar işaretli.
- `konumlar.py`: 24 gerçek kutu.

### 7.2 Ölçütler (bütün yaklaşımlarda aynı)
- **Eşleştirme (katı):** (değer, parça) çiftlerinin gerçek çiftlerle çoklu küme kesişimi, /24.
  Konum gerektirmez, Y2'ye de uygulanır.
- **Eşleştirme (gevşek):** Aynı ölçüt, parça yerine kenar düzeyinde. M2 tipi belirsizlikleri yumuşatır.
- Mimara bağlı sayılar (5 + 2 kapsam belirsiz) hem dahil hem hariç raporlanır.
- **Kenar bulma:** Bir gerçek parça, uçları ≤ 25 px içinde olan bir bulunan parça varsa bulunmuş
  sayılır (tür de karşılaştırılır). Sonuçlar: bulunan / kaçırılan / fazla. Ayrıca dış kontur sırası
  doğru mu (evet/hayır).
  - Eşleşen bulunan parça, gerçek parçanın kimliğini alır. Eşleşmeyenler `F1, F2…` olur ve doğru
    sayılmaz.
- **Bölge bulma (gerçekçi katman):** 24 gerçek kutunun kaçı bir bölgeyle örtüşüyor (kutu alanının en
  az yarısı). Ayrıca yazı olmayan bölge sayısı ve bölünme/birleşme sayısı.
- **Değer atama:** Doğru değeri alan bölge sayısı. Hane ipucuyla ve ipucusuz ayrı.
- **Süre:** Kroki başına bulma + atama + bağlama. Qwen süresi hariç; o önceki deneylerde ölçüldü.

### 7.3 Katmanlar

| Katman | Kenarlar | Sayı yerleri | Değerler | Neyi ölçer |
|---|---|---|---|---|
| **Ü: üst sınır** | gerçek | gerçek kutular | gerçek | sadece bağlama (5.5) |
| **A: ara** | bulunan | gerçek kutular | gerçek | kenar bulmanın bağlamaya etkisi |
| **G: gerçekçi** | bulunan | bulunan bölgeler | Qwen (3 çalıştırma) | uçtan uca, hane ipucuyla ve ipucusuz |

Ara katman kullanıcının istediği iki katmanın arasına benim eklediğim bir katman. Hiç maliyeti yok ve
kenar bulma hatasını, bölge ve değer hatasından ayırır.

**Qwen girdisi:** Yeni Qwen çağrısı yapılmaz. `deneyler/konum_deneyi/sonuclar/qwen_konum.json`'daki
3 çalıştırmanın (değer, kutu) listesi kullanılır. Bu çıktılar orijinal fotoğraftan alındı; koordinatlar
aynı olduğu için bölgelerle doğrudan karşılaştırılabilir. Fazla okunan değerler (3–5 / çalıştırma)
atamada eşsiz kalmalı. Kalmazsa hata olarak sayılır.

**Y3 (taban çizgisi):** Aynı Qwen çıktısı. Kutu merkezi en yakın parçaya bağlanır. Gerçek ve bulunan
parçalarla ayrı ayrı ölçülür.

**Y2 (karşılaştırma):**
- **Girdi:** Çizgileri silinmiş fotoğrafa **gerçek** parçalar P-numaralarıyla çizilir. Gerçek
  parçaların seçilme nedeni: soru "model, bağlamla bağlamayı geometriden iyi yapar mı?". Kenar
  bulmanın kalitesi bu soruyu karıştırmasın.
- **İstem:** "Her numaralı parçanın yanına yazılmış ölçü sayıları neler? JSON: {"P1": [..], ...}".
- **Çalıştırma:** 01 ve 02 için 3'er kez, `qwen3-vl:4b-instruct`, önceki ayarlarla (`num_ctx` 8192,
  çalıştırmalar arası model boşaltılır).
- **Karşılaştırma:** Ü katmanıyla karşılaştırılır.

### 7.4 Kontrol görselleri (`deneyler/eslestirme/gorseller/`, `.gitignore`'da)
- Bulunan kenar ve parçalar (gerçeklerle üst üste)
- Bulunan bölgeler
- Her katmanda bağlama: doğru yeşil, yanlış kırmızı, mimara bağlı turuncu; bağlama nedeni de yazılır.

## 8. Dosya yerleşimi

Ürün kodu `mimarlik/`, ölçüm `deneyler/eslestirme/`. Ana yol (Y1) seçildiği için kod ürüne yazılıyor;
Y2 ve Y3 atılabilir deney kodu.

| Dosya | İçerik |
|---|---|
| `mimarlik/on_isleme.py` | Mürekkep maskesi ve çizgi silme (deneyden taşınır, testleriyle) |
| `mimarlik/kenar_bulma.py` | 5.2 |
| `mimarlik/bolge_bulma.py` | 5.3 |
| `mimarlik/eslestirme.py` | Dataclass'lar (6), değer atama (5.4), bağlama (5.5) |
| `tests/test_on_isleme.py`, `test_kenar_bulma.py`, `test_bolge_bulma.py`, `test_eslestirme.py` | Sentetik görüntülerle birim testleri: çizilmiş oda, ölçü işareti, açıklık, `cv2.putText` sayılar |
| `deneyler/eslestirme/gercek_eslestirme.py`, `ciz_gercek.py` | Gerçek cevap (hazır) |
| `deneyler/eslestirme/olcum.py` | Ü/A/G katmanları, Y3 → `sonuclar/*.json`, `olcumler.md` |
| `deneyler/eslestirme/calistir_y2.py` | Y2 Qwen çağrıları → `sonuclar/y2.json` |
| `deneyler/eslestirme/RAPOR.md` | Sonuç ve yorum |

**Bağımlılık:** `scipy` (Macar yöntemi) ana `requirements.txt`'ye eklenir. Deney ortamında zaten var
(EasyOCR bağımlılığı). `mimarlik/` modülleri yalnız `cv2`, `numpy` ve `scipy` kullanır, böylece iki
ortamda da çalışır.

## 9. Riskler

- **Kenar bulma en kırılgan adım.** Kısa duvar ile ölçü işaretini ayırmak (5.2/4) ve açıklığı iki ayrı
  duvardan ayırmak (5.2/5) yalnız iki krokiyle ayarlanıyor. Bu yüzden A katmanı ayrıca ölçülüyor.
- **Ölçü işareti sayının içinden geçebilir** (`102`). Bu durumda işaret, bölgenin bir parçası olarak
  görünür. Kural `temas` (5.5/2) bunu karşılamalı; ayrıca raporlanır.
- **Değer atama Qwen kutularına dayanıyor.** Hane ipucu kısmen telafi eder. Aynı haneli tekrar eden
  sayılarda (02'nin dört `40`'ı) karışma beklenir. Ancak değerler aynı olduğu için katı ölçütte
  zararsız; yanlış olan bağlama değil, sadece hangi `40`'ın hangisi olduğu.
- Örneklem 2 kroki, 24 sayı. Sonuçlar işaret, kanıt değil.

## 10. Kurucuya kalanlar (benim kararlarım ya da uygulamada seçilecekler)

- Eşikler (Hough parametreleri, birleştirme mesafeleri, açıklık aralığı, bölge birleştirme) karakter
  yüksekliğine göre seçilir; değerleri ve gerekçeleri raporda yazılır.
- **Karakter yüksekliği:** Ürün kodunda sabit tahmin değil, mürekkep bileşenlerinin medyan
  yüksekliğinden tahmin edilir. Böylece gerçek kutulara bağımlılık olmaz; kalibrasyon yalnız hane
  katsayısında.
- `w_hane` için tek bir değer seçilir (gerekçesi raporda). Izgara araması yapılmaz; aşırı uyumu önlemek
  için.
- **Y2 etiket yerleşimi:** parça ortası, beyaz zeminli küçük etiket. Sayıların üstüne binerse kaydırılır.

## 11. Bitti sayılır

- `mimarlik/` modülleri testleriyle hazır; bütün testler geçiyor.
- Ü, A ve G katmanları (G'de hane ipuçlu ve ipuçsuz), Y2 ve Y3 ölçülmüş.
- Kenar bulma puanı ve kontrol görselleri hazır.
- `RAPOR.md` hatanın hangi adımdan geldiğini gösteriyor ve sonraki adım için öneri içeriyor.
- `git status`'ta görsel yok; commit + push yapılmış.
