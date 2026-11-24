# Hata Analizi: Bütün Deneylerdeki Hatalar ve Kroki Çizim Kuralları

Tarih: 2026-11-24 · Kod değiştirilmedi. Kaynaklar: `../ocr_karsilastirma/`, `../konum_deneyi/`, `../bul_kes_okut/`,
`../cizgi_silme/`, `../eslestirme/` (raporlar ve `sonuclar/*.json`), iskeletin 01–02 çalıştırması (`output/adim0`,
`output/adim2`; `.gitignore`'da) · Karşılaştırılan belge: `kroki_cizim_kurallari.pdf` (24.11.2026, 8 kural)
· Bağlama matrisi (bölüm 1.5, 2) yeniden üretilir: `y2_hatalar.py` (iskelet girdisi: `sonuclar/iskelet_adim0.json`)

## Kısa cevap

1. **Hataların çoğu çizimden geliyor, ve ölçülen hataların büyük kısmını çizim kuralları çözebilir.** Bağlama
   aşamasında 288 denemenin 110'u hatalı (24 sayı × 12 deneme). Bu 110 hatanın:
   - 59'u (%54) PDF'teki kurallarla doğrudan çözülür (kural 3, 4, 5 ve tik uzunluğu eklenmiş kural 2);
   - 31'i (%28) yalnızca kısmen çözülür (kısa duvar parçaları; PDF'te bunu tam çözen bir kural yok);
   - 20'si (%18) çizimle çözülmez (Qwen'in kutu kayması, uydurma değer, kapı sembolünün gürültüsü).
2. **En büyük iki sınıf kısa duvar parçası (31) ve kapı boşluğu (27).** İkisi de 01'deki `10 / 90 / 15` ve
   02'deki `15 / 9-0 / 40` kapı dizilerinde toplanıyor. Kural 5 (K90) kapıyı çözüyor. Kısa parçalar için PDF'e
   bir kural eklenmeli: **"Kısa duvar parçasını da en az iki rakam boyu çiz."** Kroki zaten ölçeksiz olduğu
   için bunun çizene maliyeti yok.
3. **Tek okuma hatası (`102` → `162`) en tehlikelisi:** 02'yi okuyan 27 Qwen çalıştırmasının 21'inde var ve
   iskelet onu "emin" diye işaretliyor. Kural 4 tam bu hatayı hedefliyor.
4. **Kural 1, 6, 7 ve 8, 01–02'deki hiçbir hatayı çözmüyor.** Gereksiz değiller ama kanıtları yok (çok oda,
   pencere, kalınlık ve çapraz ölçü 01–02'de yok). Kural 1 ("Oda 1") ve 7 ("d=25") yeni bir hata türü
   getirebilir: program içlerindeki rakamı ölçü sanar.
5. **PDF'te düzeltilmesi gereken üç iddia var:**
   - "7 krokiyle denedik": ölçüm yalnız 01–02'de yapıldı.
   - "24 sayıdan 23": ürünün koşulunda 22.
   - "Tik bulunduğunda 9/9 doğru": yalnız gerçek kutularla. Gerçekçi koşulda tireyle bağlananların
     %56'sı doğru (36'da 20), ve iskeletin "emin" dediği 8 ölçünün 3'ü yanlış.

## Yöntem ve sınırlar

- **Hata birimi:** Her aşamada bir sayının bir denemede yanlış olması ("görülme"). Aynı sayının aynı sebeple
  tekrar eden hatası "farklı hata" olarak bir kez sayılır.
- **Aşamalar ayrı sayılır, toplanmaz.** Aynı kök hata birkaç aşamada görünebilir: `162`, okumada da
  bağlamada da hata sayılır.
- **Doğru cevap:** kullanıcının verdiği 24 sayı (`dogru_cevaplar.py`), elle çizilen gerçek kutular
  (`konumlar.py`) ve gerçek sayı–parça eşlemesi (`gercek_eslestirme.py`). Mimarın duvar boylarıyla doğrulama
  hâlâ yok.
- **Sınıflandırma benim yargım.**
  - Kural: değer yanlışsa okuma ya da değer atama sınıfına girer; değer doğru ama parça yanlışsa kenar
    ya da çizim sınıfına.
  - Bir hatanın birden fazla sebebi varsa birincil sebep sayıldı, ikincisi notta.
