# 01 ve 02 çizim hatalı: etkisi ve 01–02'ye göre konmuş kurallar

Tarih: 2026-11-24 · Kod değiştirilmedi (yalnız `tests/test_cizim_hatali.py` eklendi).

## Bulgu

Mimar, 01 ve 02'yi **hatalı çizdiğini doğruladı**. Toplamların tutmaması bizim yorumumuzdan (iç ölçü, duvar
kalınlığı, S1/S3) değil, **çizim hatasından** geliyor. Krokiye yazılan gerçek sayılar gerçek dış hatta yerleştirilince
kalan fark (`../kapi_kurali/olcum.py`, "ideal kapanma"):

| Kroki | Yatay fark | Dikey fark |
|---|---|---|
| 01 | 40 cm | 53 cm |
| 02 | 48 cm | 60 cm |

**Kapanma kontrolü gerçek bir hatayı yakaladı.** İç duvar kalınlığı denemesinin (`../kapi_kurali/RAPOR.md`) farkı
açıklayamaması da bununla tutarlı.

**Karar (kullanıcı):** 01 ve 02, "çizim hatalı: kapanma kontrolü bunu yakalamalı" test vakasıdır
(`tests/test_cizim_hatali.py`). **Okuma ve bağlama ölçümünde geçerli, geometri / kapanma / DXF doğruluğunda
kullanılmaz** (kullanıcı kararı, aşağıdaki "Ayrım"). Mimardan düzeltilmiş ölçüler istendi; gelince
01–02'nin "doğru hali" test verisi olarak eklenecek.

## Hangi sonuçlar etkilendi

| Sonuç | Durum |
|---|---|
| Bütün 01–02 kapanma farkları (iskelet: 02 yatay 57 / dikey 85; S3 adımı: 02 dikey 85 → 0; kapı kuralı: 01 40 / 150–163, 02 0–12 / 61–95) | **Başarı ölçüsü değil.** Doğru okuma ve bağlamayla bile kapanmaması gerekiyordu. Bir 01–02 çalıştırması "kapanıyorsa" (02, kapı bağlama düzeltmesi, 3. örnek: 0 / 0) bu bir hata işaretidir |
| S3 = B adımında "02 dikey 85 → 0" | Kapanmadan hesaplanan bir kenarın farkı yutmasıydı; anlamı yok |
| İdeal kapanma ve duvar kalınlığı denemesi | Açıklandı: fark çizimden |
| OCR (22–23/24), bağlama (x/10, x/14), "emin" isabeti | Krokide yazanla karşılaştırılıyor; çizim hatası yazılan sayıyı değiştirmiyor. **Geçerli** (bkz. "Ayrım") |
| Kontur bulma (01: 8 kenar, 02: 12 kenar, parçaların gerçek parçalarla eşleşmesi) | Krokinin çizgilerine bakıyor, sayılara bakmıyor; etkilenmedi |

## 01–02'ye bakılarak konmuş kurallar ve eşikler

Değerlendirme sorusu: kural, **sayıların birbiriyle tutarlı olmasına** dayanıyor mu (o zaman çizim hatasından
etkilenmiş olabilir), yoksa yalnız **çizimin görüntüsüne** mi (o zaman bu hatadan etkilenmez; ama iki krokiden
ayarlandığı için genelleşmeme riski yine var)?

### A. Sayıların tutarlılığına dayananlar: çizim hatasından etkilenmiş olabilir

| Kural / eşik | Yer | Neden 01–02'den | Değerlendirme |
|---|---|---|---|
| Tek bilinmeyen kenarın boyunu kapanmadan hesaplama ("hesaplandi") | `geometri.plan_kur` | Genel kural, ama yalnız 01–02'de denendi | **Etkilenmiş.** Hatalı krokide farkı bilinmeyen kenara yükler ve kapanma kontrolünü susturur: hata kaybolur. S3 = B'de "02 dikey 85 → 0" bu yüzden çıkmıştı. Doğru krokilerle yeniden denenmeli; hatalı krokide farkın bir kenara yüklendiği kullanıcıya açıkça gösterilmeli |
| Ölçek (okunan kenarların cm/px medyanı) ve ilk geçişin ölçeği `olcek0` | `geometri._olcek`, `kroki.coz` | Ölçek yalnız 01–02'de kuruldu | **Etkilenmiş olabilir.** Yanlış yazılmış bir sayı ölçeği kaydırır. Medyan tek bir hatalı sayıya dayanıklı, ama 01'de yalnız 8 kenar var |
| `KAPI_OLCEK_PAYI = 10` cm (ipucu yoksa ölçekten kapı genişliği) | `kenar_bulma` | 01–02'de hiç kullanılmadı (iki kapı da okunan sayıdan geldi) | **KALDIRILDI (2026-11-24):** değer atama sıkılaşınca ölçek kaydı ve 02'nin girinti ağzı kapı sanıldı. Kanıtsız boşluk artık sorulur (`../deger_atama/RAPOR.md`) |
| `KAPI_DIK_UC_DUVARI = 6` h ("120 sol" kuralı) | `varsayimlar` | 01'de "120 sol" kapı genişliğine (120) uyduğu için sahte kapı çıkıyordu | **Belirsiz, şüpheli.** Kural sayının değerine dayanıyor. Hatalı sayı "120 sol" ise (01'in yatay farkı 40 cm; tek sayının hatalı olduğu varsayılırsa adaylar: 180 → 220, 40 → 80, 140 → 100 ya da 120 → 80) kuralın gerekçesi değişir. Ayrıca 6 h'den kısa dik duvarın yanındaki gerçek kapıları engelleyebilir. Önce düzeltilmiş ölçüler, sonra yeniden değerlendirme |

