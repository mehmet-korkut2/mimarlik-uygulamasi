# Mimarlık Uygulaması — Proje Bağlamı ve Yol Haritası

> Bu dosya, projeyi her yeni sohbette / Claude Code oturumunda baştan anlatmamak için hazırlandı.
> Claude Code için: bu dosyayı repo köküne `CLAUDE.md` olarak koy (ya da `CLAUDE.md` içinden buna referans ver).

---

## 1. Ben ve çalışma şeklim

- **Mehmet Korkut**, İstanbul Gelişim Üniversitesi, Bilgisayar Mühendisliği 4. sınıf.
- Bildiğim diller: C++, Java, Python, C, Unity (C#). İngilizcem B2. **Bana Türkçe cevap ver.**
- Projeyi **tek başıma, sıfırdan** yapıyorum; ileride ekip gerekeceğini biliyorum.
- **Temelden, adım adım** ilerlemek istiyorum: her adımda ne yaptığımızı ve nedenini açıkla, büyük kod bloklarını tek seferde yığma.
- Bir şey önerdiğimde hemen onaylama; önce mantıklı mı diye değerlendir, **artılarını ve eksilerini** söyle.
- Alan danışmanlarım: bir **mimar** ve bir **iç mimar** (ailemden; onlardan "mimar" ve "iç mimar" diye bahset). Mimari kurallar, çizim standartları ve gerçek iş akışı konusunda onlara soruyorum.

## 2. Proje özeti

Mimarların ve iç mimarların çizim işini otomatikleştiren bir uygulama.

**Seçilen ilk ürün:** Mimarın **elle çizdiği planı** (kâğıt, fotoğraf ya da tarama) alıp **AutoCAD'de açılıp düzenlenebilen bir dosyaya** dönüştürmek.

**Uzun vadeli vizyon:** İç mimarın tüm işini kapsamak (konut, diş kliniği, okul, restoran, kafe vb.), modül modül.

### Planlanan sıra
1. **El çizimi → AutoCAD** (çekirdek ürün)
2. **AutoCAD çizimine mobilya/obje ekleme** (6 kişilik masa, yatak, kanepe vb. 2D bloklar). Bu, iç mimarın fikri.
3. **3D modelleme** (en son; bu konuda henüz pek fikrim yok)

## 3. Temel teknik kararlar (taslak, tartışmaya açık)

| Konu | Karar | Neden |
|---|---|---|
| Ana dil | **Python** | Görüntü işleme (OpenCV), ML ve DXF kütüphaneleri en olgun bu dilde |
| Çıktı formatı | **DXF** (`ezdxf` kütüphanesi) | AutoCAD DXF'i doğrudan açar ve düzenler. DWG kapalı bir format; gerekirse ODA File Converter ile DXF→DWG dönüşümü yapılır |
| Görüntü işleme | **OpenCV** | Ön işleme, çizgi/kontur tespiti |
| Yazı/ölçü okuma | Başta EasyOCR / Tesseract, sonra gerekirse özel model | Plandaki ölçüleri ve oda adlarını okumak için |
| Arayüz | Önce **komut satırı → basit web arayüzü** (FastAPI + basit frontend). Mobil/masaüstü uygulama sonra | Ben uygulama tarafına yakınım, ama çekirdek algoritma çalışmadan arayüze yatırım yapmak riskli. Backend aynı kalır, sonradan mobil arayüz eklenir (fotoğraf çekmek için mobil mantıklı) |
| Sürüm kontrolü | Git + GitHub (github.com/mehmet-korkut2) | |

## 4. Yol haritası

### Faz 0 — Hazırlık (1–2 hafta)
- [ ] Mimar ve iç mimarla görüşme: elle çizilmiş **gerçek örnek planlar** topla (en az 10–20 adet, farklı çizim stilleri).
- [ ] Onlardan şunları öğren: duvar kalınlıkları, kapı/pencere sembolleri, ölçek alışkanlıkları (1/50, 1/100), AutoCAD'de katman (layer) düzenleri.
- [ ] Her örnek plan için mümkünse **aynı planın AutoCAD versiyonunu** da iste (doğruluğu ölçmek için referans olur).
- [ ] Python ortamı kur: `venv`, `opencv-python`, `ezdxf`, `numpy`, `pytest`.
- [ ] GitHub reposunu aç, bu dosyayı `CLAUDE.md` olarak ekle.

**Bitti sayılır:** Klasörde örnek planlar var, ortam çalışıyor, repo açık.

### Faz 1 — DXF'i tanımak (1 hafta) — ✅ BİTTİ (2026-11-24)
- [x] `ezdxf` ile koddan basit bir DXF üret: dikdörtgen oda, duvar çizgileri, katmanlar (DUVAR, KAPI, PENCERE, ÖLÇÜ).
- [x] Dosyayı AutoCAD'de (veya ücretsiz bir DWG/DXF görüntüleyicide) açıp düzenlenebildiğini doğrula.
- [x] Birim ve ölçek mantığını öğren (DXF'te birim = mm/cm/m).
- [x] DWG çıktısı (mimar B-12): ODA File Converter ile AutoCAD 2013 biçimi; AutoCAD Web'de düzenlenebilir modda açıldı ve düzenlendi, ölçü yazıları, çizgi kalınlıkları ve Türkçe karakterler görünüyor (**doğrulandı, 2026-11-24**).

**Bitti sayılır:** Koddan ürettiğim bir oda planı AutoCAD'de düzgün açılıyor ve düzenlenebiliyor. → Sağlandı (DXF 2026-11-16, DWG 2026-11-24).

### Faz 2 — Tek oda krokisinden DXF'e (3–5 hafta)
> **Yaklaşım değişikliği (2026-11-16):** Gerçek röleve krokileri ölçekli değil; kâğıtta aynı boyda çizilmiş iki duvarın yanında 180 ve 140 yazabiliyor. Doğru bilgi **duvarların yanına yazılan sayılar**. Bu yüzden "bir ölçü gir, pikselden ölçekle" yaklaşımı bırakıldı: program krokiden duvarların **sırasını ve yönünü** çıkarır, **sayıları okur**, geometriyi sayılardan kurar. Sayı okuma (OCR) bu yüzden Faz 3'ten Faz 2'ye alındı.

Girdi: `ornekler/01_*`, `ornekler/02_*` (tek oda, tek çizgi, dik açılı, çizgili defter).
- [ ] Ön işleme: perspektif düzeltme, defterin çizgi/noktalarını temizleme, mürekkebi ayırma (renk ipucu: bazı krokilerde ölçüler farklı renkte).
- [ ] Duvar dizisini çıkarma: çizgi tespiti + 0°/90° yakalama → kapalı poligonun kenar sırası ve yönleri.
- [ ] Ölçü sayılarını okuma: el yazısı, virgüllü, yan/ters yazılmış. Klasik OCR (EasyOCR/Tesseract) ile görüntü anlayan bir yapay zekâ modelini 01–02 üzerinde karşılaştır; doğruluk, maliyet ve bağımlılık açısından seç.
- [ ] Sayıyı doğru duvarla eşleştirme (en yakın kenar, tick işareti).
- [ ] Geometriyi sayılardan kurma; şekil kapanmıyorsa (toplamlar tutmuyorsa) nerede tutmadığını göster.
- [ ] Kullanıcı onayı: okunan sayıların düzeltilebilir listesi. Hedef "%100 otomatik" değil, "taslak + hızlı düzeltme".
- [ ] Sonucu DXF'e yaz (Faz 1 modülü `mimarlik/dxf_yazici.py`).

**Bitti sayılır:** 01 ve 02 krokilerinin fotoğrafından, mimarın verdiği "doğru ölçülerle" aynı DXF çıkıyor; kullanıcı en fazla birkaç sayıyı düzeltiyor. (01–02 çizim hatalı çıktı: fotoğraftan doğru çıktı "kapanmıyor" uyarısı; kullanıcı mimarın düzelttiği sayıları girince plan kapanmalı.)

### Faz 3 — Çok odalı planlar ve semboller (4–8 hafta, en zor kısım)
Girdi: `ornekler/03_*` – `ornekler/07_*`.
- [ ] Çift çizgili / taralı duvarlar ve duvar kalınlığı.
- [ ] Kapı, pencere, kolon sembolleri (önce kural tabanlı, sonra gerekirse makine öğrenmesi).
- [ ] Eğik duvarlar; köşegen ölçülerle (kutu içindeki sayılar olabilir, mimara sorulacak) üçgenleme.
- [ ] Yükseklik notları (`H=`, `h1`, `h2`), kesikli çizgiler, oda adları.
- [ ] Birden fazla oda ve ortak duvarlar.
- [ ] Her öğeyi doğru katmana yerleştir.
- [ ] Kâğıt türleri (mimar, B-8: kareli, düz ve aydınger hepsi kullanılıyor): ön işleme hepsine dayanıklı olmalı (çizgi ve nokta silme). Şu an yalnız çizgili defter destekleniyor.
- [ ] Doğruluk ölçümü: mimarın verdiği "doğru cevap" ölçüleri / AutoCAD dosyalarıyla karşılaştır.

**Bitti sayılır:** Çıktı DXF'te duvar, kapı ve pencere ayrı katmanlarda; mimar dosyayı açınca "bunu düzeltmek sıfırdan çizmekten hızlı" diyor.

### Faz 4 — Kullanılabilir prototip (2–3 hafta)
> **Karar (2026-11-19):** Mobil uygulama yerine telefonda da çalışan web arayüzü. Telefon tarayıcısından kamerayla fotoğraf yüklenebilmeli; düzeltme ekranı bilgisayar için tasarlanmalı. Mimar gerçek kullanımda mobil uygulama isterse aynı backend'e bağlanan bir uygulama sonra eklenir.

- [ ] FastAPI ile backend: görsel yükle → DXF indir.
- [ ] Basit web arayüzü: yükleme, önizleme, okunan ölçüleri düzeltme, indirme.
- [ ] Mimar ve iç mimara gerçek işlerinde denet, geri bildirim topla.

### Faz 5 — Mobilya/obje ekleme modülü
- [ ] 2D mobilya blok kütüphanesi (masa, yatak, kanepe, dolap vb.); iç mimardan standart ölçüler al.
- [ ] Mevcut bir DXF'i oku, odaları tespit et.
- [ ] Komutla ekleme: "salona 6 kişilik masa ekle" → doğru bloğu uygun konuma yerleştir.
- [ ] Sonra: yazılı komutları anlamak için LLM entegrasyonu.

### Faz 6 — 3D (uzun vade)
- [ ] 2D plandan duvarları yükselterek basit 3D model (extrude).
- [ ] Format seçenekleri: DXF 3D, IFC, ya da SketchUp/Blender'a aktarım. Bu fazda ayrıca araştırılacak.

## 5. Riskler ve dürüst değerlendirme

**Artılar**
- Gerçek bir problem: elle çizilen planı AutoCAD'e aktarmak zaman alan, sıkıcı bir iş.
- Alan uzmanlarına (mimar, iç mimar) doğrudan erişimim var; çoğu kişide bu yok.
- Modüler yapı: her faz kendi başına gösterilebilir bir çıktı. CV'ye ve portfolyoya yazılabilir.

**Eksiler / riskler**
- **El çizimi tanıma çok zor.** Çizim stilleri, eğri çizgiler ve kötü fotoğraflar doğruluğu çok düşürür. Çözüm: girdiyi kısıtla (kareli kâğıt, net fotoğraf, ölçek referansı) ve "%100 otomatik" yerine **"kullanıcının hızlıca düzelttiği yarı otomatik"** bir ürün hedefle.
- **Makine öğrenmesi için veri lazım.** Faz 3'te kural tabanlı yöntem yetmezse etiketli veri gerekecek; toplaması zaman alır.
- **Rakip çözümler var** (raster→vektör dönüştürücüler, AutoCAD'in kendi araçları). Farkımız mimari anlamlandırma (duvar/kapı/katman) olmalı. Faz 2'den önce rakipleri kısaca incele.
- **Kapsam şişmesi:** Faz 3 bitmeden 3D'ye veya mobil uygulamaya geçme.
- **Zaman:** Okul, bitirme projesi ve staj başvurularıyla paralel yürüyor; fazların süreleri tahmini.

## 5.1 Örnek çizimler

`ornekler/` klasöründe, zorluk sırasıyla adlandırılmış 7 gerçek röleve krokisi var (fotoğraf). **Klasör `.gitignore`'da: müşteri işi olabilir, GitHub'a gönderilmez.** Hiçbirinin AutoCAD karşılığı yok; doğrulama için mimardan 01 ve 02'nin "doğru ölçüleri" istenecek.

> **01 ve 02 çizim hatalı (mimar doğruladı, 2026-11-24).** Bunlar "çizim hatalı: kapanma kontrolü bunu yakalamalı" test vakasıdır (`tests/test_cizim_hatali.py`). **Okuma ve bağlama ölçümünde geçerli** (krokide yazan sayıyla ölçülür, çizim hatası yazılanı değiştirmez); **geometri, kapanma ve DXF doğruluğunda kullanılmaz.** Mimardan düzeltilmiş ölçüler istendi; gelince 01–02'nin "doğru hali" test verisi olarak eklenecek. 01–02'ye göre konmuş kurallar ve çizim hatasından etkilenip etkilenmedikleri: `deneyler/cizim_hatasi/RAPOR.md`.

| Dosya | Zorluk | Not |
|---|---|---|
| `01_kolay_tek_oda_180x140.jpg` | Kolay | Tek oda, tek çizgi, dik açılı. 15/90/10 doğru okunmuş (mimar). **Çizim hatalı** (mimar doğruladı): toplamlar tutmuyor (yatay 40, dikey 53 cm). **01: şekil yanlış** (mimar, 24.11.2026: programın çıkardığı plan şekli doğru değil) |
| `02_kolay_tek_oda_300x240.jpg` | Kolay | Tek oda, tek çizgi, dik açılı. **Çizim hatalı** (mimar doğruladı): toplamlar tutmuyor (yatay 48, dikey 60 cm). **02: plan şekli mimar tarafından doğru bulundu (24.11.2026), 162→102 okuma hatası hariç** (sol üst girinti, 45/45 basamağı, alt 40'lık girinti, kapı; AutoCAD Web'de DWG üzerinden) |
| `03_orta_egik_duvar.jpg` | Orta | Eğik duvar, kapılar, kesikli çizgi, `h1`/`h2` |
| `04_orta_oda2_wc.jpg` | Orta | Taralı çift çizgili duvarlar, WC, iki oda |
| `05_zor_oda3_balkon.jpg` | Zor | Çok ölçü, köşegenler (kutu içinde), iki renk |
| `06_zor_salon_balkon.jpg` | Zor | Çok oda, köşegenler, kolonlar |
| `07_zor_sauna_yan_cekilmis.jpg` | Zor | Yan çekilmiş, ölçüler kırmızı, duvarlar mavi |

## 6. Claude'a notlar

- Şu an hangi fazda olduğumu her oturumun başında söyleyeceğim. Söylemezsem sor.
- Kodu küçük, test edilebilir parçalar halinde yaz; her parça için nasıl test edeceğimi göster.
- Kütüphane veya yaklaşım seçerken alternatifleri kısaca karşılaştır.
- Mimari bir varsayım yapman gerektiğinde (duvar kalınlığı, sembol vb.) bunu belirt; mimara/iç mimara danışmam gereken soruları listele.

## 7. İlerleme günlüğü

| Tarih | Faz | Ne yapıldı | Sonraki adım |
|---|---|---|---|
| 2026-11-14 | 0 | Yol haritası hazırlandı | Mimar ve iç mimardan örnek el çizimleri toplamak |
| 2026-11-15 | 0 | Claude Code + Superpowers kuruldu, proje klasörü ve CLAUDE.md oluşturuldu | Git reposu, Python ortamı |
| 2026-11-15 | 1 | DXF yazıcı modülü (`mimarlik/dxf_yazici.py`) + örnek oda demosu, 27 test geçiyor | `output/oda_demo.dxf` AutoCAD'de açılıp bir duvar ve bir ölçü düzenlenecek (mimar); açık sorular mimara |
| 2026-11-16 | 1 | Bağımsız inceleme düzeltmeleri (NaN/sonsuz, yay/ölçü doğrulaması, zoom extents) + AutoCAD Web'de bulunan hata: ölçü yazıları görünmüyordu (`dimtxsty` boş, `$DIMSTYLE` yok) → düzeltildi, 43 test geçiyor. Ders: `audit()` temiz ≠ AutoCAD'de doğru | Yeni `oda_demo.dxf`'te 450/350 yazılarını AutoCAD Web'de kontrol et; mimarla elle doğrulama |
| 2026-11-16 | 0→2 | 7 gerçek röleve krokisi alındı (`ornekler/`). Krokiler ölçekli değil → Faz 2 yaklaşımı değişti: geometri yazılı ölçülerden kurulacak, OCR Faz 2'ye alındı | Mimara: 01–02'nin doğru ölçüleri ve yazım alışkanlıkları (kutu içi sayılar, `H=`, kesikli çizgi) |
| 2026-11-16 | 2 | OCR deneyi (`deneyler/ocr_karsilastirma/RAPOR.md`), 01–02 / 24 sayı: EasyOCR 5/24, Gemini 3.6 Flash 24/24, Qwen3-VL 4B (yerel) 22–23/24. Gemini 3.8 Flash ücretsiz katmanda sürekli 503. Fark küçük → yerel yol (Qwen3-VL 4B) öneriliyor | Qwen'den sayıların konumunu da almak (sayı–duvar eşleştirme); duvar toplamı kontrolü; 03–07 ile tekrar (mimarın doğru cevaplarıyla) |
| 2026-11-16 | 1 | AutoCAD testi geçti: `oda_demo.dxf` açılıyor, 4 katman var, birim cm, duvar ve ölçü düzenlenebiliyor. Faz 1 şimdilik açık bırakıldı | — |
| 2026-11-17 | 2 | Konum deneyi (`deneyler/konum_deneyi/RAPOR.md`): Qwen3-VL 4B'den sayı + kutu. Okuma düşmedi (22/24/22, dün 23/22/22) ama fazla sayı 1→3–5, süre ~2 kat. Kutular 01'de %58, 02'de %14 tam doğru; eşleştirme için tek başına güvenilmez. `102→162` hatasında kutu yazının hemen yanında | Kes–büyüt–tekrar okut; konumu ayrı bir yazı bulucuyla (EasyOCR/CRAFT, OpenCV) bulup okumayı Qwen'e bırakmayı dene |
| 2026-11-17 | 2 | Bul–kes–okut (`deneyler/bul_kes_okut/`): gerçek kutulardan kesitle okuma 15/14/14 → bütün fotoğraftan kötü, bulucuya geçilmedi. Çizgi silme (`deneyler/cizgi_silme/`): defter çizgileri renkle silinince 23/23/23 (dün 23/22/22), `102→162` sürdü (çizgi değil, sayıdan geçen ölçü işareti). **OCR iyileştirmesi bırakıldı;** kalan hataları kullanıcı onayı + duvar toplamı kontrolü yakalayacak | Sayı–duvar eşleştirme tasarımı |
| 2026-11-18 | 2 | Sayı–duvar eşleştirme (`deneyler/eslestirme/RAPOR.md`): `mimarlik/` kenar bulma, sayı bölgeleri, değer atama, bağlama (99 test). Gerçek kenarlarla Y2 (Qwen'e numaralı parçaları sormak, karışık numara) 18–19/24 ≈ geometrik yolun (Y1) üst sınırı 19; Y1 gerçekçi 10–14/24. Karar, Y2 bulunan kenarlarla ölçülünce | Y2'yi **bulunan** kenarlarla ölçmek; kenar bulmada kısa parçalar (01 `10/90/15`, kısa tireler) |
| 2026-11-18 | 2 | Y2 bulunan kenarlarla: 13/17/12 /24 (Y1 gerçekçi 13/14/10); tavan kenar bulma (17/24). **Karar:** iki yol birleşir — ölçü tiresi bulunan sayılar geometrik (9/9 doğru), diğerleri Y2; çelişkide ya da Y2 gürültü parçasına değer yazınca kullanıcıya sorulur. Kenar bulma mimar görüşmesine kadar beklemede. Dal `sayi-duvar-eslestirme` main'e birleştirilmedi | Mimara: M1–M5 (`deneyler/eslestirme/RAPOR.md`), özellikle `15/90/10` ve `15/9-0/40`'ın anlamı |
| 2026-11-19 | 4 | **Karar:** mobil uygulama yerine telefonda da çalışan web arayüzü (telefon tarayıcısından kamerayla yükleme; düzeltme ekranı bilgisayar için). Mobil uygulama ancak mimar gerçek kullanımda isterse, aynı backend'e bağlanarak sonra | — |
| 2026-11-19 | 2 | Uçtan uca iskelet: `python -m mimarlik.kroki <fotoğraf>` → DXF + JSON (`okuma`, `birlestirme`, `geometri`, `plan_cizimi`; mimara bağlı kurallar tek dosyada: `mimarlik/varsayimlar.py`; yeni KONTROL katmanı; 148 test). 02: DXF çıkıyor ama kapanmıyor (yatay 57, dikey 85 cm; `102→162` ve kenar bulma hataları), 18 ölçünün 7'si "emin". 01: dış kontur bulunamadı (bilinen), bulunan kenarlar KONTROL'de. Qwen ~3–4 dk/kroki. Çelişki kuralı tiresiz sayılarda da uygulanıyor (Y2 ≠ en yakın parça → emin değil) | Mimarın cevabıyla `varsayimlar.py`; sonra kenar bulma (01 konturu) |
| 2026-11-24 | 2 | Mimarın cevapları (`mimar-cevaplari`, main'e birleştirildi): S3 = B, X iptali, hata analizi (`deneyler/hata_analizi/`), kapı boşluğu kuralı (etiket → okunan sayı → ölçek): 01'in dış konturu ilk kez bulundu, 02'ninki geri geldi; kapı sayısı açıklığa bağlanır (02 bağlama 12/14). Gerçek değerlerle bile 01 (40/53 cm) ve 02 (48/60 cm) kapanmıyor; iç duvar kalınlığıyla açıklanamadı (`deneyler/kapi_kurali/RAPOR.md`). Sonra: katman çizgi kalınlıkları (B-10), DWG çıktısı ODA File Converter ile, AutoCAD 2017 uyumlu R2013 (B-11, B-12) | Mimara: kapanma farkı, dış duvar kalınlığı; ODA File Converter kurulup DWG AutoCAD'de denenecek |
| 2026-11-24 | 2 | **Mimar 01 ve 02'yi hatalı çizdiğini doğruladı:** toplamların tutmaması yorumdan değil çizimden. Kapanma kontrolü gerçek hatayı yakalamış. 01–02 "çizim hatalı" test vakası (`tests/test_cizim_hatali.py`): okuma/bağlama ölçümünde geçerli, geometri/kapanma/DXF doğruluğunda kullanılmıyor. Kapanmadan hesaplanan kenar artık farkı gizlemiyor: o eksen "doğrulanamadı", kenar KONTROL'de işaretli (02'nin yanlış bağlamayla "0/0 kapanan" örneği artık doğrulanamadı). 01–02'ye göre konmuş kurallar değerlendirildi (`deneyler/cizim_hatasi/RAPOR.md`): kapanmadan kenar hesaplama, ölçek, ölçekten kapı ve "120 sol" kuralı etkilenmiş olabilir; görsel eşikler etkilenmez | Mimardan 01–02'nin düzeltilmiş ölçüleri → "doğru hal" test verisi; sonra A grubu kurallar yeniden değerlendirilecek |
| 2026-11-24 | 2 | **DWG AutoCAD Web'de doğrulandı:** düzenlenebilir açılıyor, ölçü yazıları ve çizgi kalınlıkları görünüyor. İki sorun düzeltildi: Türkçe karakterler "?" çıkıyordu (txt.shx; metin DWG'de doğruydu) → bütün yazılar TrueType Arial; KONTROL notları planın üstüne yığılıyordu → planda numaralı daire, tam metin planın sağında liste. ODA File Converter `Program Files/ODA` altındaki en yeni sürümden kendiliğinden bulunuyor | Kullanıcı yeni DWG'leri AutoCAD Web'de tekrar kontrol edecek; sonra main'e birleştirme |
| 2026-11-24 | 1→2 | **Faz 1 bitti:** DWG AutoCAD'de açılıp düzenlendi (doğrulandı). Mimar AutoCAD Web'de baktı: **02: plan şekli mimar tarafından doğru bulundu (24.11.2026), 162→102 okuma hatası hariç. 01: şekil yanlış.** `mimar-cevaplari` main'e birleştirildi | 01'in şeklinin nerede yanlış olduğunu bulmak; mimardan 01–02'nin düzeltilmiş ölçüleri |
| 2026-11-24 | 2 | 01'in şekil analizi (`deneyler/sekil_01/`): sıra/yön doğru, "merdiven" değer atamadaki kaymadan. Ö1: Qwen koordinat dönüşümü doğru (sentetik test), kayma modelin belirsizliği. Ö2: değer atama ≤ 1 h, "emin" ≤ 0,5 h (yanlış atama 67 → 29 / 193; "emin" isabeti 01'de 1/1, 02'de 5/6–8/10). **Ölçekten kapı kaldırıldı** (krokiler ölçeksiz; ölçek kayınca 02'nin girinti ağzı kapı sanıldı); kanıtsız boşluk "kapı mı?" diye soruluyor. Y2'yi zayıf kapı ipucu saymak denendi, geri alındı. 02: onaylı 12 kenarlı şekil birebir korunuyor. 01: kapı kanıtı yok → kontursuz (eski kapı şans eseriymiş) | 01–02'de yeni ayar yok; Ö3, Ö4, Ö5 yeni test krokileriyle |