- **Bulunan kenar katmanları** (A, G, Y2 bulunan, iskelet) X değişikliğinden önceki kenar bulma koduyla
  (`40d19d1`) gerçek parçalara eşlendi; ölçümler o kodla yapılmıştı.
- **Veri azlığı:** 2 kolay kroki, 24 sayı. Oranlar yön göstermek için.

## 1. Hata envanteri (aşama aşama)

### 1.1 Okuma: Qwen, bütün fotoğraf

5 koşul × 3 çalıştırma × 24 sayı = 360 okuma: sadece sayı (GPU), sadece sayı (CPU), sayı + kutu,
çizgi silme, ürün koşulu.

| # | Kroki | Sayı | Ne oldu | Kaç çalıştırmada | Sınıf |
|---|---|---|---|---|---|
| O1 | 02 | `102` | `162` okundu | 11 / 15 (CPU'da 0/3) | S1 çizgi sayının içinden |
| O2 | 02 | `90` (`9/0`) | `96` okundu | 1 (sayı + kutu #3) | S1 |
| O3 | 02 | dört `40`'tan biri | kaçtı | 5 (GPU 2/3, CPU 3/3); çizgi silinince 0/6 | S2 kâğıt çizgisi |
| O4 | 02 | `240` | kaçtı | 2 (sayı + kutu #1, ürün #2) | S5 Qwen kaçırma |
| O5 | 02 | `15` | kaçtı | 1 (ürün #1) | S5 |
| O6 | 02 | `200` | kaçtı | 1 (ürün #3) | S5 |
| O7 | 01, 02 | fazla `40`, `45`, `200`, `50`, `100`, `15` | aynı sayıyı tekrar yazdı | 27 fazla sayı (26'sı kutu istenen koşullarda) | S4 Qwen tekrar / uydurma |

**Toplam:** 21 yanlış ya da kaçan okuma, 27 fazla sayı.

**EasyOCR** (tek çalıştırma): 24 sayının 19'unu kaçırdı ve 16 uydurma sayı üretti. Yöntem bu yüzden
bırakıldı; el yazısı için klasik OCR yetersiz (sınıf S6). **Gemini**'nin hiç hatası yok.

### 1.2 Okuma: kesitten (bırakılan yöntem)

3 çalıştırma × 24 sayı = 72 okumanın 29'u hatalı.

| Sayı | Okunan | Sınıf |
|---|---|---|
| 02 `102` | `162` ×3 | S1 |
| 02 `90` (`9/0`) | `960` ×3 | S1 |
| 01 `40`, 02 `45` ×3 sayı, 02 `40` ×2 sayı, 02 `240` | YOK, `55`, `5`, `25`, `15`, `120`; toplam 21 okuma | S3 el yazısı `4` ≈ `u` (yalnız kesitte) |
| 01 `108` | `80` (1 kez) | S3, kesitte bağlam kaybı |
| 01 `90` | YOK (1 kez) | S3 |

`4` içeren sayıları bütün fotoğrafta hiç kaçırmadı. Yani bu hata el yazısının değil, kesitte bağlamın
kaybolmasının sonucu; ürün bu yöntemi kullanmıyor.

### 1.3 Konum: Qwen kutuları

81 kutu:

| | Doğru | Yakın | Yanlış |
|---|---|---|---|
| 01 | 18 | 9 | 4 |
| 02 | 7 | 17 | 26 |

02'de yazı yoğun ve küçük, aynı sayı birçok kez geçiyor:
- Etiket ile kutu karışıyor: bir `40`'ın kutusu `45` etiketli.
- 02 #1'de 8 kutu sıra halinde uydurulmuş.

Bunun bağlamaya etkisi değer atama hatası olarak görünüyor (1.5'te S7).

### 1.4 Kenar bulma (parça düzeyi)

| Kroki | Gerçek parça | Bulunan | Kaçan | Fazla | Sebep |
|---|---|---|---|---|---|
| 01 | 10 | 6 | 4 | 0 | Kapının yanındaki `10` ve `15` duvarları 33 ve 50 px (h = 37 px; en kısa çizgi sınırı h) **[S10]**. Komşu `120` duvarı ucu boşta kalınca budandı **[S10]**. Kapı açıklığı iki yanı olmadığı için oluşmadı **[S11]** |
| 02 | 16 | 11 | 5 | 11 | Üst duvar T-birleşimde bölünmedi: iç duvarın üst ucu 2,4h, duvar sayılmadı **[S10]**, köşe X'li **[S13]**. İç kapılı duvarın 3 parçası yok: kapının iki yanındaki parça 16–20 px kaymış, açıklık hizalama payı h/2 ≈ 12 px **[S11]** |

02'deki 11 fazla parçanın kaynağı:
- 9'u küçük odadaki kapı kanadı, kapı yayı, `9/0` ve X çizgileri **[S12, S13]**;
- 2'si kâğıt destesinin kenarı ve arkadaki koyu zemin **[S14]**. Eşleştirme raporu fazlaların hepsini
  küçük odaya bağlıyordu; bu bir düzeltme.

Geliştirme sırasında bir hata daha vardı: 01'de fotoğrafın kenarındaki mavi kumaş eksen açısını −17°'ye
çekti. Kodla düzeltildi (kalın leke temizliği) **[S14]**.

### 1.5 Bağlama: sayı × katman

**Katmanlar** (sayı başına 12 deneme):

| Katman | Kenarlar | Kutu ve değer | Deneme |
|---|---|---|---|
| Ü | gerçek | gerçek | 1 |
| A | bulunan | gerçek | 1 |
| G | bulunan | Qwen | 3 |
| Y2g | gerçek | Qwen'e numaralı parça sorusu | 3 |
| Y2b | bulunan | Qwen'e numaralı parça sorusu | 3 |
| İsk | bulunan | birleşik yol (iskeletin ilk çalıştırması) | 1 |

Hatasız sayılar tabloda yok: 01 `180` ve 02 `45 üst sağ`'ın yalnız 1–2 hatası var, onlar tabloda.

| Kroki | Sayı | Hata /12 | Katmanlar ve sınıflar |
|---|---|---|---|
| 02 | `15` | **12** | Ü, A, G#3, Y2g ×3, Y2b ×3, İsk: S11 · G#1–2: S7 |
| 02 | `90` | **11** | Ü, A, Y2g ×2, Y2b ×3, İsk: S11 · G#1–2: S7 · G#3: S1 (`96`) |
| 01 | `10` | 9 | Ü: S9 (eğri kılavuz çizgi) · A, G ×3, Y2b ×3, İsk: S10 |
| 01 | `15` | 9 | A, G ×3, Y2b ×3, İsk: S10 · Y2g#2: S11 (`15` ile `90` yer değiştirdi) |
| 01 | `90` | 9 | A, G#1, Y2g#2, Y2b ×3, İsk: S11 · G#2–3: S7 |
| 01 | `120 sol` | 8 | A, G ×3, Y2b ×3, İsk: S10 |
| 01 | `40` | 8 | A, Y2g ×3, Y2b ×2, İsk: S8a · G#3: S7 |
| 02 | `300` | 8 | A, G#1, G#3, Y2b ×3, İsk: S10 · G#2: S7 |
| 01 | `50` | 7 | Y2g ×3, Y2b ×2, İsk: S8a · G#3: S7 |
| 02 | `102` | 7 | G#1, G#3, Y2g ×2, Y2b ×2, İsk: S1 (`162`) |
| 01 | `108` | 5 | Ü, A, G ×3: S8b (kısa tire bulunamadı, köşede). Y2 ve iskelet doğru |
| 02 | `45 üst sol` | 5 | Ü, A, G ×3: S8b. Y2 ve iskelet doğru |
| 02 | `45 alt` | 3 | G#2: S7 · Y2b#3, İsk: S12 (kapı kanadı/yayı parçasına gitti) |
| 01 | `180` | 2 | Y2b#1, #3: S15 (Qwen komşu parçaya yazdı) |
| 01 | `120 sağ`, `140` · 02 `40 sağ alt`, `200 alt`, `240` | 1'er | G ya da İsk: S7 (değer başka bölgeye gitti) |
| 02 | `200 sol` | 1 | Y2g#3: S15 (`100` yazdı) |
| 02 | `40 üst` | 1 | İsk: S11 |

**Toplam: 110 / 288.**

**Fazla bağlamalar** (sayısı olmayan yere değer):
- **G:** 14 değer yazı olmayan bölgeye gitti (01: 2, 02: 12).
- **Y2b:** 27 değer eşleşmeyen parçaya yazıldı:
  - 9'u X'li parçalara **[S13]**;
  - 18'i küçük odanın kapı kanadı, yay ve `9/0` parçalarına **[S12]**;
  - bunların içinde krokide hiç olmayan değerler var: `180` ×3, `150` ×4, `100`, `120`, `60`, `12` **[S15]**.

### 1.6 İskelet: geometri ve "emin" işaretleri

| Kroki | Sonuç | Sebep |
|---|---|---|
| 01 | Dış kontur yok | Kapı dizisinin kısa parçaları ve `120 sol` bulunamadı (S10, S11) |
| 02 (önce) | Kapanmıyor: yatay 57, dikey 85 cm | Kontur iptal edilen köşeyi içeriyordu (S13); `300` bölünmemiş üst kenarda (S10); `102` → `162` tek başına yaklaşık 60 cm (S1) |
| 02 (X kuralından sonra) | Dış kontur yok | Gerçek dış hat iç kapılı duvardan geçiyor, o duvar bulunamıyor (S11) |

**"Emin ama yanlış": iskeletin "emin" dediği 8 ölçüden 3'ü yanlış.**
- 01 `40`: tireyle komşu parçaya bağlandı (köşe, S8a).
- 02 `90`: tireyle açıklık yerine bitişik duvar parçasına bağlandı (S11).
- 02 `162`: okuma hatası (S1).

Gerçekçi koşulda (G) tireyle bağlananların 36'da 20'si doğru (%56). Gerçek kutularla (Ü) 9/9'du. Fark
Qwen kutularının değeri yanlış bölgeye atamasından geliyor. **Sonuç:** "tire = emin" kuralı ürün koşulunda
güvenli değil.

## 2. Sınıflar

Bağlama sütunu 1.5'teki 110 hatanın dağılımı. Okuma ve kenar sütunları kendi aşamalarının görülmeleri.

| Sınıf | Farklı hata | Görülme | Kroki | Örnek | Çizimle çözülür mü? Çizen neyi farklı yapsaydı? |
|---|---|---|---|---|---|
| **S1** Çizgi sayının içinden geçiyor | 2 | Okuma 12 + kesit 6 · bağlama 8 · iskelette 1 "emin" | 02 | `102` → `162`: duvardan inen ölçü çizgisi `0`'ın ortasından geçiyor. `9/0` → `96` / `960` | **Evet.** Ölçü/tik çizgisi sayının yanında bitsin; rakamların arasına çizgi girmesin |
| **S2** Kâğıt (defter) çizgisi | 1 | Okuma 5 | 02 | Dört `40`'tan biri kaçtı; çizgiler silinince düzeldi | **Kodla çözüldü** (çizgi silme). Mimar her kâğıt türünü kullandığı için (B-8) çizim kuralı yerine program; farklı renk kalem yardımcı olur |
| **S3** El yazısı `4` ≈ `u` (yalnız kesitte) | 9 | Kesit 23 | 01, 02 | `40` → YOK, `45` → `55` | **Gerekmez:** bütün fotoğrafta hiç olmadı; kesit yöntemi bırakıldı |
| **S4** Qwen aynı sayıyı tekrar yazıyor | ~6 değer | Okuma 27 fazla | 01, 02 | `40` ×6 fazla (02, ürün #3) | **Hayır.** Konum istenince artıyor; istem ya da model sorunu. Kullanıcı onayı ve "aynı parçada 2 değer" kontrolü yakalıyor |
| **S5** Qwen sayı kaçırıyor | 3 | Okuma 4 | 02 | `240`, `15`, `200` | **Hayır** (model) |
| **S6** Klasik OCR el yazısını okuyamıyor | — | 19 kaçan + 16 uydurma | 01, 02 | EasyOCR 5/24 | **Hayır**; yöntem bırakıldı |
| **S7** Qwen kutusu kayıyor, değer yanlış bölgeye gidiyor | 12 | Bağlama 15 · 30 yanlış kutu · 14 fazla değer | 01, 02 | 01 `50` ↔ `40` yer değiştirdi; 02 `45 alt` bölgesine `200` | **Kısmen.** Seyrek ve duvara yakın yazı (kural 3), farklı renk kalem kutuları iyileştirir; asıl sebep model |
| **S8a** Sayı köşeye yakın | 2 | Bağlama 13 · iskelette 1 "emin" | 01 | `50` ve `40` basamak köşesinde, iki duvara da yakın | **Evet:** kural 3 |
| **S8b** Ölçü tiki kısa, bulunamadı (köşede) | 2 | Bağlama 10 | 01, 02 | `-108`, `-45`: tire rakamdan kısa | **Evet**, ama kural 2'ye **"tik en az bir rakam boyu"** eklenmeli; kural 3 de yardım eder |
| **S9** Uzaktaki sayı eğri kılavuz çizgiyle bağlı | 1 | Bağlama 1 | 01 | `10`, kısa duvara kıvrık çizgiyle bağlı | **Evet:** kural 3 ("duvara yakın"). Açıkça yazılmalı: "sayıyı uzağa yazıp çizgiyle bağlama" |
| **S10** Kısa duvar parçası bulunamadı (ve zincirleme budama) | 4 | Bağlama 31 · kenar 4–5 parça | 01, 02 | 01 `10`, `15` (33 ve 50 px), budanan `120 sol`; 02'de `300`'ü bölen iç duvar ucu (2,4h) | **Kısmen kural 2 ve 5.** Asıl çözüm PDF'te yok: **kısa parçaları da en az iki rakam boyu çizmek** (ölçeksiz krokide maliyetsiz) |
| **S11** Kapı boşluğu bulunamadı ya da kapı dizisi karıştı | 5 | Bağlama 27 · iskelette 1 "emin" · iki krokide de kontur kaybı | 01, 02 | `10 / 90 / 15`, `15 / 9-0 / 40`: boşluk açıklık sayılmıyor, sayılar komşu parçaya gidiyor | **Evet:** kural 5 (K90). Ayrıca "kapının iki yanındaki duvar aynı hizada" (02'de 16–20 px kayma) |
| **S12** Kapı sembolü çizgileri gürültü | 1 | Bağlama 2 · 18 fazla bağlama · 9 fazla parça · 13 yazı olmayan bölge | 02 | Kapı kanadı ve yayı duvar parçası ya da sayı bölgesi sanılıyor | **Hayır:** yay + kanat mimarın standardı (B-3), çizene "çizme" denemez. Program ayırmalı; K etiketi yerini gösterir |
| **S13** X ile iptal (anlamı bilinmiyordu) | 1 | 9 fazla bağlama · yanlış kontur (02) | 02 | `X`'li köşe duvar sayıldı | **Çizen zaten doğru yapıyor.** Kodla çözüldü (mimar S5, 24.11) |
| **S14** Fotoğrafta kâğıt dışı nesne / kâğıt kenarı | 2 | Kenar 2 fazla · eksen −17° (geliştirmede) | 01, 02 | 01 mavi kumaş, 02 kâğıt destesinin kenarı | **Evet, fotoğraf kuralıyla:** kâğıdı düz, mürekkep renginde olmayan bir zemine koy; çerçevede kâğıttan başka şey olmasın. Program da perspektif düzeltmede kâğıdı kesmeli |
| **S15** Qwen Y2 uydurması / karışıklığı | 2 + 23 uydurma değer | Bağlama 3 | 01, 02 | Krokide olmayan `180`, `150`, `100`; 01 `180` komşu parçada | **Hayır** (model). "Gürültü parçası → emin değil" kuralı yakalıyor |

### Çizimle çözülemeyenler (ayrıca)

S4, S5, S6, S15 ve S7'nin büyük kısmı modelden geliyor.

| Aşama | Çizimle çözülmeyen |
|---|---|
| Okuma | 31 görülme: 27 fazla sayı + 4 kaçırma |
| Bağlama | 18 görülme (S7 15, S15 3) |
| Fazla bağlama | yaklaşık 41 (G 14, Y2b 27) |

S12 de çizimle çözülemez: kapı sembolü çizilmek zorunda.

Bu hataları yakalayan şeyler çizim değil, programın kontrolleri:
- kullanıcı onayı;
- "aynı parçada 2 değer" ve "Y2 gürültü parçası → emin değil" kuralları;
- kapanma kontrolü.

Bunlar zaten iskelette var. Ama 1.6'daki "emin ama yanlış" sonuçları, "emin" işaretinin tek başına
güvenilir olmadığını gösteriyor.

## 3. Kroki çizim kurallarıyla (PDF, 8 kural) karşılaştırma

Bağlama aşamasındaki 110 hatanın hangi kuralla çözüldüğü. Okuma ve kenar etkileri sağ sütunda.

| Kural | Çözdüğü sınıflar | Farklı hata | Bağlama görülmesi | Not |
|---|---|---|---|---|
| **1** Oda adı (ŞART) | — | 0 | 0 | 01–02 tek oda; çok odalı krokiler için gerekçesi var ama ölçülmedi. **Risk:** "Oda 1" içindeki `1` ölçü sayısı diye okunur (fazla sayı) |
| **2** Parça uçlarına tik (ŞART) | S8b (tik uzunluğu şartıyla), S10 (kısmen: program tikten bölerse) | 2 + 4 | 10 + 31 (kısmen) | S8b'nin sebebi tam da tikin **kısa** olması. Kural "en az bir rakam boyu" demeli. 01'in 33 px'lik `10` parçasını tik bulduramaz, yalnız bölme noktasını gösterir |
| **3** Ölçü duvar ortasına, duvara yakın (ŞART) | S8a, S8b, S9; kısmen S7 | 5 | 24 (+ S7'den kısmen) | En çok ölçülmüş faydası olan kurallardan |
| **4** Çizgi sayının içinden geçmesin (ŞART) | S1 | 2 | 8 (+ okumada 18, iskelette 1 "emin" hata) | En tehlikeli hatayı çözüyor. Kural 2 ile birlikte okunmalı: `102`'yi kesen çizgi bir ölçü çizgisi |
| **5** Kapı boşluğuna K ve genişlik (ŞART) | S11; dolaylı S10 (01'de kapı yanındaki `10` ve `15` S1 ile sayılardan kurulur), S12'nin yeri | 5 (+ 2 dolaylı) | 27 (+ 01'in S10 payı 16) | Ölçek yerine etiket: krokiler ölçeksiz olduğu için programın kapıyı genişlikten tanıması mümkün değil (01: ~41 cm, 02: ~54 cm göründü) |
| **6** Pencereye P ve genişlik (ŞART) | — | 0 | 0 | 01–02'de pencere yok; Faz 3 |
| **7** Farklı duvar kalınlığı d=… (İYİ OLUR) | — | 0 | 0 | Kalınlık henüz ölçülmüyor. **Risk:** `d=25`'teki `25` ölçü sayılır; program `d=` önekini tanımalı |
| **8** Çapraz ölçü kutu içinde (İYİ OLUR) | — | 0 | 0 | 01–02'de çapraz ölçü yok. Mimarın cevabı (A-7) AÇIK; kural bir sözleşme koyuyor, uygun ama ölçülmedi |
| Zaten yapılan: X ile iptal | S13 | 1 | (fazla bağlama 9) | Kod artık uyguluyor |
| Zaten yapılan: farklı renk ("mümkünse") | S2, S7, S1'e yardım | — | — | Ölçüler duvardan farklı renkteyse sayıyı kesen duvar rengindeki çizgi renkle silinebilir. 02'deki 13 yazı olmayan bölge de azalır |
| Fotoğraf kuralları | S14 (kısmen) | 1 | — | "Dört köşe görünsün" kâğıdı kesmeye yarar. Kâğıt dışı nesne ve zemin rengi söylenmiyor |

**Özet:**
- Kural 3, 4, 5 ve tik uzunluğu eklenmiş kural 2, 110 bağlama hatasının **59**'unu doğrudan çözer.
- Kural 2 ve 5, S10'un **31**'ini kısmen çözer.
- **20**'si çizimle çözülmez.

### Eksik kurallar

1. **Kısa duvar parçasını da en az iki rakam boyu çiz** (ŞART adayı).
   - S10'un 31 görülmesinin asıl çözümü; kapı yanındaki `10` / `15` parçalarını görünür kılar ve S11'e de
     yardım eder.
   - Kroki zaten ölçeksiz; çizenin bir şey kaybetmesi yok.
   - Mimarın kabul edip etmeyeceği sorulmalı: oranları bozuyor gibi görünebilir.
2. **Kural 2'ye ek: tik en az bir rakam boyu olsun.** S8b'nin iki hatasının sebebi rakamdan kısa tireler
   (`-108`, `-45`).
3. **Kural 3'e ek: sayıyı uzağa yazıp eğri bir çizgiyle bağlama** (S9, 01 `10`).
4. **Köşelerde ve birleşimlerde çizgiler birbirine değsin; kapının iki yanındaki duvar aynı hizada olsun.**
   - 02'nin iç kapısında parçalar 16–20 px kaymış (S11).
   - Geliştirme sırasında 02'nin konturu ancak köşe toleransı h/2'den 0,75h'ye çıkınca kapandı.
   - Programın da toleranslı olması gerek; kural yalnız riski azaltır.
5. **Fotoğraf: kâğıdı mürekkep renginde olmayan düz bir zemine koy; çerçevede kâğıttan başka nesne,
   kâğıt destesi kenarı olmasın** (S14).
6. **Farklı renk kalemi "mümkünse"den "İYİ OLUR" kuralına yükseltmek.** S2'yi, S7'yi ve S1'i hafifletir;
   kanıtı orta düzeyde (ölçülmedi, renk ayrımının işe yaradığı çizgi silme deneyinden çıkarım).

### Gereksiz ya da riskli kurallar

- **Hiçbiri kanıtla gereksiz değil, ama dördünün (1, 6, 7, 8) 01–02'de ölçülmüş bir faydası yok.** Faz 3
  krokileri (03–07) ölçülünce yeniden değerlendirilmeli.
- **Kural 1 "ŞART" olarak fazla güçlü.** Tek odalı krokide gereksiz. "Çok odalı krokilerde" diye
  sınırlanmalı ve rakamsız adlar önerilmeli ("Yatak", "WC", "Salon"; "Oda 1" değil). Yoksa yeni bir S4
  tipi fazla sayı üretir.
- **Kural 7**'de program `d=` önekini tanıyana kadar `25` bir ölçü sayısı gibi okunur.

### PDF'te düzeltilmesi önerilen iddialar

| PDF'te | Ölçülen |
|---|---|
| "Programı 7 gerçek krokiyle denedik" | Ölçüm yalnız 01 ve 02'de; 03–07 hiç çalıştırılmadı |
| "Program yazıyı çok iyi okuyor (24 sayıdan 23)" | Ürünün koşulunda (çizgi silme + konumlu istem) 22/22/22; kelime (oda adı) okuma hiç ölçülmedi |
| "Tik bulunduğunda sayı–duvar eşleştirmesi 9/9 doğru" | Yalnız gerçek kutu ve değerlerle (Ü). Gerçekçi koşulda tireyle bağlananların %56'sı doğru; iskelette iki tireli bağlama yanlıştı ve "emin" işaretlendi |
| "102 her denemede 162 okundu" | 02'yi okuyan 27 Qwen çalıştırmasının 21'inde; CPU'da 3/3 doğru okundu |

## 4. Sonuç ve öneri

- **Çizim tarafı:**
  - PDF'e üç ek önerilir: kısa parçaları uzun çiz, tik en az bir rakam boyu, fotoğraf zemini.
  - Kural 1 "çok odalı" diye sınırlanmalı, rakamsız adlar önerilmeli.
  - Dört iddia düzeltilmeli.
  - Bu kurallar ölçülen bağlama hatalarının yaklaşık %80'ine dokunuyor.
- **Program tarafı** (çizimle çözülmeyenler):
  - kapı sembolü gürültüsü (S12);
  - fazla ve uydurma değerler (S4, S15);
  - kutu kayması (S7);
  - "tire = emin" kuralının ürün koşulunda gözden geçirilmesi (1.6).
- **3. adımdaki kapı kuralı** (bekleyen öneri) S11'i hedefliyor ve iki krokide de konturun kapanmamasının
  ortak sebebi. Kural 5 uygulanırsa etiket (K90) kapıyı doğrudan gösterir; o zaman sayının yakınlığına
  bakmaya gerek kalmaz.
- **Yeni krokilerle ölçüm şart.** PDF'teki istek ("2–3 yeni kroki + doğru ölçüler") kurallarla çizilmiş
  krokilerde bu sınıfların gerçekten kaybolup kaybolmadığını gösterecek tek ölçüm.
