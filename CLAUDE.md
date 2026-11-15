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
- Alan danışmanlarım: **abim (mimar)** ve **yengem (iç mimar)**. Mimari kurallar, çizim standartları ve gerçek iş akışı konusunda onlara soruyorum.

## 2. Proje özeti

Mimarların ve iç mimarların çizim işini otomatikleştiren bir uygulama.

**Seçilen ilk ürün:** Mimarın **elle çizdiği planı** (kâğıt, fotoğraf ya da tarama) alıp **AutoCAD'de açılıp düzenlenebilen bir dosyaya** dönüştürmek.

**Uzun vadeli vizyon:** İç mimarın tüm işini kapsamak (konut, diş kliniği, okul, restoran, kafe vb.), modül modül.

### Planlanan sıra
1. **El çizimi → AutoCAD** (çekirdek ürün)
2. **AutoCAD çizimine mobilya/obje ekleme** (6 kişilik masa, yatak, kanepe vb. 2D bloklar). Bu, abimin fikri.
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
- [ ] Abim ve yengemle görüşme: elle çizilmiş **gerçek örnek planlar** topla (en az 10–20 adet, farklı çizim stilleri).
- [ ] Onlardan şunları öğren: duvar kalınlıkları, kapı/pencere sembolleri, ölçek alışkanlıkları (1/50, 1/100), AutoCAD'de katman (layer) düzenleri.
- [ ] Her örnek plan için mümkünse **aynı planın AutoCAD versiyonunu** da iste (doğruluğu ölçmek için referans olur).
- [ ] Python ortamı kur: `venv`, `opencv-python`, `ezdxf`, `numpy`, `pytest`.
- [ ] GitHub reposunu aç, bu dosyayı `CLAUDE.md` olarak ekle.

**Bitti sayılır:** Klasörde örnek planlar var, ortam çalışıyor, repo açık.

