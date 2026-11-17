# Defter Çizgisi Silme Deneyi Raporu

Tarih: 2026-11-17 · Ham çıktı: `sonuclar/qwen_silinmis.json` · Kontrol görselleri: `gorseller/silinmis_*.jpg`
(**fotoğraf sayılır, `.gitignore`'da**)

## Sonuç

**Küçük bir iyileşme var; `102` → `162` düzelmedi.** Defter çizgileri renkle silinince Qwen3-VL 4B
24 sayıdan **23 / 23 / 23** okudu (dün aynı istemle 23 / 22 / 22). Fark tek bir sayı: dört `40`'tan
biri artık her çalıştırmada bulunuyor. Fazla sayı yine 1 (`162`). Üç çalıştırma birebir aynı sonucu
verdi; dün `40`'ın okunup okunmaması değişiyordu.

Ön işleme kroki başına ~0,05 s, toplam süre değişmedi (~56–59 s).

Kullanıcı kararıyla OCR iyileştirmesi burada bırakılıyor. Kalan hataları kullanıcı onayı ve duvar toplamı
kontrolü yakalayacak. **Öneri:** Ucuz ve zararsız olduğu için ön işleme ürüne alınabilir. Ancak iyileşme tek
bir sayıya dayanıyor; kesin bir kazanç değil, bir işaret.

## Yöntem

- **Ön işleme** (`on_isleme.py`):
  - OpenCV ile fotoğrafı renk tonu, doygunluk ve parlaklık (HSV) uzayına çevir.
  - Mavi mürekkebi tut: ton 95–135, doygunluk ≥ 25, parlaklık ≥ 40. Maskeyi 1 px genişlet, kalan her
    pikseli beyaz yap.
  - Ölçülen değerler:
    - Mürekkep: ton ~113. Doygunluk koyu yerlerde ~85–125, soluk yerlerde 26–70.
    - Defter çizgisi ve kâğıt: ton ~22–30 (sarımsı), doygunluk ~15–40.

    Yani ayrımı asıl renk tonu yapıyor.
  - İlk denemede doygunluk eşiği 55'ti: soluk sayılar kırıldı (`200` "2..." oldu). Eşik 25'e indirildi.
- **Tek değişken ön işleme:** İstem (`ocr_karsilastirma/istem.py`), model (`qwen3-vl:4b-instruct`),
  `num_ctx` 8192 ve her çalıştırmadan sonra modeli boşaltma dünküyle birebir aynı. Modele kayıpsız PNG
  verildi.
- **Kalan kusur:** Krokinin dışındaki koyu lacivert kumaş/ayraç parçaları maskede kalıyor. Sayılardan
  uzak oldukları için bu deneyi etkilemedi.

## Karşılaştırma

| | 01 doğru /10 | 02 doğru /14 | Toplam /24 | Fazla | Kaçırılan (02) | Süre / kroki |
|---|---|---|---|---|---|---|
| Ham fotoğraf (dün, GPU) | 10 / 10 / 10 | 13 / 12 / 12 | 23 / 22 / 22 | 1 / 1 / 1 (`162`) | `102`; 2 kez `40` | ~60 s |
| **Çizgiler silinmiş** | 10 / 10 / 10 | 13 / 13 / 13 | **23 / 23 / 23** | 1 / 1 / 1 (`162`) | `102` | ~56–59 s |

## `102` → `162`: hipotez düzeltmesi

Önceki raporda (`../bul_kes_okut/RAPOR.md`) bu hatayı `0`'ın ortasından geçen **defter çizgisine**
bağlamıştım. Bu hipotez büyük olasılıkla yanlış. Defter çizgileri silindiği halde `0`'ın içindeki dikey
çizgi silinmiş görselde **kaldı**, yani o çizgi mavi mürekkep. En olası açıklama: duvardan inen ölçü
işareti (tick) sayının içinden geçiyor ve `0`'ı "6"ya benzetiyor. Bu hatayı ön işleme çözmez. Duvar
toplamı kontrolü ve kullanıcı onayı yakalamalı.

## Sınırlar

- 2 kroki, 24 sayı. İyileşme tek bir sayıdan ibaret.
- Renk eşikleri bu iki krokiye göre ayarlandı. Kırmızı ölçülü (05, 07) ya da farklı mürekkepli krokilerde
  renk aralığı yeniden ayarlanmalı.

## Çalıştırma (repo kökünden)

```bash
P=deneyler/.venv/Scripts/python
$P -m pytest deneyler/cizgi_silme        # ön işleme testleri
$P deneyler/cizgi_silme/calistir.py      # -> sonuclar/qwen_silinmis.json + gorseller/silinmis_*.jpg
```
