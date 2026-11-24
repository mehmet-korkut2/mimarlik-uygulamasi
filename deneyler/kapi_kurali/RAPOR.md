# Kapı boşluğu kuralı (mimar cevapları, 3. adım)

**Kural:** Aynı doğrultuda karşılıklı iki duvar ucu arasındaki boşluk (1–8 h) kapı adayıdır. Kapı genişliği sırasıyla
kapı etiketinden (`K90`), boşluğun yakınında okunan kapı genişliğindeki sayıdan (80/90/100/110/120, B-3) ya da ilk
geçişin ölçeğinden (±10 cm) gelir. Kontur boşluğun üstünden kapanır, kapı KAPI katmanına çizilir; etiketten gelmeyen
kapılar KONTROL'de not edilir ("? kapı 90: yakında okunan sayıdan").

Ölçüm: `olcum.py`, 01 ve 02 (aşağıdaki tablo kapı bağlama düzeltmesinden önce), `--okuma` (Qwen-1 kayıttan, Y2 her klasörde yeniden soruldu → 3 örnek).

| Kroki | Koşul | Kontur | Kapı | Bağlama | "Emin" doğru | Kapanma yatay / dikey (cm) |
|---|---|---|---|---|---|---|
| 01 | kuralsız (adim2) | yok | — | 3/10 | 0/1 | — |
| 01 | kural, örnek 1 | 8 kenar (8/9 parça gerçeğe eşlendi) | 90, sayıdan | 4/10 | 2/4 | 40 / 150 |
| 01 | kural, örnek 2 | 8 kenar | 90, sayıdan | 6/10 | 3/5 | 40 / 163 |
| 01 | kural, örnek 3 | 8 kenar | 90, sayıdan | 6/10 | 3/5 | 40 / 163 |
| 02 | kuralsız (adim2) | yok | — | 9/14 | 3/4 | — |
| 02 | kural, örnek 1 | 12 kenar (14/14) | 90, sayıdan | 11/14 | 5/7 | 12 / 95 |
| 02 | kural, örnek 2 | 12 kenar | 90, sayıdan | 10/14 | 5/7 | 12 / 94 |
| 02 | kural, örnek 3 | 12 kenar | 90, sayıdan | 8/14 | 3/4 | 0 / 61 |

**Sonuç:** Kural iki krokide de amacına ulaştı: 01'in dış konturu ilk kez bulundu, 02'nin 2. adımda kaybolan konturu
geri geldi; kapı iki krokide de doğru yerde ve doğru genişlikte (90). Bağlama 01'de 3 → 4–6/10, 02'de 9 → 8–11/14
(Y2'nin örnekten örneğe oynaması kural etkisinden büyük). İki krokide de kapı etiketi yok; kapılar okunan sayıdan geldi.

## Önemli bulgu: krokiler ideal durumda da kapanmıyor

Gerçek sayılar gerçek dış hatta (S1: `15/90/10` toplanır, S3 = B) yerleştirilse bile kapanma farkı
**01: yatay 40, dikey 53 cm; 02: yatay 48, dikey 60 cm**. Yani bugünkü yorumla kapanma kontrolü bu iki krokiyi
doğrulayamaz; ölçülen farkın bir kısmı okuma/bağlama hatası değil, yorumun kendisi. Mimara sorulacak: bu krokilerde
ölçüler iç ölçü mü (S6), duvar kalınlıkları toplama girmeli mi, eksik/fazla sayılan bir ölçü var mı?

## Bilinen kırılganlıklar

- 01'de kapı açıklığı, altındaki 10 cm'lik kısa duvarı da yutuyor (o parça çizgi olarak bulunamıyor; sanal
  duvar 0,5 h). Açıklığın ucu gerçeğe eşlenmediği için "90" ve "10" ölçümde yanlış sayılıyor.
- 01'de kapı seçimi ipuçlarının boşluğa uzaklık sırasına bağlı; yakında ikinci bir kapı genişliğinde sayı olsaydı
  yanlış boşluk seçilebilirdi.
- 120 hem kapı genişliği hem duvar uzunluğu olabilir ("120 sol"); dik uç durumu için uzun duvar (≥ 6 h, `varsayimlar.KAPI_DIK_UC_DUVARI`) şartı bu
  yüzden konuldu.

## Düzeltme: kapıyı veren sayı kapı açıklığına bağlanır

`birlestir`: kapı kuralı bir kapı bulduysa kapı genişliğindeki sayı (kapı sayıdan geldiyse en yakın aynı değerli
sayı; etiketten/ölçekten geldiyse yalnız 5 h içindeki) açıklık parçasına bağlanır (kaynak "kapi", emin). Aynı Y2
cevaplarıyla (`--okuma` önceki üç örneğin kaydı) yeniden ölçüldü:

| Kroki | Örnek 1 | Örnek 2 | Örnek 3 |
|---|---|---|---|
| 02 bağlama (önce → sonra) | 11 → **12**/14 | 10 → **11**/14 | 8 → **9**/14 |
| 02 "emin" doğru | 5/7 → 5/6 | 5/7 → 6/7 | 3/4 → 3/3 |
| 01 bağlama | 4/10 (değişmedi) | 6/10 | 6/10 |

01'de 90 zaten açıklıktaydı (yukarıdaki kısa duvar sorunu). 02'nin 3. örneği bu düzeltmeyle 0 / 0 cm "kapanıyor",
ama 5 sayı yanlış parçada: yanlış bağlama da kapanabilir, kapanma tek başına doğruluk kanıtı değil.

## Deneme: kapanma farkı iç duvar kalınlığıyla açıklanır mı? (`duvar_kalinligi.py`)

Kapanma kontrolü değiştirilmedi (mimarın cevabı bekleniyor). Fark = n geçiş × t kalınlık (t = 10/20/25, ±5 cm):

| Kroki | Eksen | Fark | Uyan n × t | Krokide görülen iç duvar geçişi |
|---|---|---|---|---|
| 01 | yatay | 40 | 4×10, 2×20 | 0 (iç duvar çizilmemiş) |
| 01 | dikey | 53 | 5×10, 2×25 (−3) | 0 |
| 02 | yatay | 48 | 5×10, 2×25 (+2) | 1 (X'li küçük odanın kapılı duvarı) |
| 02 | dikey | 60 | 6×10, 3×20 | 1 (küçük odanın alt duvarı) |

**Sonuç: krokide görülen geçişlerle açıklanamıyor.** 01'de hiç iç duvar yok ama fark 40 / 53 cm. 02'de geçiş başına
48 ve 60 cm gerekir (25 cm'lik dış duvardan bile kalın). Sayısal olarak uyan çiftler (ör. 10 cm × 4–6 geçiş) krokide
karşılığı olmayan geçiş sayıları istiyor. Fark kalınlıktan başka bir yerden geliyor olabilir: bir ölçünün dış hatta
yanlış yere konması (yorum), krokide eksik bir ölçü ya da ölçülerin kendisi. Mimara sorulan soru ("fark aradaki duvar
kalınlıklarından mı, iç duvarlar kaç cm?") yine de gerekli; 01 için ayrıca "bu kroki kendi içinde kapanmalı mı?"
sorulmalı.

Sonuçlar: `sonuclar/olcum.json`, `sonuclar/duvar_kalinligi.json`.
