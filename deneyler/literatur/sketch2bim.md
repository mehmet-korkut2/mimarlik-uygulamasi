# Literatür: Sketch2BIM (arXiv 2510.20838)

Tarih: 2026-11-28 · Kod yazılmadı. Kaynak: arXiv PDF'inin tam metni (v1, 16 Ekim 2025).

**Künye:** A. K. Ratul, S. Acharjee, S. Park, M. N. Sakib (University of Texas at Arlington, İnşaat Müh.),
"Sketch2BIM: A Multi-Agent Human-AI Collaborative Pipeline to Convert Hand-Drawn Floor Plans to 3D BIM".
arXiv kaydında dergi bilgisi: *Automation in Construction* 189 (2026) 106984 (yayıncı sayfasını okumadım).
Aynı ekibin önceki çalışması: "From sketch to BIM…", ASCE i3CE 2025 (yalnız dikdörtgen/üçgen planlar).

## 1. Ne yapıyor (kısa)

Tek bir el çizimi plan görselinden, **GPT-5** ile çalışan altı "ajan" üzerinden Revit'te 3D BIM modeli üretiyor.
İki faz var:

| Faz | Ajan | Görev |
|---|---|---|
| 1. Çizim → JSON | A1 Algılama | Görselden duvar (düz/açılı/eğri), kapı, pencere; JSON + "anlamsal özet" (topoloji, sayılar, oranlar) |
| | A2 İnsan geri bildirimi | Kullanıcının doğal dille düzeltmesini (Kabul / Reddet / Düzenle) JSON'a uygular |
| | A3 Şema / topoloji doğrulama | Şema, benzersiz kimlik, kapalı oda poligonları, açıklık duvarın üstünde mi, uçlar bağlı mı |
| | A4 Orkestra | Hafıza: görsel, özet, güncel JSON, geri bildirim geçmişi, kısıt ihlalleri |
| 2. JSON → Revit | A5 Betik üretici | JSON'dan RevitPythonShell betiği + statik denetim |
| | A6 Hata düzeltici | Çalışma hatalarına göre betiği onarır |

Döngü, **kullanıcı kabul edene ve doğrulama geçene kadar** sürer. Arayüz iki Streamlit uygulaması (doğal dille
düzeltme; JSON → Revit betiği). Birim feet, poligonlar saat yönünün tersine; dış duvarlar önce, iç duvarlar
soldan sağa / aşağıdan yukarı numaralanıyor (deterministik kimlik).

## 2. Ölçü okuma ve sayı–duvar eşleştirme (bizim için asıl soru)

**Makale bu iki konuyu neredeyse hiç işlemiyor.**

- Ölçü yazıları için tek cümle var: ölçüler ve etiketler (Door/D, Window/W, Room) "ölçek belirsizliği ve çizim
  kusurları yüzünden güvenilmez, **zayıf öncül**" sayılıyor.
- Ölçek: "piksel → feet ölçeği, yazılı ölçülerden **anizotropik en küçük kareler** (izotropiye doğru
  düzenlileştirilmiş) ile" hesaplanıyor. Yani geometri **pikselden** geliyor, sayılar yalnız ölçeği ayarlıyor.
  Bizim yaklaşımımızın tersi: biz krokiler ölçeksiz olduğu için geometriyi **sayılardan** kuruyoruz (CLAUDE.md,
  Faz 2, 2026-11-16).
- Sayıyı duvara bağlama yöntemi (yakınlık, tik, kılavuz çizgisi…) **anlatılmıyor**; GPT-5'in "zincirleme
  düşünme"sine bırakılmış görünüyor. Toplamların kapanmaması (bizim kapanma kontrolümüz) **hiç geçmiyor**.
- OCR / sayı okuma doğruluğu **ölçülmemiş**; ayrı bir OCR motoru yok.
- Kapı/pencere: etiket ya da kapı yayından. Etiket yoksa **varsayılan genişlik** (kapı ~3 ft = 91 cm, 2,5–3,5 ft;
  pencere ~4,5 ft). Açıklık duvar ucundan en az 0,75 ft (23 cm), iki açıklık arası en az 0,5 ft.
