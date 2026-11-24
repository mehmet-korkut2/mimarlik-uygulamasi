# Ö2: değer atama yerel ve sınırlı; kapı kanıtı

Tarih: 2026-11-24 · Kaynak: `../sekil_01/RAPOR.md` (H1: 01'in "merdiveni" değerlerin komşu bölgelere kaymasından).

## Kural

- Qwen'in değeri yalnız kutusu sayının bölgesine **≤ 1 h** ise atanır (eskiden merkez uzaklığı köşegenin %20'si
  ≈ 12,7 h). Uzaktaki değer zorla atanmaz, "yeri bulunamadı" kalır (Y2 / kullanıcı).
- **"Emin"** için kutu–bölge uzaklığı ≤ 0,5 h; bölgesi hiç bulunamayan (yalnız Y2'nin bağladığı) değer emin değil.

## Eşik seçimi (`olcum.py`: 14 kayıtlı Qwen-1 cevabı, 01–02, 193 değer; Qwen çağrılmaz)

| Kural | Doğru | Yanlış | Yeri bulunamadı | "Emin" (≤ 0,5 h) isabeti |
|---|---|---|---|---|
| Eski | 124 | 67 | 2 | — |
| **Sınırlı 1 h (ürün)** | 108 | **29** | 56 | 106/131 |
| Sınırlı 1,5 h | 110 | 38 | 45 | 102/129 |
| Sınırlı 3 h | 117 | 46 | 30 | 100/124 |

1 → 1,5 h: 2 doğru kazanılır, 9 yanlış eklenir. Kalan yakın-ama-yanlışların çoğu sınırla çözülemez: OCR okuma
hatası (102 → "162", 4 kez), Qwen'in kutuyu başka bir sayının üstüne koyması, sayı olmayan bölgeler (kılavuz).

## Uçtan uca (01–02, aynı Qwen kayıtları, 3 örnek) ve ortaya çıkan iki sorun

| | Önce | Ö2 |
|---|---|---|
| 01 "emin" isabeti | 2/4, 3/5, 3/5 | 1/1 (3 örnekte) |
| 02 "emin" isabeti | 5/6, 6/7, 3/3 | 5/6, 6/7, 8/10 |
| 01 bağlama | 4, 6, 6 /10 | 6, 6, 6 /10 |
| 02 bağlama | 12, 11, 9 /14 | 11, 10, 10 /14 |

1. **02: ölçekten kapı.** Daha az değer atanınca ilk geçişin ölçeği 0,38 → 0,48 cm/px kaydı; alttaki 40'lık
   girintinin ağzı "80'lik kapı" sanıldı, kontur 12 → 8 kenar (mimarın onayladığı şekil bozuldu).
   **Karar (kullanıcı): ölçekten kapı kaldırıldı.** Bir boşluk ancak yakınında K etiketi ya da kapı genişliğinde
   okunmuş bir sayı varsa kapı; kanıtsız boşluk KONTROL'de "boşluk: kapı mı?" diye sorulur
   (`varsayimlar.KAPI_KANIT_SART`). Sonuç: 02 üç örnekte de 12 kenar; yön dizisi ve parça geometrisi mimarın
   AutoCAD Web'de onayladığı DWG ile birebir aynı. 02'de 3 kanıtsız boşluk soruluyor.
2. **01: kapı şans eseriymiş.** Eski atama 10'un eğri kuyruğuna yanlışlıkla 90 yazıyordu, bu kapının yanına
   düşüyordu. Qwen'in 90 kutusu 8,4 h uzakta: kapının kanıtı yok.
   Denendi (kullanıcı kararı c): Y2'nin kapı genişliğinde bağladığı sayı zayıf ipucu. **Geri alındı:** 01'de
   3 örnekte de kapı bulunmadı; 02'nin 3. örneğinde Y2'nin "100"ü girinti ağzını kapı yaptı (12 → 8).
   **Sonuç (a): 01 bu okumayla kontursuz;** bulunan kenarlar KONTROL'de, boşluk "kapı mı?" diye soruluyor.
   01'in şekli artık "merdiven" değil, ama kapı kanıtı (doğru yerde okunan 90) olmadan kontur kurulmuyor.

01–02 üzerinde yeni ayar yapılmıyor; Ö3 (kılavuz çizgileri) ve Ö5 (kapı yanındaki kısa duvar) yeni test krokileri
gelene kadar bekliyor. Ö4 (kısa tik) de bekliyor.
