# Sayı–Duvar Eşleştirme Raporu

Tarih: 2026-11-18 · Tasarım: `docs/superpowers/specs/2026-11-17-sayi-duvar-eslestirme-design.md` ·
Plan: `docs/superpowers/plans/2026-11-17-sayi-duvar-eslestirme.md` · Tablolar: [`olcumler.md`](olcumler.md)
(`olcum.py` üretir) · Ham sonuçlar: `sonuclar/` · Kontrol görselleri: `gorseller/` (**`.gitignore`'da**)

## Kısa cevap

**Kazanan yaklaşım Y2: numaralı parçaları Qwen'e sormak.** Kenar parçaları verildiğinde Qwen3-VL 4B,
24 sayıdan **19/18/19**'unu doğru parçaya bağladı (P numaraları karışık sırayla). Geometrik ana yolun
(Y1) üst sınırı bile 18. Gerçekçi hali, yani bulunan kenarlar + bulunan bölgeler + Qwen değerleri ise
**9–13**'te kaldı.

**Öneri:** Ana yolu değiştirmek. Kenar bulma (Y1'in ilk adımı) kalsın; kenarlar fotoğrafa
numaralanarak çizilsin ve sayı okuma ile bağlama tek bir Qwen çağrısında yapılsın. Ancak Y2 burada
**gerçek** kenarlarla ölçüldü. **Bulunan** kenarlarla ölçülmedi; kararın asıl sınavı bu ve sonraki
adım (aşağıda).

| Yaklaşım | Katı /24 (çalıştırma başına) | Ne gösteriyor |
|---|---|---|
| Y1 üst sınır (gerçek kenar + gerçek kutu + gerçek değer) | 18 | Bağlama kuralının kendi tavanı |
| Y1 ara (bulunan kenar + gerçek kutu + gerçek değer) | 14 | Kenar bulmanın maliyeti: −4 |
| Y1 gerçekçi, hane ipuçlu | 12 / 13 / 9 | Uçtan uca |
| Y3 taban (Qwen kutusu → en yakın parça), gerçek kenar | 16 / 15 / 16 | |
| Y3 taban, bulunan kenar | 11 / 13 / 11 | Y1 gerçekçiyle aynı düzeyde |
| **Y2, kontur sırasıyla numaralı** | **21 / 22 / 22** | Sıradan da yararlanıyor (aşağıda) |
| **Y2, karışık numaralı** | **19 / 18 / 19** | Asıl Y2 sonucu |

Mimara bağlı 7 sayı (`15/90/10`, `15/9-0`, `300`, `200`) hariç (/17): Y1 üst sınır 13, Y1 gerçekçi
8–12, Y2 karışık 14–15.

## Hata nereden geliyor (Y1)

**1. Bağlama kuralının kendisi zayıf: üst sınır 18/24.**
- Ölçü işaretiyle bağlananlar 9/9 doğru, "en yakın parça" ile bağlananlar 15'te 9 doğru.
- Kaybedilen 6 sayının hepsi köşe yakınında. İşaret bulunamayınca sayı komşu duvara gidiyor:
  - 01: `108` sol duvar yerine üst duvara gidiyor.
  - 01: `40`, kırık bir kılavuz çizgiyle bağlı.
  - 02: iki `45` sağ üst basamakta.
  - 02: `15/9-0` iç kapıda.
- **Asıl neden:** kısa ölçü tireleri (`-108`, `-45`) karakter yüksekliğinden kısa olduğu için çizgi
  olarak hiç bulunamıyor.

**2. Kenar bulma: −4.**
- 01'in sol alt kenarındaki `10/90/15` parçaları 33 ve 50 px. Çizgi bulucunun en kısa çizgi sınırının
  (h = 37 px) altında kaldıkları için bulunamıyor. Bunun sonucu olarak komşu `120` duvarı da
  budanıyor (bir ucu boşta kalıyor). 01'de 10 gerçek parçanın 6'sı bulundu, kontur kapanmıyor.
- 02'de dış konturun 10 kenarı sıra olarak gerçekle aynı, ama parça düzeyinde iki fark var:
  - Üst kenar, iç duvarın üst ucu bulunamadığı için T-birleşimde bölünmedi. Bu yüzden ara katmanda
    `300` kaybediliyor.
  - Sol duvar, `X` çizgisi yüzünden fazladan bölündü.

  Bu yüzden puanlama "kontur doğru: hayır" diyor. 16 gerçek parçanın 11'i bulundu. Fazla 11 parça sol
  üstteki küçük odadan geliyor: kapı kanadı, kapı yayı, `9/0` ve `X` çizgileri.

**3. Bölge bulma + değer atama: −2 ile −5.**
- Bölge bulma iki krokide de 24 sayının hepsini kapsıyor. Ama 02'de 28 bölgenin 13'ü yazı değil.
- Değeri bölgeye Qwen'in kutularıyla atamak 02'de zayıf: 17 atamanın yalnız ~10'u doğru değeri
  alıyor. Qwen kutuları 02'de kaymıştı (konum deneyi).
- Sonuç olarak Y1'in gerçekçi hali, Qwen kutusunu doğrudan en yakın parçaya bağlamaktan (Y3, bulunan
  kenar) daha iyi değil.

## Y2 neden iyi, nerede yanılıyor

- **Okuma ile bağlamayı aynı anda yapıyor;** sayının yerini ayrıca bulmaya gerek kalmıyor.
  Konum deneyinde Qwen'in kutuları kötüydü, ama "bu parçanın yanındaki sayı" sorusunu çok daha iyi
  cevaplıyor.
- **Sıra kontrolü:**
  - Kontur sırasıyla numaralandırınca (P1 = sol üstten saat yönünde ilk kenar) 21–22 aldı.
  - Numaralar karışınca 18–19'a düştü. Kayıp çoğunlukla 01'de: `50` ve `40` köşede yer değiştirdi.
  - Yani sıranın 2–4 sayılık katkısı var, ama bağlamanın büyük kısmı gerçek.
- **Kalan hataları:**
  - `102` → `162` okuma hatası (bağlama doğru, değer yanlış).
  - İç kapı bölgesinde `15/90/40` karışıyor.
  - **Sayısı olmayan parçalara uydurma değer veriyor:** 02'nin `X`'li parçalarına `180`, `150`, `15`,
    `45` yazdı; `180` krokide hiç yok. Bu yüzden kullanıcı onayı ekranında boş olması gereken parçalar
    da kontrol edilmeli.
- **Süre:** kroki başına ~70–80 s (sadece okuma ~56–60 s). Ayrı bir okuma çağrısına gerek kalmadığı için
  toplamda daha kısa.

## Hane ipucu ve diğer denemeler

- **Hane ipucu** (kullanıcı eklemesi) eşleştirme puanını **değiştirmedi** (ipuçlu ve ipuçsuz birebir
  aynı). Doğru değeri alan bölge sayısında da net etkisi sıfır: 01'in 2. çalıştırmasında −1, 02'nin
  3. çalıştırmasında +1, diğer 4 çalıştırmada eşit. Bölgeler artık sayıları tam kapsadığı için
  mesafe tek başına yetiyor; ipucu belirleyici olmuyor.
- **`temas` kuralı etkisiz:** Kapatıldığında Ü, A ve G birebir aynı. Temasla bağlanan bölgelerin
  çoğu duvar silme artıklarıydı; en yakın kural da onları yanlış bağlıyor.
- **İşaret payı h/2 → h:** 01'de −1, 02'de +1, net 0. Plan değeri (h/2) korundu.

## Ayarlanan eşikler (hepsi h = karakter yüksekliği cinsinden; gerekçeleriyle)

İlk değerler plandan. Gerçek krokilere bakarak değiştirilenler:

| Eşik | Plan | Son | Gerekçe | Bedeli (yanlışsa) |
|---|---|---|---|---|
| Doğrudaş birleştirme açısı | 10° | 20° | Kısa kalın çizgilerde Hough açısı ±12° oynuyor; doğrudaşlığı dik mesafe denetliyor | Yakın dik çizgiler birleşebilir (dik mesafe engelliyor) |
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

1. **Y2'yi bulunan kenarlarla ölçmek** (karışık numaralı, 3'er çalıştırma). Kararın asıl sınavı bu.
   - 02'de dış kontur doğru bulunduğu için sonucun yakın çıkması beklenir.
   - 01'de eksik kenarlar (`10/90/15`, `120`) numarasız kalacak. Model bu sayıları ya yanlış parçaya
     yazacak ya da atlayacak.
