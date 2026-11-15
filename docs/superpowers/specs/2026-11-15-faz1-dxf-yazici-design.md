# Faz 1 — DXF Yazıcı Modülü ve Örnek Oda (Tasarım)

Tarih: 2026-11-15 · Durum: onaylandı (2026-11-15)

## Amaç ve neden

Koddan, AutoCAD'de düzgün açılan ve düzenlenebilen bir oda planı DXF'i üretmek ve DXF'in
birim/katman mantığını öğrenmek. Modül Faz 2'de yeniden kullanılacak: görüntü işlemeden
çıkan `(x1, y1, x2, y2)` çizgi listesi doğrudan bu modüle verilecek. Bu yüzden ne tek
kullanımlık bir script ne de ağır bir yapı; **küçük, fonksiyonlardan oluşan bir modül**.

## Hedefler

- Çizgi listesi + katman adı + birim alıp DXF yazan fonksiyonlar.
- Bu modülü kullanan ayrı bir demo: dikdörtgen oda, 1 kapı, 1 pencere, ölçüler → `output/`.
- pytest testleri: üretilen dosyayı ezdxf ile geri okuyup katman, birim ve duvar sayısını doğrular.

## Hedef dışı (bu fazda yok)

Görüntü işleme, kapı/pencere için blok (BLOCK) tanımları, tarama (hatch), oda adı yazıları,
DWG çıktısı, komut satırı argümanları, sınıf hiyerarşisi.

## Başarısızlık sayılır (çalışsa bile)

- Dosya açılıyor ama **ölçek yanlış** (ör. AutoCAD birimi mm sanıyor, oda 10 kat küçük).
- Çizgiler katmanlara dağılmamış ya da düzenlenemiyor (ör. tek bir blok/patlatılamaz nesne).

## Kısıtlar (kullanıcı kararları)

- DXF sürümü **R2010**. Birim **cm**.
- Dış duvar **25 cm**, iç duvar **10 cm** (bu fazda kullanılmıyor, sabit olarak tanımlı), kapı **90 cm**.
- Katman adları ASCII: `DUVAR`, `KAPI`, `PENCERE`, `OLCU`; **tek bir dosyada sabit**,
  mimardan cevap gelince tek satırdan değişecek.
- Sınıf yok, sadece fonksiyonlar.

## Yaklaşımlar

1. **Fonksiyon modülü + ayrı demo + testler (seçilen).** Faz 2'de yeniden kullanılabilir,
   test edilebilir, yine de küçük.
2. Tek script — öğrenmek için hızlı ama Faz 2'de yeniden yazılır. Reddedildi.
3. Sınıf tabanlı yapı (`Plan`, `Duvar`, `Kapi` nesneleri) — bu aşama için fazla. Kullanıcı reddetti.

## Dosya yapısı

```
mimarlik/
  __init__.py
  standartlar.py    # katman adları, renkleri, duvar/kapı ölçü sabitleri — TEK değişiklik noktası
  dxf_yazici.py     # fonksiyonlar
  demo_oda.py       # örnek oda; `python -m mimarlik.demo_oda` ile çalışır
tests/
  test_dxf_yazici.py
  test_demo_oda.py
pytest.ini          # pythonpath = .
```

## Modül arayüzü (`dxf_yazici.py`)

- `yeni_cizim(birim="cm")` → ezdxf belgesi. R2010; `$INSUNITS` birime göre (mm=4, cm=5, m=6),
  `$MEASUREMENT=1` (metrik); `standartlar.py`'deki tüm katmanları oluşturur; ölçü stilini ayarlar.
  Bilinmeyen birimde `ValueError`.
- `cizgi_ekle(doc, cizgiler, katman)` — `cizgiler`: `(x1, y1, x2, y2)` listesi. Tanımsız
  katmanda `ValueError` (yanlış yazılmış katman adı sessizce yeni katman açmasın diye).
- `yay_ekle(doc, merkez, yaricap, bas_aci, bit_aci, katman)` — kapı açılım yayı için.
- `olcu_ekle(doc, p1, p2, uzaklik, katman)` — doğrusal ölçü; AutoCAD'de gerçek ölçü nesnesi
  (düzenlenebilir, değeri geometriden otomatik okunur).
