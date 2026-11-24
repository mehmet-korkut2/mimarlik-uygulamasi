# 01'in şekli neden yanlış: kenar kenar hata listesi

> **Güncelleme (2026-11-24): uygulananlar.** Ö1 (kalibrasyon): dönüşüm doğru, düzeltilecek katsayı yok
> (`../konum_kalibrasyon/RAPOR.md`). Ö2 (değer atama yerel/sınırlı + "emin" yakınlık şartı) uygulandı; ölçekten
> kapı kaldırıldı (02'nin şeklini bozuyordu). 01'in kapısı eski atamada şans eseri bulunuyormuş: artık 01
> kontursuz, boşluk "kapı mı?" diye soruluyor (`../deger_atama/RAPOR.md`). Ö3, Ö4, Ö5 yeni krokiler gelene kadar
> bekliyor.

Tarih: 2026-11-24 · Kod değiştirilmedi. Girdi: `output/dwg/01_kolay_tek_oda_180x140.json` (mimarın AutoCAD Web'de
baktığı DWG'nin raporu; Qwen-1 cevabı `--okuma` kaydından). Gerçek: `../eslestirme/puanlama_eslestirme.py`
(gerçek kenarlar), `../bul_kes_okut/konumlar.py` (gerçek sayı kutuları).

## Kısa cevap

**Sıra ve yön hatası yok.** Bulunan 8 kenarın sırası ve yönü gerçek konturla birebir aynı; köşeler gerçeğe
~10 px içinde. "Merdiven" görüntüsü **değerlerin komşu kenarlara kaymasından** geliyor: K3'e 40 yerine 120,
K4'e 120 yerine 10 yazılmış. Böylece sağdaki çıkıntı 3 kat geniş ve 12 kat alçak bir basamağa dönüşüyor.

Kayma, **değer atama** adımında başlıyor: Qwen'in sayı kutuları 01'de 10 sayının 6'sında 1,7–16,5 h kayık. Değer
atama ise geniş bir mesafe sınırıyla (köşegenin %20'si ≈ 12,7 h) bütün krokiyi birlikte eşlediği için kayma
zincirleme yayılıyor. Bölgeler (sayının kâğıttaki yeri) ve bölgeden duvara bağlama (tik) doğru: **yanlış olan,
bölgeye hangi değerin yazıldığı.**

Şekil hatalarının hepsi programın kendi hatası. 01'in çizim hatası (toplamlar 40 / 53 cm tutmuyor) şekli bozmuyor;
yalnız kapanma farkını oluşturuyor ve bu fark doğru şekilde "KAPANMIYOR" olarak gösteriliyor.

## Kenar kenar karşılaştırma

| Kenar | Yön (bulunan = gerçek) | Programın değeri | Gerçek değer | Doğru mu | Hata |
|---|---|---|---|---|---|
| K1 (üst) | → | 180 | 180 | ✓ (108 de aynı parçaya düştü) | H4 |
| K2 (sağ üst, aşağı) | ↓ | 40 | 50 | ✗ | H1 |
| K3 (basamak, sağa) | → | 120 | 40 | ✗ (merdiven) | H1, H2 |
| K4 (sağ, aşağı) | ↓ | 10 | 120 | ✗ (merdiven) | H1 |
| K5 (alt) | ← | 140 | 140 | ✓ | — |
| K6 (sol alt, yukarı) | ↑ | 90 + 15 = 105 | 10 + 90 + 15 = 115 | ✗ (10'luk parça yok) | H5, H3 |
| K7 (sol basamak) | ← | 120 | 120 | ✓ (Y2'den; geometrik yol yanlıştı) | H1 |
| K8 (sol, yukarı) | ↑ | 95 (ölçekten tahmin) | 108 | ✗ | H4 |

## Bölgeye yazılan değerler (kaymanın kendisi)

| Kâğıttaki sayı | Bölge doğru bulundu mu | Tik / bağlandığı parça | Bölgeye yazılan değer |
|---|---|---|---|
| 180 | ✓ | tik → K1 ✓ | 180 ✓ |
| 50 | ✓ | tik → K2 ✓ | **40** |
| 40 | ✓ (kılavuz çizgisiyle birlikte, en/boy 4,2) | tik → K3 ✓ | **120** |
| 108 | ✓ | tik bulunamadı → en yakın K1 ✗ | 108 ✓ |
| 120 sol | ✓ | temas → K7 ✓ | **50** |
| 120 sağ | ✓ | tik → K4 ✓ | **10** |
| 15 | ✓ | tik → K6.2 ✓ | 15 ✓ |
| 90 | ✓ | en yakın | **120** |
| 10 | ✗: sayı okunmadı; eğri kuyruğu ayrı bölge sayıldı | kuyruk → K6.1 | kuyruğa **90** |
| 140 | ✓ | tik → K5 ✓ | 140 ✓ |

Qwen kutularının kayması (kutu merkezi ile gerçek merkez arası, h = 37 px): 180 0,5 h · 140 0,4 h · 108 1,7 h ·
50 2,0 h · 40 2,5 h · 120 sol 2,8 h · 120 sağ 4,1 h · 15 8,1 h · 90 8,4 h · 10 16,5 h.
**Sistematik bir sola kayma da var:** kutu merkezlerinin x'i gerçeğin medyan 0,89 katı (01: 0,886; 02: 0,90),
y'de belirgin kayma yok (01: 0,998; 02: 0,948). Sebebi bilinmiyor; koordinat dönüşümünde bir hata ya da modelin
(veya Ollama'nın görüntüyü yeniden boyutlandırmasının) yanlılığı olabilir. Bu yalnız birer Qwen-1 kaydında ölçüldü.

## Hatalar

| # | Hata | Nerede başlıyor | Çizim hatası mı, program mı | Düzeltilirse 02'yi etkiler mi |
|---|---|---|---|---|
| **H1** | Değerler komşu bölgelere kayıyor (50 → 40, 40 → 120, 120 sağ → 10, 120 sol → 50, 90 → 120). **Merdivenin sebebi.** Kayık bölgedeki tikli sayı "emin" bile işaretleniyor (K2 = 40, emin): "emin" yalnız bölge → parça bağlamasına bakıyor, değer → bölge eşlemesine bakmıyor | **Bağlama** (değer atama, `eslestirme.degerleri_ata`); kökü OCR konumu (Qwen kutuları) | Program | **Evet.** Aynı adım; 02'deki "90 → '40 üst' bölgesi" (S7) aynı sınıf. İkisinde birlikte ölçülmeli |
| **H2** | "40"ın bölgesi kılavuz çizgisini (`⌐40`) de içeriyor; 3 haneli gibi görünüp "120"yi çekiyor | **Bölge bulma** (`bolge_bulma`; hata analizi S9) | Program (mimarın normal çizim alışkanlığı) | **Evet.** 02'de "15" ve "45 üst sağ" kılavuz çizgili |
| **H3** | "10" okunmadı (bölgesi atanmamış); eğri kuyruğu ayrı bir "sayı" bölgesi sayıldı ve ona 90 yazıldı | **Bölge bulma** + değer atama | Program | **Evet**, aynı nedenle (02'de eğri kılavuzlar) |
| **H4** | 108'in kısa tiki bulunamadı → en yakın parça K1 (108 ile K8 ve K1 arası uzaklık neredeyse eşit). K8 değersiz kaldı → ölçekten 95 | **Bağlama** (işaret bulma; hata analizi S8b, kısa tik) | Program | **Olabilir.** 02'deki tikli bağlamalar şu an doğru; tik eşiği gevşerse sahte tik riski. Gerileme ölçümü gerekli |
| **H5** | Kapı açıklığı alttaki 10 cm'lik kısa duvarı yutuyor; kapı köşeye dayanıyor (gerçekte 10 cm içeride) | **Kenar bulma / kapı kuralı** (dik uç durumu, `SANAL_DUVAR` 0,5 h; kısa parça çizgi olarak bulunmuyor) | Program (krokide parça çizili) | **Büyük olasılıkla hayır:** 02'nin kapısının iki yanı da çizili, dik uç durumu kullanılmıyor. Yine de kenar bulma eşiği değişirse 02 yeniden kontrol edilmeli |
| H6 | Kapanma farkı yatay 40 / dikey 53 cm | — | **Çizim hatası** (mimar doğruladı) | — (doğru davranış: "KAPANMIYOR") |

Doğru değerlerle bu şekil krokiye benzer çıkar; yalnız 40 / 53 cm'lik açık (çizim hatası) "KAPANMIYOR" olarak
kalır. 01'in fotoğrafından beklenen doğru çıktı budur.

## Düzeltme önerileri (uygulanmadı, onay bekliyor)

| Öneri | Hedef | Yapılacak | Risk / 02 |
|---|---|---|---|
| **Ö1** Qwen kutularındaki sistematik x kaymasını ölç | H1'in kökü | Önce deney, ürün kodu değişmez: eski konum deneyi kayıtlarında (çok çalıştırma, 01–02) x oranı tutarlı mı? Tutarlıysa sebebi bul (dönüşüm hatası mı, model mi); kalibrasyon ancak ondan sonra | Düşük. 02'de de aynı kayma var: düzelirse 02 de iyileşebilir |
| **Ö2** Değer atamayı yerel ve sınırlı yap | H1 | Mesafe sınırını köşegen yerine h ile (ör. birkaç h) koy; kutusu hiçbir bölgeye yakın olmayan değer zorla atanmasın, "yeri bulunamadı" kalsın (Y2 ya da kullanıcı). "Emin" için kutu–bölge yakınlığı da şart olsun | Orta. Daha çok sayı "yeri bulunamadı"ya düşebilir; ama yanlış ve "emin" görünen değer yerine soru sorulur (ürün hedefi: taslak + hızlı düzeltme). 01 ve 02'de birlikte ölçülmeli |
| **Ö3** Kılavuz çizgilerini bölgeden ayır | H2, H3 | Rakama bağlı ince düz çizgi (`⌐40`) ve eğri kuyruk ("10") bölge kutusundan çıkarılsın; tek başına kuyruk bölge sayılmasın | Orta. 02'deki kılavuzlu sayılar (15, 45) etkilenir; ölçülmeli |
| **Ö4** Kısa tiki yakala | H4 | Tik uzunluğu alt sınırını gevşet ya da "duvara değen ve yazıya bakan kısa çizgi" kuralı ekle | Orta–yüksek: sahte tik → "emin" yanlış bağlama. 02'deki tikli bağlamalar gerileme testi olmalı |
| **Ö5** Kapı yanındaki kısa duvar | H5 | Dik uç durumunda kapının ucundaki kısa çizgiyi (≈ 0,5–1 h) parça olarak koru ya da yakındaki sayıyla (10) boyunu al | Düşük (01'e özgü durum) |

Önerilen sıra: **Ö1** (ucuz, kodsuz deney; H1'in kökü olabilir) → **Ö2** (merdiveni doğrudan hedefler) → Ö3 →
Ö5 → Ö4. Her adım 01 ve 02'de ölçülür. Ölçütler: bağlama, şekil (kenar değerleri) ve 02'nin mimarın onayladığı
şeklinin korunması. Kapanma, kararımız gereği 01–02'de doğruluk ölçütü değil.