- Geometri adımları (eğim için Hough, RANSAC ile düz duvar, BIC/AIC ile yön kümeleri K ∈ [1, 8], birleştirme
  eşikleri: açı ≤ 1°, uç ≤ 3 ft, dik kayma ≤ 0,5 ft, örtüşme ≥ %60; kısa açılı parçaları ≥ 1,25 ft ise koruma;
  yarım-kenar düzlemsel graf ile odalar) **A1 ajanının görevi olarak** yazılmış. Bunların gerçekten kodla mı
  çalıştığı, yoksa GPT-5'e istemle mi tarif edildiği makalede **net değil** ve kod yayımlanmamış.

## 3. Sonuçlar

- **Veri:** 10 plan. Yazarların ekibi **Samsung Notes'ta tabletle (Samsung Tab S10+, kalem)** çizmiş; kâğıt
  fotoğrafı değil. Bilerek karışık seçilmiş: 6 Manhattan (dik açılı), 4 Manhattan-dışı (eğik, eğri duvar),
  3–7 oda.
- **Ölçütler:** öğe türüne göre (duvar, kapı, pencere) Macar algoritmasıyla eşleştirme sonrası kesinlik / duyarlılık /
  F1; eşleşen öğelerde boy hatası (RMSE) ve orta nokta kayması (MAE). Her kullanıcı düzeltmesinden sonra yeniden puan.
- **İlk geçiş (insan düzeltmesinden önce):** duvar duyarlılığı ≥ 0,845; kapılar F1 = 1,0; pencerede bir planda
  (P06) ΔF1 0,11. Duvar boy hatası ortalama RMSE **2,34 ft ≈ 71 cm** (0–8,35 ft), konum MAE 0,62 ft; kapı konum
  MAE 0,80 ft; pencere konum MAE 1,30 ft.
