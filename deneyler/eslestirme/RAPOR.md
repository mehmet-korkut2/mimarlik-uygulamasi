# Sayı–Duvar Eşleştirme Raporu

Tarih: 2026-11-18 (Y2 bulunan kenar ölçümü eklendi) · Tasarım: `docs/superpowers/specs/2026-11-17-sayi-duvar-eslestirme-design.md` ·
Plan: `docs/superpowers/plans/2026-11-17-sayi-duvar-eslestirme.md` · Tablolar: [`olcumler.md`](olcumler.md)
(`olcum.py` üretir) · Ham sonuçlar: `sonuclar/` · Kontrol görselleri: `gorseller/` (**`.gitignore`'da**)

## Kısa cevap

**Aynı (gerçek) kenarlar verildiğinde Y2 ile geometrik yolun üst sınırı berabere.**
- **Y2** (numaralı parçaları Qwen'e sormak, numaralar karışık sırayla): 24 sayıdan **19/18/19**.
- **Y1 üst sınır** (gerçek kenar + gerçek kutu + gerçek değer): **19**.

Y2 bunu kendi okuduğu değerlerle yapıyor; Y1'in üst sınırı ise gerçek değerleri ve gerçek kutuları
kullanıyor. **Y1'in gerçekçi hali** (bulunan kenarlar + bulunan bölgeler + Qwen değerleri) **10–14**'te
kaldı, ve taban çizgisinden (Y3) belirgin şekilde iyi değil.

**Bulunan kenarlarla (gerçekçi koşul) Y2 biraz önde ama kesin değil:**
- Y2: **13 / 17 / 12** (ortalama 14,0).
- Y1 gerçekçi: 13 / 14 / 10 (ortalama 12,3).

Y2 çalıştırmalar arasında çok oynuyor. İki yolun da tavanını **kenar bulma** belirliyor:
- Kenarı bulunamayan sayı hiçbir yolla bağlanamıyor.
- Bulunan kenarlarla en fazla 17/24 bağlanabiliyor (01'de 6, 02'de 11).
- Y2 bir çalıştırmada bu tavana ulaştı.

**Öneri:** Önce kenar bulmayı iyileştirmek (iki yolun da tavanı). Ana yol olarak Y2'ye yönelmek
mantıklı: daha basit (bölge bulma ve değer atama yok, okuma ve bağlama tek çağrıda), ortalamada önde.
Ama oynaklığı (01'de köşe sayılarının yer değiştirmesi) ve gürültü parçalarına yazdığı uydurma
değerler, geometrik denetimle (bkz. sonraki adım 3) ve kullanıcı onayıyla yakalanmalı. Karar senin.

| Yaklaşım | Kenarlar | Katı /24 (çalıştırma başına) | Mimara bağlılar hariç /17 | Fazla bağlama |
|---|---|---|---|---|
| Y1 üst sınır (gerçek kutu + gerçek değer) | gerçek | 19 | 15 | 5 |
| Y1 ara (gerçek kutu + gerçek değer) | bulunan | 14 | 13 | 10 |
| Y1 gerçekçi (bulunan bölge + Qwen), hane ipuçlu | bulunan | 13 / 14 / 10 | 12 / 13 / 9 | 14 / 15 / 15 |
| Y3 taban (Qwen kutusu → en yakın parça) | gerçek | 13 / 15 / 17 | 9 / 13 / 13 | 14 / 14 / 8 |
| Y3 taban | bulunan | 9 / 13 / 13 | 8 / 12 / 12 | 18 / 16 / 12 |
| Y2, kontur sırasıyla numaralı | gerçek | 21 / 22 / 22 | 16 / 16 / 16 | 5 / 4 / 4 |
| Y2, karışık numaralı | gerçek | 19 / 18 / 19 | 14 / 15 / 14 | 7 / 8 / 7 |
| **Y2, karışık numaralı** | **bulunan** | **13 / 17 / 12** | **12 / 16 / 11** | 13 / 9 / 14 |

**Fazla bağlama:** Doğru olmayan bağlama sayısı (yanlış parça, uydurma ya da fazla okunan değer).
Tasarım 7.3'e göre fazla okunan bir değerin bir yere bağlanması hatadır; "katı" sütunu bunu
cezalandırmıyor, bu yüzden ayrıca gösteriliyor. Y1'in gerçekçi hali çalıştırma başına 14–15 fazla
bağlama üretiyor (aşağıda).

## Hata nereden geliyor (Y1)

**1. Bağlama kuralının tavanı: üst sınır 19/24.**
- Ölçü işaretiyle bağlananlar 9/9 doğru, "en yakın parça" ile bağlananlar 15'te 10 doğru.
- Kaybedilen 5 sayının hepsi köşe yakınında ve ölçü işaretleri bulunamamış:
  - 01: `108` sol duvar yerine üst duvara gidiyor.
  - 01: `10`, köşedeki kısa duvara kavisli bir kılavuz çizgiyle bağlı.
  - 02: `45` sağ üst basamakta.
  - 02: iç kapıdaki `15` ve `90`.
- **Asıl neden:** kısa ölçü tireleri (`-108`, `-45`) karakter yüksekliğinden kısa olduğu için çizgi
  olarak bulunamıyor.

**2. Kenar bulma: −5 (19 → 14).**
- 01'in sol alt kenarındaki `10/90/15` parçaları 33 ve 50 px. Çizgi bulucunun en kısa çizgi sınırının
  (h = 37 px) altında kaldıkları için bulunamıyor. Komşu `120` duvarı da bir ucu boşta kaldığı için
  budanıyor. 01'de 10 gerçek parçanın 6'sı bulundu, kontur kapanmıyor.
- 02'de dış konturun 10 kenarı sıra olarak gerçekle aynı, ama parça düzeyinde iki fark var:
  - Üst kenar, iç duvarın üst ucu bulunamadığı için T-birleşimde bölünmedi. Bu yüzden ara katmanda
    `300` kaybediliyor.
  - Sol duvar, `X` çizgisi yüzünden fazladan bölündü.

  Bu yüzden puanlama "kontur doğru: hayır" diyor. 16 gerçek parçanın 11'i bulundu. Fazla 11 parça sol
  üstteki küçük odadan geliyor: kapı kanadı, kapı yayı, `9/0` ve `X` çizgileri.

**3. Bölge bulma ve değer atama: 0 ile −4.**
- Bölge bulma iki krokide de 24 sayının hepsini kapsıyor, ama 02'de 28 bölgenin 13'ü yazı değil.
- Değeri bölgeye Qwen'in kutularıyla atamak 02'de zayıf: 17 atamanın yalnız ~10'u doğru değeri
  alıyor. Qwen kutuları 02'de kaymıştı (konum deneyi).
- **Tasarımdan sapma: fazla değerler eşsiz kalmıyor.** Qwen 02'de 14 sayı için 17, 19 ve 14 değer
  döndürdü. Hepsi atandı (`yeri_bulunamayan` 6 çalıştırmanın hepsinde 0); fazlalar yazı olmayan
  bölgelere dağıldı.

  Neden: mesafe üst sınırı (köşegenin %20'si ≈ 400 px) karakter yüksekliğine (23–37 px) göre çok
  gevşek, neredeyse hiçbir çifti yasaklamıyor. Sınırı daraltmak doğru değerleri de düşürebilir
  (Qwen'in kutuları 02'de bir sayı boyundan fazla kaymıştı). Bu yeni bir ayar olduğu için bu
  çalışmada değiştirilmedi; etkisi "Fazla bağlama" sütununda görünüyor.

## Y2 bulunan kenarlarla (gerçekçi koşul)

Ayarlar gerçek kenarlı Y2 ile aynı (karışık numara, tohum 17, 3'er çalıştırma). Fotoğrafa
`kenarlari_bul`'un bulduğu parçalar çizildi: 01'de 6, 02'de 22. Puanlama ara katmandaki gibi yapıldı:
bulunan parça, uçları ≤ 25 px olan gerçek parçaya eşlendi; eşleşmeyen parçaya yazılan sayı yanlış
sayıldı.

| Kroki | Katı (1/2/3) | Bulunan kenarlarla en fazla | Ne oldu |
|---|---|---|---|
| 01 /10 | 3 / 6 / 3 | 6 | `10/90/15` ve `120` kenarları bulunamadığı için numarasız. 2. çalıştırma tavana ulaştı; 1. ve 3.'de köşedeki `180`, `50`, `40` komşu parçalara kaydı |
| 02 /14 | 10 / 11 / 9 | 11 | İç kapının `15/90`'ı numarasız. `300` bölünmemiş üst kenara yazıldı (gevşek ölçütte doğru). `102` → `162` okuma hatası |

- **Fazla bağlama** 9–14. Çoğu 02'nin iç odasındaki gürültü parçalarına (kapı kanadı, yay, `X`)
  yazılmış uydurma değerler: `180`, `150`, `40`. Y1 gerçekçinin fazlası (14–15) ile aynı düzeyde.
- **Süre:** 01'de ~58 s, 02'de ~88 s. Parça sayısı arttıkça cevap uzuyor.
- **Sonuç:** Y2 ile Y1 gerçekçi arasındaki fark, aralarındaki oynaklıktan büyük değil. İkisini de
  kenar bulma sınırlıyor.

## Y2 nerede iyi, nerede yanılıyor

- **Okuma ile bağlamayı aynı anda yapıyor;** sayının yerini ayrıca bulmaya gerek kalmıyor.
  Konum deneyinde Qwen'in kutuları kötüydü, ama "bu parçanın yanındaki sayı" sorusunu çok daha iyi
  cevaplıyor.
- **Sıra kontrolü:**
  - Kontur sırasıyla numaralandırınca (P1 = sol üstten saat yönünde ilk kenar) 21–22 aldı.
  - Numaralar karışınca 18–19'a düştü. Kayıp çoğunlukla 01'de: `50` ve `40` köşede yer değiştirdi.
  - Yani sıranın 2–4 sayılık katkısı var. Gerçek sonuç karışık sıradaki 18–19.
- **Kalan hataları:**
  - `102` → `162` okuma hatası (bağlama doğru, değer yanlış).
  - İç kapı bölgesinde `15/90/40` karışıyor.
  - **Sayısı olmayan parçalara uydurma değer veriyor:** 02'nin `X`'li parçalarına `180`, `150`, `15`,
    `45` yazdı; `180` krokide hiç yok. Bu yüzden kullanıcı onayı ekranında boş olması gereken parçalar
    da kontrol edilmeli.
- **Süre:** kroki başına ~70–80 s (sadece okuma ~56–60 s). Ayrı bir okuma çağrısına gerek kalmadığı için
  toplamda daha kısa.

## İnceleme düzeltmeleri (bağımsız inceleme sonrası)

1. **Parça sınırında eşitlik:**
   - **Sorun:** Bir nokta iki parçanın ortak ucuna düştüğünde (ölçü işaretleri çoğu zaman tam oraya
     düşer, köşedeki sayılar da iki duvara eşit uzak olur) seçimi parçaların sırası belirliyordu. Alt
     ve sol kenarlar ters sırada olduğu için bu, sayıyı açıklık parçasına bağlayabiliyordu.
   - **Düzeltme:** Artık sayının merkezinin izdüşümünün düştüğü parça seçiliyor.
   - **Etki:**
     - Ü 18 → 19.
     - Y1 gerçekçi 12/13/9 → 13/14/10.
     - Y3 (gerçek kenar) 16/15/16 → 13/15/17. Eski değerler kısmen eşitliklerin şans eseri doğru
       bozulmasından geliyordu; yeni değerler parça sırasından bağımsız.
2. **Kenar yönü:** Birleşen iki eğik kısa parça ±15°'lik toleransın dışına çıkınca kenarın yönü boş
   (`None`) kalabiliyordu ve geometri adımıyla sözleşmeyi ("yatay" | "dikey") bozuyordu. Yön artık
   parçaların çoğunluğundan alınıyor.
3. **Fazla bağlama** sütunu eklendi (yukarıda).

## Hane ipucu ve diğer denemeler

- **Hane ipucu** (kullanıcı eklemesi) eşleştirme puanını **değiştirmedi** (ipuçlu ve ipuçsuz birebir
  aynı). Doğru değeri alan bölge sayısında da net etkisi sıfır: 01'in 2. çalıştırmasında −1, 02'nin
  3. çalıştırmasında +1, diğer 4 çalıştırmada eşit. Bölgeler artık sayıları tam kapsadığı için
  mesafe tek başına yetiyor; ipucu belirleyici olmuyor.
- **`temas` kuralı neredeyse hep gürültüde tetikleniyor.** Gerçekçi katmanda 16 bağlamanın 5'i doğru.
  Bağlanan bölgelerin çoğu duvar silme artığı. Eşitlik düzeltmesinden önce kapatılıp ölçüldüğünde
  Ü, A ve G birebir aynıydı. Kaldırılması önerilir.
- **İşaret payı h/2 → h:** 01'de −1, 02'de +1, net 0. Plan değeri (h/2) korundu.

## Ayarlanan eşikler (hepsi h = karakter yüksekliği cinsinden; gerekçeleriyle)

İlk değerler plandan. Gerçek krokilere bakarak değiştirilenler:

| Eşik | Plan | Son | Gerekçe | Bedeli (yanlışsa) |
|---|---|---|---|---|
| Doğrudaş birleştirme açısı | 10° | 20° | Kısa kalın çizgilerde Hough açısı ±12° oynuyor; doğrudaşlığı dik mesafe denetliyor | Yakın dik çizgiler birleşebilir; yön artık üyelerden alınıyor (inceleme düzeltmesi 2) |
| İşaret sayılma uzunluğu | < 3h | < 6h, bir ucu boşta | İşaret rakam çizgileriyle birleşip uzuyor (`240`) | Bir ucu boşta kısa gerçek duvar işaret sayılır (01'deki `120` duvarı) |
| Kalın leke temizliği | yok | çapı h disk | 01'deki mavi kumaş eksen açısını −17° yapıyordu (doğrusu ~−4°) | h'den kalın gerçek duvar silinir |
| Köşe/bağlantı toleransı | h/2 | 0,75h | Elle çizilen köşeler tam buluşmuyor; 02'nin konturu kapanmıyordu | Yakın çizgiler arasında sahte köşe |
| Rakam gruplama (yatay) | 0,6h | 1,0h | 02'de rakam aralığı ~1 karakter; sayılar parçalanıyordu (9/14 → 14/14) | Yakın iki sayı birleşir (02'de 1 kez) |
| En küçük bölge yüksekliği | yok | 0,5h | Duvar silme artıkları (10 px) bölge sayılıp değer alıyordu | Çok küçük yazılmış sayı kaybolur |

**Uyarı:** Bu eşikler yalnız 01 ve 02'ye bakılarak ayarlandı (tasarımın aşırı uyum riski). 03–07'de
yeniden ölçülmeli.

## Mimara sorular (tasarım bölüm 3)

1. **M1:** Bir kenarda arka arkaya yazılan üç sayı "duvar – açıklık (kapı) – duvar" mı? Desen iki
   krokide de var: 01 `15/90/10`, 02 `15/9-0/40`. Açıklık sayısı kapı genişliği mi, kasa dahil mi?
2. **M2:** Bir T-birleşimin yanındaki sayı tüm kenarı mı, sadece o parçayı mı ölçüyor? 02'de `300` ve
   `200`. 02'de yatay toplam ancak `300` tüm kenar sayılınca tutuyor.
3. **M3:** 01'in toplamları bu okumalarla tutmuyor. Bir okuma mı yanlış, yorum mu?
4. **M4:** `X` işaretleri ne anlama geliyor? (Y2 bu parçalara uydurma değer yazdı.)
5. **M5:** Ölçüler iç ölçü mü, dış ölçü mü?

## Sonraki adım önerisi

1. ~~Y2'yi bulunan kenarlarla ölçmek~~ (yapıldı, yukarıda).
2. **Kenar bulmada kısa parçalar (öncelikli; iki yolun da tavanı).** 01'in sol alt kenarı ve kısa ölçü tireleri için en kısa çizgi
   sınırını h/2'ye indirmek. Gürültüyü artırır; budama kuralıyla birlikte yeniden ölçülmeli. İki yol
   için de gerekli.
3. **İki yolu birleştirmek:** Y1'in ölçü işaretiyle yaptığı bağlamalar 9/9 doğru. Y2 ile çeliştiklerinde
   kullanıcıya sorulabilir. Boş olması gereken parçalara yazılan değerler de onay listesinde
   işaretlenir.
4. **03–07** (mimarın doğru cevaplarıyla) aynı ölçüm.

## Sınırlar

- 2 kroki, 24 sayı. Gerçek parçalar ve gerçek eşleştirme elle çizildi (kullanıcı onaylı).
- Y1'in gerçekçi katmanı, konum deneyinin (orijinal fotoğraftan alınmış) Qwen kutularını kullandı;
  yeni Qwen çağrısı yapılmadı.
- **Ü katmanındaki ölçü işaretleri** bulunan sonuçtan alındı. Gerçek kenarlarda işaret yok, adaylar
  mürekkepten bulunuyor. Yani Ü, işaret bulmadaki eksikleri de içeriyor (kısa tireler).
- Y2 tek istemle, iki numaralandırma sırasıyla denendi; istem iyileştirmesi yapılmadı.
- `olcumler.md`'deki "atama + bağlama" süresinin ilk değeri (01, ~300 ms) `scipy` içe aktarmasını
  içeriyor. Algoritmanın kendisi ~1 ms.
