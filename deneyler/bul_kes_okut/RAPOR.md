# "Bul → kes → okut" Deneyi: Rapor (adım 2'de kapatıldı)

Tarih: 2026-11-17 · Ham çıktı: `sonuclar/ust_sinir.json` · Gerçek kutular: `konumlar.py` ·
Kontrol görselleri: `gorseller/` (**`.gitignore`'da**): `gercek_kutular_*.jpg`, `ust_sinir_*_calistirma*.jpg`

## Sonuç

**Kesitten okuma, bütün fotoğraftan belirgin şekilde kötü; bulucu adımına geçilmedi.** Gerçek kutulardan
kesilen kesitlerde bile 24 sayıdan 15/14/14 doğru okundu. Bütün fotoğrafta 22–24 doğru okunuyordu.
Süre 3–4 kat arttı ve `102` → `162` hatası kesitte de sürdü. Deney kapatıldı (kullanıcı kararı,
2026-11-17). Gerçek kutular (`konumlar.py`) kullanıcı tarafından kontrol edilip doğrulandı. Bu kutular
sayı–duvar eşleştirmesinde yeniden kullanılabilir.

## Durum

Kullanıcının koşulu: "Kesitten okuma dünküyle aynı ya da daha iyiyse bulucu adımına geç; belirgin şekilde
kötüyse dur." **Kesitten okuma belirgin şekilde kötü çıktı, bulucu adımı (EasyOCR detector, OpenCV)
yapılmadı.**

## Üst sınır: gerçek kutulardan kesip okutma

- **Kesitler:** 24 sayının gerçek kutusu her yöne yüksekliğin yarısı kadar (en az 15 px) genişletildi ve
  kesildi. Kısa kenarı 224 px'e büyütüldü.
- **İstem:** "Bu sayı ne? Yoksa YOK yaz."
- **Ayarlar:** `qwen3-vl:4b-instruct`, `num_ctx` 8192. Model çalıştırma boyunca bellekte kaldı.

| | 01 doğru /10 | 02 doğru /14 | Toplam /24 | Fazla | Kroki başına süre |
|---|---|---|---|---|---|
| Bütün fotoğraf, sadece sayı (dün) | 10 / 10 / 10 | 13 / 12 / 12 | **23 / 22 / 22** | 1 / 1 / 1 | ~60 s |
| Bütün fotoğraf, sayı + kutu | 10 / 10 / 10 | 12 / 14 / 12 | **22 / 24 / 22** | 5 / 5 / 3 | 116–177 s |
| **Kesitten okuma (bugün)** | 9 / 8 / 8 | 6 / 6 / 6 | **15 / 14 / 14** | 6 / 6 / 7 | **183 s (01), 250 s (02)** |

### Hangi sayılar yanlış okundu (3 çalıştırma)

| Sayı | Okunan | Not |
|---|---|---|
| 01 `40` | YOK ×3 | "4" bu el yazısında "u"ya benziyor |
| 01 `108` | 80 (1 kez) | |
| 01 `90` | YOK (1 kez) | |
| 02 `45` üst sol | 5 / 25 / 15 | |
| 02 `45` üst sağ | 55 ×3 | |
| 02 `45` alt | 15 / YOK / 15 | |
| 02 `90` (`9/0`) | 960 ×3 | Bölü çizgisi "6" sanılıyor |
| 02 `40` sol alt | 120 ×3 | |
| 02 `40` sağ alt | YOK ×3 | |
| 02 `240` | YOK ×3 | |
| 02 `102` | **162 ×3** | Bkz. aşağı |

### `102` → `162`

Temiz, büyütülmüş, tek başına bir kesitte bile üç çalıştırmada da `162` okundu. Kesite bakınca olası
neden görünüyor: **defterin dikey çizgisi tam `0`'ın ortasından geçiyor**, `0` "6"ya ya da "φ"ye
benziyor. Yani bu hata bağlam eksikliğinden değil, defter çizgisinden kaynaklanıyor olabilir.
Önceki deneyde önerilen **"kes, büyüt, tekrar okut" bu hatayı tek başına düzeltmedi.**

> **Düzeltme (aynı gün, `../cizgi_silme/RAPOR.md`):** Defter çizgileri silindikten sonra da `0`'ın
> içindeki çizgi kaldı. Yani çizgi mürekkep, büyük olasılıkla ölçü işareti. "Defter çizgisi" hipotezi
> büyük olasılıkla yanlış.

## Neden daha kötü? (hipotezler, test edilmedi)

1. **Bağlam kaybı:** Bütün fotoğrafta model aynı el yazısının "4"ünü birçok kez görüyor; ayrıca sayının
   bir duvar ölçüsü olduğunu ve krokideki diğer sayıları biliyor. Tek başına bir "u0" belirsiz kalıyor.
   Hataların çoğu `4` içeren sayılarda (`40`, `45`, `240`); bu hipotezi destekliyor.
2. **"YOK" seçeneği kaçış yolu:** 7 okumada model "YOK" dedi. İstem "emin değilsen YOK" anlamına
   kayıyor olabilir.
3. **Defter çizgileri:** Kesitte çizgi rakamla aynı büyüklükte görünüyor, bütün fotoğrafa göre daha
   baskın. Örnekler: `102`, `90` (`9/0`).

## Süre

- Kesit başına ~17,5 s. Küçük bir kesit bile ~1.170 görüntü token'ı tutuyor; bütün fotoğraf ~2.440.
  Ollama küçük görüntüyü büyütüyor ya da 224 px'e büyütmemiz pahalıya geliyor olabilir (ölçülmedi).
- Kroki başına 183–250 s, yani bütün fotoğrafı okumanın 3–4 katı. Bulucu adımı eklenince kesit sayısı
  (yazı olmayan bölgeler dahil) artacağı için süre de artar.

## Sınırlar

2 kroki, 24 sayı, tek istem, tek kesim ayarı. Gerçek kutular elle çizildi ve kullanıcı tarafından doğrulandı.