- **Sonuç:** 3–4 düzeltme turunda bütün ölçütler 1,0 / 0,00 ft. Bu, **insanın hataları düzeltmesinin** sonucu;
  otomatik doğruluk değil. P10 için doğal dille 7–8 düzeltme gerekmiş ("kapı 3'ü duvar 8'e taşı", "duvar 2'yi
  8 ft aşağı kaydır"…).
- **Faz 2:** üç BIM yüksek lisans öğrencisi Revit modellerini kontrol listesiyle onaylamış (nitel).
- **Kendi belirttikleri sınırlar:** yalnız 10 çizim; GPT-5 bazen halüsinasyon görüyor (10 çizimin 2'sinde ilk
  çıkarım yeniden çalıştırılmış, 1 betik onarılmış); model değişirse sonuç değişebilir; merdiven, çok kat, MEP yok.
- **Tutarsızlıklar:** metin P10 için "sekiz düzeltme" diyor, tabloda 7 adım var; Şekil 4 başlığı "plan 08",
  metin "plan 10". Özet "açıklıklar ilk geçişte yüksek güvenilirlikle" diyor; sonuçlarda pencerede düşüş var.

## 4. Veri ve kod erişilebilir mi?

- **Veri:** "Makul bir talep üzerine sorumlu yazardan" (makalede "Data availability"). Herkese açık değil.
- **Kod:** Makalede ve arXiv sayfasında depo bağlantısı yok.
- **Model:** GPT-5 (kapalı, bulut). Yeniden üretilebilirlik modelin sürümüne bağlı (yazarlar da söylüyor).
- Çizimler tabletle ve yazarlarca üretilmiş, ölçü sayıları ve kâğıt gürültüsü (defter çizgileri, fotoğraf) yok
  gibi görünüyor. Veri elimize geçse bile **bizim röleve krokilerimize benzemez.**

## 5. Bizim projeyle karşılaştırma

| Konu | Sketch2BIM | Biz |
|---|---|---|
| Girdi | Tabletle çizilmiş, kabaca orantılı | Kâğıt röleve krokisi fotoğrafı, ölçeksiz, defter çizgili |
| Geometri kaynağı | Piksel (+ sayılardan ölçek) | Yazılı sayılar (sıra/yön krokiden) |
| Sayı okuma | GPT-5 içinde, ölçülmemiş | Qwen3-VL 4B yerel, ölçülmüş (22–23/24) |
| Sayı–duvar bağlama | Anlatılmamış | Tik/temas/yakınlık + Y2, çelişkide soru; ölçülmüş |
| Tutarlılık | Şema/topoloji doğrulama | Kapanma kontrolü (gerçek çizim hatasını yakaladı) |
| Kanıtsız kapı | Varsayılan genişlikle konur | Konmaz, "kapı mı?" diye sorulur |
| İnsan | Doğal dille düzeltme turları | KONTROL katmanı + (Faz 4) düzeltme ekranı |
| Model / gizlilik | Bulut (GPT-5) | Yerel (müşteri verisi dışarı çıkmaz) |
| Değerlendirme | 10 yapay çizim, düzeltme sonrası | 2 gerçek kroki (+ mimarın doğrulaması) |

## 6. Bizim projeye neler alınabilir

1. **Değerlendirme yöntemi (en yararlısı).** Öğe türüne göre Macar eşleştirmesi + kesinlik / duyarlılık / F1, eşleşen
   öğelerde boy RMSE ve konum MAE. Bunu **kullanıcı düzeltmesi sayısıyla** birleştirmek, "taslak + hızlı düzeltme"
   hedefimizi ölçmenin doğrudan yolu. Mimarın "kroki başına ~1 saat" (B-14) cevabıyla birlikte ürün ölçütü olur:
   "kaç düzeltmede ve kaç dakikada doğru plan?". Yeni test krokileri gelince ölçüm altyapısı bu biçimde kurulabilir.
2. **Açık bir JSON şeması ve doğrulayıcı.** Şu an JSON raporumuz var ama şeması yazılı değil. Faz 4'teki düzeltme
   ekranı için "şema + deterministik doğrulama" (kapalı poligon, açıklık duvarın üstünde, uçlar bağlı, kimlikler
   benzersiz) yararlı. Doğrulamayı GPT ile değil kodla yapmak bizim için daha uygun (deterministik, yerel).
3. **Algılama ile üretimi ayırma.** Belirsizliğin tek bir denetlenebilir ara dosyada (JSON) toplanması, üretimin
   deterministik kalması. Bizim mimarimiz zaten böyle (rapor JSON → DXF/DWG); makale bu kararı destekliyor.
4. **Doğal dille düzeltme (Faz 4, belki).** "Kapı 3'ü duvar 8'e taşı" gibi komutlar. Bizde öncelik form tabanlı
   sayı düzeltme olmalı (mimar sayıyı değiştirir, plan yeniden kurulur). Doğal dil ancak yerel bir modelle ve
   sonradan düşünülebilir.
5. **Deterministik kimlik sırası** (dış duvarlar önce, sonra konum sırası): KONTROL notlarının ve düzeltme
   ekranının kararlı olması için. Bizde kenar numaraları kontur sırasından geliyor; düzeltmeden sonra
   numaraların kaymaması ayrıca kontrol edilmeli.
6. **Mimara sorulabilecek kural:** "Açıklık duvar ucundan en az 0,75 ft (23 cm)". 01'deki kapı 10 cm'lik
   duvarla köşeye çok yakın; bizim krokilerde bu sınır geçerli mi?

**Alınmaması gerekenler:**
- Ölçeği pikselden kurmak (röleve krokileri ölçeksiz; bizde ölçekten kapı bu yüzden kaldırıldı).
- Etiket yoksa varsayılan kapı genişliği koymak (kanıtsız kapı kararımızla çelişir).
- Bütün algılamayı tek bir bulut modele bırakmak (gizlilik, maliyet, yeniden üretilebilirlik).

## 7. Atıf verdiği ilgili çalışmalar

- Text2BIM (Du vd., arXiv:2408.08054): metinden BIM, çok ajanlı.
- BIMgent (Deng vd., arXiv:2506.07217): arayüz kullanan ajanla BIM.
- Raster-to-Vector (Liu vd., ICCV 2017): taranmış CAD benzeri planın vektöre çevrilmesi (dik açılı).
- Kim vd. 2021 (J. Comput. Civ. Eng. 35(2)): el çizimi planlarda stil aktarımıyla segmentasyon.
- 3DPlanNet (Park ve Kim, Electronics 2021), Jang vd. 2020 (IJGI), Barreiro vd. 2023 (MVA).

Makalede **ölçü yazılı el çizimi plan veri seti** geçmiyor. Bizim problemimiz için, yani ölçeksiz kâğıt krokide
yazılı sayıları okuyup duvara bağlamak için, bu makaleden hazır bir yöntem ya da veri çıkmıyor.