2. **Kenar bulmada kısa parçalar.** 01'in sol alt kenarı ve kısa ölçü tireleri için en kısa çizgi
   sınırını h/2'ye indirmek. Gürültüyü artırır; budama kuralıyla birlikte yeniden ölçülmeli. Bu iş Y2
   için de gerekli, çünkü numarası olmayan kenarın sayısı sorulamaz.
3. **Y2 cevabını geometriyle denetlemek:** Y1'in ölçü işareti bağlamaları (9/9 doğru) Y2 ile
   çeliştiğinde kullanıcıya sormak. Boş olması gereken parçalara yazılan değerler de onay listesinde
   işaretlenir.
4. **03–07** (mimarın doğru cevaplarıyla) aynı ölçüm.

## Sınırlar

- 2 kroki, 24 sayı. Gerçek parçalar ve gerçek eşleştirme elle çizildi (kullanıcı onaylı).
- Y1'in gerçekçi katmanı, konum deneyinin (orijinal fotoğraftan alınmış) Qwen kutularını kullandı;
  yeni Qwen çağrısı yapılmadı.
- **Ü katmanındaki ölçü işaretleri** bulunan sonuçtan alındı. Gerçek kenarlarda işaret yok, adaylar
  mürekkepten bulunuyor. Yani Ü, işaret bulmadaki eksikleri de içeriyor (kısa tireler).
- Y2 tek istemle, iki numaralandırma sırasıyla denendi; istem iyileştirmesi yapılmadı.
