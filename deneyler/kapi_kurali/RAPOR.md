# Kapı boşluğu kuralı (mimar cevapları, 3. adım)

**Kural:** Aynı doğrultuda karşılıklı iki duvar ucu arasındaki boşluk (1–8 h) kapı adayıdır. Kapı genişliği sırasıyla
kapı etiketinden (`K90`), boşluğun yakınında okunan kapı genişliğindeki sayıdan (80/90/100/110/120, B-3) ya da ilk
geçişin ölçeğinden (±10 cm) gelir. Kontur boşluğun üstünden kapanır, kapı KAPI katmanına çizilir; etiketten gelmeyen
kapılar KONTROL'de not edilir ("? kapı 90: yakında okunan sayıdan").

Ölçüm: `olcum.py`, 01 ve 02, `--okuma` (Qwen-1 kayıttan, Y2 her klasörde yeniden soruldu → 3 örnek).

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

- **"90" kapıya değil komşu duvara bağlanıyor.** Kapı 90'dan çıkarılıyor ama aynı 90 ölçüsü 01'de K6.1'e, 02'de
  K12.1'e yazılıyor (gerçekte kapı açıklığı); bu yüzden "90" her örnekte yanlış sayılıyor. Sonraki küçük düzeltme
  adayı: kapıyı veren sayı, kapı açıklığının ölçüsü olarak bağlansın.
- 01'de kapı seçimi ipuçlarının boşluğa uzaklık sırasına bağlı; yakında ikinci bir kapı genişliğinde sayı olsaydı
  yanlış boşluk seçilebilirdi.
- 120 hem kapı genişliği hem duvar uzunluğu olabilir ("120 sol"); dik uç durumu için uzun duvar (≥ 6 h) şartı bu
  yüzden konuldu.

Sonuçlar: `sonuclar/olcum.json`.