### Faz 1 — DXF'i tanımak (1 hafta)
- [ ] `ezdxf` ile koddan basit bir DXF üret: dikdörtgen oda, duvar çizgileri, katmanlar (DUVAR, KAPI, PENCERE, ÖLÇÜ).
- [ ] Dosyayı AutoCAD'de (veya ücretsiz bir DWG/DXF görüntüleyicide) açıp düzenlenebildiğini doğrula.
- [ ] Birim ve ölçek mantığını öğren (DXF'te birim = mm/cm/m).

**Bitti sayılır:** Koddan ürettiğim bir oda planı AutoCAD'de düzgün açılıyor ve düzenlenebiliyor.

### Faz 2 — Temiz çizimden vektöre (2–4 hafta)
Önce **kolay girdiyle** başla: cetvelle, kareli kâğıda, düz çekilmiş net çizim.
- [ ] Görüntü ön işleme: gri tonlama, eşikleme (threshold), gürültü temizleme, perspektif düzeltme (fotoğraf yamuk çekildiyse).
- [ ] Çizgi tespiti: Hough Line Transform / kontur bulma.
- [ ] Çizgileri sadeleştirme: yakın çizgileri birleştirme, açıları 0°/90°'ye yakalama (snap), köşeleri birleştirme.
- [ ] Ölçek kalibrasyonu: kullanıcı bilinen bir ölçüyü girsin (örn. "bu duvar 400 cm") ve tüm çizim buna göre ölçeklensin.
- [ ] Sonucu DXF'e yaz.

**Bitti sayılır:** Temiz bir el çiziminin fotoğrafından, duvarları doğru yerde ve doğru ölçekte olan bir DXF çıkıyor.

### Faz 3 — Anlamlandırma (4–8 hafta, en zor kısım)
- [ ] Duvar ile diğer çizgileri ayırt et (çift çizgi = duvar gibi kurallar).
- [ ] Kapı ve pencere sembollerini tanı (önce kural tabanlı, sonra gerekirse makine öğrenmesi).
- [ ] OCR ile ölçü yazılarını ve oda adlarını oku, doğru çizgiyle eşleştir.
- [ ] Her öğeyi doğru katmana yerleştir.
- [ ] Doğruluk ölçümü: Faz 0'daki referans AutoCAD dosyalarıyla karşılaştır.

**Bitti sayılır:** Çıktı DXF'te duvar, kapı ve pencere ayrı katmanlarda; abim dosyayı açınca "bunu düzeltmek sıfırdan çizmekten hızlı" diyor.

### Faz 4 — Kullanılabilir prototip (2–3 hafta)
- [ ] FastAPI ile backend: görsel yükle → DXF indir.
- [ ] Basit web arayüzü: yükleme, önizleme, ölçek girme, indirme.
- [ ] Abim ve yengeme gerçek işlerinde denet, geri bildirim topla.

### Faz 5 — Mobilya/obje ekleme modülü
- [ ] 2D mobilya blok kütüphanesi (masa, yatak, kanepe, dolap vb.); yengemden standart ölçüler al.
- [ ] Mevcut bir DXF'i oku, odaları tespit et.
- [ ] Komutla ekleme: "salona 6 kişilik masa ekle" → doğru bloğu uygun konuma yerleştir.
- [ ] Sonra: yazılı komutları anlamak için LLM entegrasyonu.

### Faz 6 — 3D (uzun vade)
- [ ] 2D plandan duvarları yükselterek basit 3D model (extrude).
- [ ] Format seçenekleri: DXF 3D, IFC, ya da SketchUp/Blender'a aktarım. Bu fazda ayrıca araştırılacak.

## 5. Riskler ve dürüst değerlendirme

**Artılar**
- Gerçek bir problem: elle çizilen planı AutoCAD'e aktarmak zaman alan, sıkıcı bir iş.
- Alan uzmanlarına (abim, yengem) doğrudan erişimim var; çoğu kişide bu yok.
- Modüler yapı: her faz kendi başına gösterilebilir bir çıktı. CV'ye ve portfolyoya yazılabilir.

**Eksiler / riskler**
- **El çizimi tanıma çok zor.** Çizim stilleri, eğri çizgiler ve kötü fotoğraflar doğruluğu çok düşürür. Çözüm: girdiyi kısıtla (kareli kâğıt, net fotoğraf, ölçek referansı) ve "%100 otomatik" yerine **"kullanıcının hızlıca düzelttiği yarı otomatik"** bir ürün hedefle.
- **Makine öğrenmesi için veri lazım.** Faz 3'te kural tabanlı yöntem yetmezse etiketli veri gerekecek; toplaması zaman alır.
- **Rakip çözümler var** (raster→vektör dönüştürücüler, AutoCAD'in kendi araçları). Farkımız mimari anlamlandırma (duvar/kapı/katman) olmalı. Faz 2'den önce rakipleri kısaca incele.
- **Kapsam şişmesi:** Faz 3 bitmeden 3D'ye veya mobil uygulamaya geçme.
- **Zaman:** Okul, bitirme projesi ve staj başvurularıyla paralel yürüyor; fazların süreleri tahmini.

## 6. Claude'a notlar

- Şu an hangi fazda olduğumu her oturumun başında söyleyeceğim. Söylemezsem sor.
- Kodu küçük, test edilebilir parçalar halinde yaz; her parça için nasıl test edeceğimi göster.
- Kütüphane veya yaklaşım seçerken alternatifleri kısaca karşılaştır.
- Mimari bir varsayım yapman gerektiğinde (duvar kalınlığı, sembol vb.) bunu belirt; abime/yengeme danışmam gereken soruları listele.

## 7. İlerleme günlüğü

| Tarih | Faz | Ne yapıldı | Sonraki adım |
|---|---|---|---|
| 2026-11-14 | 0 | Yol haritası hazırlandı | Abim ve yengemden örnek el çizimleri toplamak |
| 2026-11-15 | 0 | Claude Code + Superpowers kuruldu, proje klasörü ve CLAUDE.md oluşturuldu | Git reposu, Python ortamı |
| 2026-11-15 | 1 | DXF yazıcı modülü (`mimarlik/dxf_yazici.py`) + örnek oda demosu, 27 test geçiyor | `output/oda_demo.dxf` AutoCAD'de açılıp bir duvar ve bir ölçü düzenlenecek (mimar); açık sorular mimara |