### B. Okunan sayının değerine ve yerine dayananlar: yalnız hatalı sayı işin içindeyse etkilenir

| Kural / eşik | Yer | Değerlendirme |
|---|---|---|
| Kapı seçme sırası etiket → okunan sayı → ölçek | `kenar_bulma._kapi_secimi` | Kullanıcı kararı, krokiden bağımsız. Hatalı sayı kapı genişliğindeyse (90) yanlış kapı seçilebilir; 01–02'de iki kapı da 90 ve doğru yerde. Etkilenmedi |
| Aday boşlukların ipucuna uzaklık sırası | `kenar_bulma._kapi_secimi` | Görsel. Etkilenmedi; bilinen kırılganlık sürüyor (yakında ikinci bir kapı genişliğinde sayı) |
| `KAPI_IPUCU_MESAFESI = 5` h (01: 2,2 h, 02: 4,4 h) | `kenar_bulma` | Görsel. Etkilenmedi; ama 02 sınıra yakın, iki krokiden ayarlandı |
| `KAPI_SAYI_MESAFESI = 5` h (kapı sayısını açıklığa bağlama) | `birlestirme` | Görsel. Etkilenmedi |

### C. Yalnız görüntüye dayananlar: çizim hatasından etkilenmez, iki krokiden ayarlandı

| Kural / eşik | Yer | 01–02 bağlantısı |
|---|---|---|
| Köşe toleransı `0,75 h` | `kenar_bulma.kenarlari_bul` | h/2 ile 02'nin konturu kapanmıyordu (bu, sayıların değil çizgilerin kapanması) |
| `SANAL_DUVAR = 0,5` h | `kenar_bulma` | 01'de kapının altındaki 10 cm'lik parça çizgi olarak bulunamıyor |
| `TASMA_SINIRI = 1,5` h | `kenar_bulma` | 02'de kapının üstündeki parça üst duvarı aşıyor |
| `KAPI_KAYMASI = 1` h, `ACIKLIK_ARALIGI = 1–8` h | `kenar_bulma` | 01–02'deki kapı boşlukları |
| `_duvarin_ortasinda`, "en az bir yan ≥ 3 h" | `kenar_bulma` | 01'de 180'in tikinin üst duvara değmesi |
| `SARKAN_SINIRI = 6` h, `DUVAR_UZUNLUGU = 3` h | `kenar_bulma` | İşaret ve yazı birleşmeleri, 01–02 |
| X açıları (`CARPI_*`) | `kenar_bulma` | 02'deki iki X |
| `GRUPLAMA = (1,0; 0,3)` h | `bolge_bulma` | 02'de gevşek yazılmış "2 0 0" |
| `HANE_KATSAYISI = 0,8` | `eslestirme` | 01–02 gerçek kutularının medyanı 0,814 |
| Mürekkep renk aralığı (mavi) | `on_isleme` | 01–02 mavi tükenmez; 05 ve 07 kırmızı |

Bu gruptaki eşikler çizim hatasından etkilenmez. Ama hepsi aynı kişinin aynı kalemle çizdiği iki krokiden
ayarlandı. 03–07 ve yeni krokilerle yeniden ölçülmeleri gerekiyor.

## Ayrım (kullanıcı kararı, 2026-11-24)

Okuma ve bağlama doğruluğu krokide **yazan** sayıyla ölçülüyor ve çizim hatası yazılanı değiştirmiyor. Bu yüzden
01–02 **okuma ve bağlama ölçümünde geçerli**; **geometri, kapanma ve DXF doğruluğunda geçersiz.**

## Yapılan değişiklik: kapanmadan hesaplanan kenar farkı gizlemiyor

A grubundaki ilk kural değiştirildi (`geometri.plan_kur`, `plan_cizimi`): bir eksende kapanmadan hesaplanmış kenar
varsa o eksenin kapanması `"durum": "dogrulanamadi"` (`"tutuyor": False`); hesaplanan kenar KONTROL'de çizgiyle ve
"? K5 … cm: okunmadı, kapanmadan hesaplandı" notuyla işaretli; başlık "DOĞRULANAMADI". Aynı kayıtlarla 01–02
yeniden çalıştırıldı (`output/adim5*`): 02'nin 3. örneği daha önce yanlış bağlamaya rağmen 0 / 0 "kapanıyordu";
artık iki eksende de "doğrulanamadı: K5 / K12 kapanmadan hesaplandı". Diğer beş çalıştırma değişmedi (kapanmıyor).

## Mimardan beklenen

- 01 ve 02'nin **düzeltilmiş ölçüleri**: hangi sayı(lar) yanlış ve doğrusu ne?
- Gelince: `tests/` altına "doğru hal" verisi (aynı dış hat, düzeltilmiş sayılar, kapanmalı). Bu, kullanıcının bir
  sayıyı düzeltince planın kapandığını da test eder (Faz 2 hedefi "taslak + hızlı düzeltme").
- Fotoğraf hatalı sayıları göstermeye devam eder: programın 01–02 fotoğrafından doğru çıktısı "kapanmıyor" uyarısıdır.