- `kaydet(doc, yol)` — klasör yoksa oluşturur, kaydeder.

## Örnek oda geometrisi (`demo_oda.py`)

Orijin dış köşede (0,0). Dış ölçü 450×350, iç ölçü 400×300 cm (duvar 25 cm).

- **Duvarlar (DUVAR):** dış ve iç dikdörtgen, kapı ve pencere boşluklarında kesik; boşlukların
  kenarlarında duvarı kapatan kısa "söve" çizgileri. Toplam **16 çizgi**
  (dış 6 parça + iç 6 parça + 4 söve).
- **Kapı (KAPI):** güney duvarında, 90 cm boşluk; içeri açılan kanat çizgisi (1) + 90° yay (1).
- **Pencere (PENCERE):** kuzey duvarında ortalı 120 cm; duvarın iki yüzünde + ortada cam
  çizgisi olmak üzere **3 paralel çizgi**.
- **Ölçüler (OLCU):** dış genişlik 450 ve dış derinlik 350 → **2 ölçü**.

Geometri saf bir fonksiyonda (`oda_geometrisi()` → katman → çizgi listesi sözlüğü) üretilir;
`oda_ciz(yol)` bunu modülle DXF'e yazar. Testler ikisini de kullanır.

## Testler

`test_dxf_yazici.py`
- Yazılan çizgiler geri okununca aynı sayıda ve aynı koordinatlarda, doğru katmanda.
- `$INSUNITS == 5` (cm), sürüm `AC1024` (R2010).
- Dört katman var; tanımsız katman ve bilinmeyen birim `ValueError` verir.
- `doc.audit()` hata bulmuyor.

`test_demo_oda.py`
- DUVAR'da 16 çizgi, KAPI'da 1 çizgi + 1 yay, PENCERE'de 3 çizgi, OLCU'da 2 ölçü.
- Dış sınır 450×350 cm.

## Elle doğrulama (Faz 1 "bitti" ölçütü)

`output/oda_demo.dxf` dosyasını **AutoCAD'de aç, bir duvarı ve bir ölçüyü düzenle.**
(Öğrenci lisansı alınana kadar dosyayı mimar açar.) Açarken kontrol: katman listesinde 4 katman,
`UNITS` cm gösteriyor, dış ölçü 450 yazıyor. Düzenleme: bir duvar çizgisi taşınabiliyor/uzatılabiliyor;
ölçünün bağlı olduğu nokta değişince değeri güncelleniyor.

## Varsayımlar (mimara sorulacaklar listesine ek)

Kullanıcının onayladıkları: cm, 25/10 cm duvar, 90 cm kapı, ASCII katman adları, R2010.
Benim kararlarım (mimardan cevap gelince değişebilir):
- Oda 400×300 cm iç ölçü; pencere 120 cm, kuzeyde ortalı; kapı içeri açılır.
- Pencere 3 çizgiyle gösterilir; kapı = kanat çizgisi + çeyrek yay.
- Katman renkleri: DUVAR beyaz (7), KAPI sarı (2), PENCERE camgöbeği (4), OLCU yeşil (3).
- Ölçü yazı yüksekliği 15 cm (1/50 baskıda 3 mm); ok yerine mimari "tick" işareti.
- Ölçüler dış ölçü olarak verilir.

## Açık sorular (mimara)

- **Pencere altındaki duvar planda kesik mi, sürekli mi çizilir?** Şimdilik kesik çiziliyor
  (pencere boşluğunda duvar çizgisi yok, yerine 3 pencere çizgisi + 2 söve). Cevap "sürekli"
  olursa DUVAR çizgi sayısı ve `test_demo_oda.py` beklentisi değişir.

## Uygulayıcıya bırakılan

Fonksiyon içi ayrıntılar, ölçü stilinin ezdxf'te tam nasıl tanımlanacağı, test dosyalarındaki
yardımcı fonksiyonlar.
