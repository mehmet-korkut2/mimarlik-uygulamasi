# Sayı–Duvar Eşleştirme Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Hedef:** Krokideki her okunan ölçü sayısını fotoğraftan bulunan bir kenar parçasına bağlayan ürün
modüllerini yazmak. Ana yolu (Y1), model karşılaştırmasını (Y2) ve taban çizgisini (Y3), üst sınır,
ara ve gerçekçi katmanlarda ölçmek.

**Mimari:**
- Ön işleme mavi mürekkebi ayırır.
- `kenar_bulma` mürekkepten yatay/dikey duvarları, açıklıkları, köşeleri ve ölçü işareti adaylarını
  çıkarır.
- `bolge_bulma` duvarlar silindikten sonra kalan mürekkebi sayı bölgelerine ayırır.
- `eslestirme` Qwen'in (değer, kutu) listesini bölgelere bire bir atar: mesafe + hane ipucu,
  Macar yöntemi. Sonra her bölgeyi parçaya bağlar: işaret → temas → en yakın.
- Ölçüm kodu `deneyler/eslestirme/` altında, ürün kodunu çağırır.

**Teknoloji:** Python, OpenCV 5.0, NumPy 2.5, SciPy 1.18.1 (`linear_sum_assignment`), pytest.
Y2 için Ollama + `qwen3-vl:4b-instruct`.

**Spec:** `docs/superpowers/specs/2026-11-17-sayi-duvar-eslestirme-design.md`

## Global Kısıtlar

- Koordinatlar her yerde orijinal fotoğraf pikseli (x, y; y aşağı).
- Ürün kodu (`mimarlik/`) yalnız `cv2`, `numpy`, `scipy` kullanır. Hem ana `.venv`'de hem
  `deneyler/.venv`'de çalışmalı.
- Ürün kodu gerçek cevaplara (`konumlar.py`, `gercek_eslestirme.py`) bağımlı olamaz. Tek istisna:
  bir kez kalibre edilmiş `HANE_KATSAYISI = 0.8`. Kaynağı: gerçek kutularda hane başına
  genişlik/yükseklik medyanı 0,814.
- Eşikler karakter yüksekliği `h`'nin katı olarak tanımlanır. `h`, `karakter_yuksekligi(maske)` ile
  ölçülür; sabit piksel yok. İstisnalar planda adıyla yazılı.
- Mimara bağlı bir anlam varsayılmaz. Açıklığa ya da çok parçalı bir kenarın parçasına bağlanan
  sayının anlamı `"bilinmiyor"`; tek parçalı kenara bağlananın anlamı `"uzunluk"`.
- **Görseller ve fotoğraflar commit edilmez.** `deneyler/**/gorseller/` `.gitignore`'da. Her
  commit'ten önce `git status --porcelain -uall` ile `.jpg`/`.png` olmadığı kontrol edilir.
- Commit mesajları Türkçe, sonunda `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **Testler:**
  - Ana testler: `.venv/Scripts/python -m pytest` (repo kökü, `pytest.ini`: `testpaths = tests`).
  - Deney testleri: `deneyler/.venv/Scripts/python -m pytest deneyler/eslestirme`.

## Review Focus

1. **Boş ya da mürekkepsiz görüntü:** `kenarlari_bul` boş `KenarSonucu` döner
   (`kenarlar == []`, `kontur_sirasi == []`); çökmez. `karakter_yuksekligi` bileşen yoksa `ValueError`
   verir, mesajında "mürekkep bulunamadı" geçer. Test: Görev 3 ve Görev 1.
2. **Qwen'in fazla değerleri ve uzak kutuları:** Bölgeden çok değer varsa fazlası
   `yeri_bulunamayan`'a gider. Mesafe üst sınırını aşan çift asla atanmaz. Test: Görev 6.
3. **Aynı değer birden çok kez** (02'nin dört `40`'ı): atama her birini ayrı bir bölgeye verir, aynı
   bölgeye iki değer vermez. Test: Görev 6.
4. **Ölçü işareti sayının içinden geçiyor** (`102`): İşaret bölgenin bir parçası olarak görünse de
   bölge `temas` ile doğru parçaya bağlanır. Test: Görev 7 (sentetik, işaret rakamla kesişiyor).
5. **Fotoğraf eğik çekilmiş:** Eksen açısı ±4° döndürülmüş görüntüde de bulunur; duvarlar yatay ya
   da dikey sınıflanır, eğik sayılmaz. Test: Görev 3.

---

## Ortak test görüntüsü (Görev 1'de yazılır, sonraki görevler kullanır)

`tests/sentetik.py`, beyaz zeminde mavi mürekkeple çizilmiş bir oda üretir:
- 1000×900 tuval, BGR `(255, 255, 255)`.
- Mürekkep BGR `(150, 70, 60)`, çizgi kalınlığı 4.

```
A(100,100) → B(700,100) → C(700,300) → D(800,300) → E(800,700) → F(100,700) → A
Sol kenar F→A: duvar (100,700)→(100,670) [30 px, kısa duvar], açıklık (100,670)→(100,540),
               duvar (100,540)→(100,100)
İşaret 1: üst kenarda (400,100)→(400,70); "180" putText sol-alt (360,60)
İşaret 2: sağ kenarda (800,500)→(830,500); "240" putText sol-alt (835,515)
İşaretsiz: "60" putText sol-alt (420,760) → en yakın kenar EF
İçinden işaret geçen: "102" putText sol-alt (230,770); işaret (300,700)→(300,775) rakamları keser
Yazı: FONT_HERSHEY_SIMPLEX, ölçek 1.2, kalınlık 2
```

İmza:

```python
def sentetik_kroki(aci_derece: float = 0.0) -> tuple[np.ndarray, dict]
```

Döner: (bgr, beklenen). `aci_derece` ≠ 0 ise görüntü merkez etrafında
`cv2.getRotationMatrix2D(merkez, aci_derece, 1.0)` ile döndürülür (beyaz dolgu). Beklenen
koordinatlar da aynı matrisle dönüştürülür.

`beklenen` sözlüğü:
- `kenar_sayisi: 6`
- `parca_sayisi: 8`
- `aciklik_sayisi: 1`
- `isaret_sayisi: 3` (102'deki dahil)
- `sayilar: {"180": kutu, "240": kutu, "60": kutu, "102": kutu}`: `cv2.getTextSize`'dan
  hesaplanmış piksel kutuları.
- `kenarlar: {"AB": (A, B), "BC": …, "FA_ust": ((100,540), (100,100)), "FA_alt": …}`

---

### Görev 1: Ön işlemeyi ürüne taşı + karakter yüksekliği + scipy

**Dosyalar:**
- Oluştur: `mimarlik/on_isleme.py` (içerik `deneyler/cizgi_silme/on_isleme.py`'den kopyalanır; deney
  dosyası olduğu gibi kalır, kayıt olarak)
- Oluştur: `tests/test_on_isleme.py` (deneydeki 5 test buraya kopyalanır, import `mimarlik.on_isleme`)
- Değiştir: `requirements.txt`: `scipy==1.18.1` satırı alfabetik yere eklenir

**Arayüzler:**
- Üretir:
  - `murekkep_maskesi(bgr: np.ndarray) -> np.ndarray`: bool, şekil (H, W).
  - `cizgileri_sil(bgr: np.ndarray, genislet: int = 1) -> np.ndarray`
  - `karakter_yuksekligi(maske: np.ndarray) -> float`

- [ ] **Adım 1:** `.venv/Scripts/pip install scipy==1.18.1`, sonra `requirements.txt`'ye ekle.
  Doğrula: `.venv/Scripts/python -c "import scipy; print(scipy.__version__)"` → `1.18.1`.
- [ ] **Adım 2: Testleri yaz.** Kopyalanan 5 test, ayrıca:

```python
def test_karakter_yuksekligi_sentetik_yaziya_yakin():
    bgr, _ = sentetik_kroki()
    h = karakter_yuksekligi(murekkep_maskesi(bgr))
    assert 18 <= h <= 40   # FONT_HERSHEY_SIMPLEX 1.2 ölçek ≈ 26 px

def test_karakter_yuksekligi_bos_maskede_hata():
    with pytest.raises(ValueError, match="mürekkep bulunamadı"):
        karakter_yuksekligi(np.zeros((50, 50), bool))
```

  `tests/sentetik.py`'yi bu görevde oluştur ("Ortak test görüntüsü" tanımı); sonraki görevler onu
  kullanır.
- [ ] **Adım 3:** `pytest tests/test_on_isleme.py -v` → karakter testleri FAIL (fonksiyon yok).
- [ ] **Adım 4:** `karakter_yuksekligi` yaz.
  - 8-bağlantılı bileşenler bulunur.
  - Yüksekliği görüntü yüksekliğinin %10'undan küçük ve alanı ≥ 20 piksel olanların yüksekliklerinin
    medyanı döner. Duvarlar ve büyük gürültü böylece dışarıda kalır.
  - Uygun bileşen yoksa `ValueError("mürekkep bulunamadı")`.
- [ ] **Adım 5:** `.venv/Scripts/python -m pytest -q` → hepsi PASS (43 eski + yeniler).
- [ ] **Adım 6:** Commit: `Ön işleme ürüne taşındı; karakter yüksekliği; scipy bağımlılığı`.

### Görev 2: Veri modeli ve geometri yardımcıları

**Dosyalar:**
- Oluştur: `mimarlik/eslestirme.py` (bu görevde yalnız dataclass'lar ve yardımcılar)
- Test: `tests/test_eslestirme.py`

**Arayüzler:**
- Üretir (spec bölüm 6; hepsi `@dataclass(frozen=True)`):

```python
Nokta = tuple[float, float]
Kutu = tuple[float, float, float, float]          # x1, y1, x2, y2

class Parca:  id: str; kenar_id: str; tur: str ("duvar"|"aciklik"); bas: Nokta; bit: Nokta
class Kenar:  id: str; yon: str ("yatay"|"dikey"); parcalar: tuple[Parca, ...]; konturda: bool
class IsaretAdayi: bas: Nokta; bit: Nokta        # bas: duvara değen uç
class Bolge:  kutu: Kutu; temas: Nokta | None  # bölge mürekkebinin bir duvara değdiği nokta
class Olcu:   deger: int; bolge: Kutu; parca_id: str | None; neden: str | None; anlam: str
class Kroki:  eksen_acisi_derece: float; kenarlar: tuple[Kenar, ...]; kontur_sirasi: tuple[str, ...]
              olculer: tuple[Olcu, ...]; yeri_bulunamayan: tuple[int, ...]; okunmamis_bolgeler: tuple[Kutu, ...]
class KenarSonucu:                     # kenar_bulma'nın çıktısı; burada, döngüsel import olmasın diye
              eksen_acisi_derece: float   # yatay duvarların atan2(dy, dx) açısı, (-45, 45]
              kenarlar: tuple[Kenar, ...]; kontur_sirasi: tuple[str, ...]; isaretler: tuple[IsaretAdayi, ...]

def kroki_sozluk(kroki: Kroki) -> dict                     # json.dumps edilebilir
def nokta_parca_mesafesi(p: Nokta, parca: Parca) -> float   # dik mesafe; izdüşüm dışarıdaysa uca mesafe
def parcayi_bul(p: Nokta, kenarlar, tolerans: float) -> Parca | None  # en yakın, mesafe ≤ tolerans
```

- [ ] **Adım 1: Testleri yaz:**
  - `nokta_parca_mesafesi((5, 3), Parca(.., bas=(0,0), bit=(10,0))) == 3`
  - `nokta_parca_mesafesi((13, 4), …(0,0)→(10,0)) == 5` (uç mesafesi)
  - `parcayi_bul` iki parçadan yakın olanı döner; tolerans dışında `None`.
  - `json.loads(json.dumps(kroki_sozluk(k)))["kenarlar"][0]["parcalar"][0]["tur"] == "duvar"`
- [ ] **Adım 2:** Çalıştır → FAIL.
- [ ] **Adım 3:** Uygula. `kroki_sozluk`: `dataclasses.asdict`; tuple'lar liste olur.
- [ ] **Adım 4:** `pytest tests/test_eslestirme.py -v` → PASS.
- [ ] **Adım 5:** Commit: `Eşleştirme veri modeli ve geometri yardımcıları`.

### Görev 3: Kenar bulma: çizgiler, eksen açısı, birleştirme

**Dosyalar:**
- Oluştur: `mimarlik/kenar_bulma.py`
- Test: `tests/test_kenar_bulma.py`

**Arayüzler:**
- Kullanır: `Parca`, `Kenar`, `IsaretAdayi`, `KenarSonucu` (Görev 2, `mimarlik/eslestirme.py`);
  `karakter_yuksekligi` (Görev 1).
- Üretir: `kenarlari_bul(maske: np.ndarray, h: float) -> KenarSonucu`

Bu görev, Görev 4'ün kullanacağı iç adımları yazar:
- `_cizgi_parcalari(maske, h)`: `cv2.HoughLinesP`, `minLineLength = h`, `maxLineGap = h / 4`.
- `_eksen_acisi(parcalar)`: uzunlukla ağırlıklı açı histogramı, mod 90° katlanmış.
- `_birlestir(parcalar, aci, h)`: doğrudaşlar; dik uzaklık ≤ h/3, aradaki boşluk ≤ h/2.

Bu görevin sonunda `kenarlari_bul` birleştirilmiş çizgileri **tek parçalı kenar** olarak döner.
Açıklık, işaret ayrımı ve kontur Görev 4'te.

- [ ] **Adım 1: Testleri yaz:**
  - `test_eksen_acisi_duz`: `sentetik_kroki(0)` → `abs(sonuc.eksen_acisi_derece) < 1`
  - `test_eksen_acisi_egik` (Review Focus 5): `sentetik_kroki(4)` → `abs(aci + 4) < 1`;
    `sentetik_kroki(-4)` → `abs(aci - 4) < 1`
  - `test_egik_fotografta_kenarlar_yatay_dikey`: `sentetik_kroki(4)` → her kenarın `yon` değeri
    `"yatay"` ya da `"dikey"`.
  - `test_birlestirme_ab_tek_cizgi`: AB kenarına (uçlar ≤ 10 px) yakın tam olarak bir kenar.
  - `test_bos_maske` (Review Focus 1): `kenarlari_bul(np.zeros((100,100), bool), 20)` →
    `kenarlar == ()`, `kontur_sirasi == ()`.
- [ ] **Adım 2:** Çalıştır → FAIL.
- [ ] **Adım 3:** Uygula.
- [ ] **Adım 4:** `pytest tests/test_kenar_bulma.py -v` → PASS.
- [ ] **Adım 5:** Commit: `Kenar bulma: çizgi parçaları, eksen açısı, doğrudaş birleştirme`.

### Görev 4: Kenar bulma: duvar/işaret ayrımı, açıklık, köşe, parça, kontur

**Dosyalar:**
- Değiştir: `mimarlik/kenar_bulma.py`
- Test: `tests/test_kenar_bulma.py`

**Arayüzler:** `kenarlari_bul` imzası değişmez; artık tam sonuç döner.

**Kurallar** (spec 5.2/4–7; eşikler `h` cinsinden):
- **Uca bağlı:** Bir ucu başka bir çizgiye ≤ h/2 olan çizgi.
- **Duvar:** Aşağıdakilerden biri:
  - iki ucu da bağlı, ya da
  - uzunluğu ≥ 3h, ya da
  - aynı doğruda açıklıkla ayrılmış bir duvarın devamı.
- **İşaret adayı:** Uzunluğu < 3h, tek ucu bir duvara bağlı, diğer ucu boşta. `IsaretAdayi.bas`
  duvara değen uçtur.
- **Açıklık:** Aynı doğrudaki iki duvar arasındaki boşluk, h ≤ boşluk ≤ 8h ise tek kenarın
  `aciklik` parçasıdır.
- **Köşe:** Yatay ve dikey uçların ≤ h/2 içinde buluşması. T-birleşim: bir çizginin ucunun başka bir
  çizginin ortasına ≤ h/2 değmesi. T-birleşimler parça sınırıdır.
- **Kimlikler:**
  - Kenar: kontur kenarları, en üst-sol köşeden başlayarak saat yönünde `K1…Kn`; iç duvarlar sonra
    `Kn+1…`.
  - Parça: kenar yönünde `Ki.1, Ki.2…`.
- **Kontur:** Köşe grafındaki alanı en büyük kapalı döngü. `konturda=True`.

- [ ] **Adım 1: Testleri yaz** (`sentetik_kroki(0)` ve `(4)` ile):
  - `len(kenarlar) == 6`
  - toplam parça `8`
  - `aciklik` sayısı `1`
  - FA kenarının parça türleri sırayla `["duvar", "aciklik", "duvar"]` ya da tersi (yön kontura bağlı)
  - 30 px'lik kısa duvar `duvar` sayılır, işaret değil
  - `len(isaretler) == 3`; her işaretin `bas` ucu bir duvara ≤ 5 px
  - `len(kontur_sirasi) == 6`; ilk kenar AB'ye karşılık gelir (en üst-sol köşe A).
- [ ] **Adım 2:** Çalıştır → FAIL.
- [ ] **Adım 3:** Uygula.
- [ ] **Adım 4:** `.venv/Scripts/python -m pytest -q` → PASS.
- [ ] **Adım 5:** Commit: `Kenar bulma: duvar/işaret ayrımı, açıklıklar, parçalar, dış kontur`.

### Görev 5: Sayı bölgeleri

**Dosyalar:**
- Oluştur: `mimarlik/bolge_bulma.py`
- Test: `tests/test_bolge_bulma.py`

**Arayüzler:**
- Kullanır: `KenarSonucu` (Görev 3–4), `Bolge` (Görev 2).
- Üretir:

```python
def bolge_olustur(maske: np.ndarray, kutu: Kutu, sonuc: KenarSonucu, h: float) -> Bolge
def bolgeleri_bul(maske: np.ndarray, sonuc: KenarSonucu, h: float) -> list[Bolge]
```

- `bolge_olustur`, verilen kutunun içindeki mürekkepten herhangi bir duvar parçasına (`tur == "duvar"`)
  ≤ h/4 olan ilk noktayı `temas` olarak koyar; yoksa `None`. Ölçüm, gerçek kutular için de bunu
  çağırır.
- `bolgeleri_bul`:
  1. Duvar parçaları maskeden `kalınlık + h/4` genişlikte silinir.
  2. İşaret adayları da silinir (sayıyla kesişen kısımları dahil; `102` durumu).
  3. 8-bağlantılı bileşenler bulunur; alanı < (h/4)² olanlar atılır.
  4. Bileşenler yatayda `0.6·h` yapı elemanıyla genişletilerek birleştirilir. Her grup için
     `bolge_olustur` çağrılır.
  5. Bölgeler (y, x)'e göre sıralanır.

- [ ] **Adım 1: Testleri yaz:**
  - `sentetik_kroki(0)` → her beklenen sayı kutusunun alanının ≥ %50'sini kapsayan tam bir bölge
    var (4 sayı).
  - "180"in rakamları tek bölge (bölünmedi).
  - Duvar boyunca bölge yok.
  - `bolge_olustur(maske, beklenen["sayilar"]["240"], …).temas` sağ duvara ≤ 5 px.
- [ ] **Adım 2:** Çalıştır → FAIL.
- [ ] **Adım 3:** Uygula.
- [ ] **Adım 4:** `pytest tests/test_bolge_bulma.py -v` → PASS.
- [ ] **Adım 5:** Commit: `Sayı bölgelerini bulma`.

### Görev 6: Değeri bölgeye atama (mesafe + hane ipucu)

**Dosyalar:**
- Değiştir: `mimarlik/eslestirme.py`
- Test: `tests/test_eslestirme.py`

**Arayüzler:**

```python
HANE_KATSAYISI = 0.8      # hane başına genişlik/yükseklik (gerçek kutular, medyan 0,814)
W_HANE = 0.05             # 1 hane farkı ≈ köşegenin %5'i kadar mesafe cezası (~120 px)
MESAFE_UST_SINIR = 0.2    # köşegen oranı; üstündeki çiftler yasak

def hane_tahmini(kutu: Kutu) -> float           # (genişlik / yükseklik) / HANE_KATSAYISI, yuvarlanmaz
def degerleri_ata(bolgeler: list[Bolge], ogeler: list[tuple[int, Kutu]],
                  boyut: tuple[int, int], w_hane: float = W_HANE
                  ) -> tuple[list[tuple[Bolge, int]], list[int], list[Bolge]]
    # döner: (atanmış (bölge, değer), yeri_bulunamayan değerler, okunmamış bölgeler)
```

- **Maliyet:** `‖merkez(bölge) − merkez(kutu)‖ / köşegen + w_hane · |hane_tahmini(bölge.kutu) − len(str(değer))|`.
  Mesafe > `MESAFE_UST_SINIR` ise maliyet `1e6`.
- `scipy.optimize.linear_sum_assignment` dikdörtgen matrisle çalıştırılır. Maliyeti `1e6` olan
  atamalar geri alınır: değer `yeri_bulunamayan`'a, bölge `okunmamış`'a gider.

- [ ] **Adım 1: Testleri yaz:**
  - `test_yakin_kutu_atanir`: iki bölge, iki öğe; her öğe kendi bölgesine.
  - `test_fazla_deger_yeri_bulunamayan` (Review Focus 2): 2 bölge, 3 öğe → `len(yeri_bulunamayan) == 1`.
  - `test_uzak_kutu_atanmaz` (Review Focus 2): öğe kutusu bölgeden köşegenin %30'u uzakta →
    atanmaz, `yeri_bulunamayan == [değer]`.
  - `test_ayni_deger_iki_bolgeye` (Review Focus 3): iki `40`, iki bölge → iki bölge de `40` alır,
    hiçbir bölge iki kez geçmez.
  - `test_hane_ipucu_karari_degistirir`:
    - Kurgu: dar bölge (2 hane genişliği, `hane_tahmini≈2`) ve geniş bölge (≈3); kutular ikisinin
      ortasında, eşit mesafede; değerler `40` ve `240`.
    - `w_hane=0.05` ile `240` → geniş bölge.
    - `w_hane=0` ile sonuç sadece mesafeye bağlı. Bu testte geniş bölgeye 1 px daha yakın olan `40`
      oraya gider.
- [ ] **Adım 2:** Çalıştır → FAIL.
- [ ] **Adım 3:** Uygula.
- [ ] **Adım 4:** `pytest tests/test_eslestirme.py -v` → PASS.
- [ ] **Adım 5:** Commit: `Değer atama: mesafe + hane ipucu, Macar yöntemi`.

### Görev 7: Bölgeyi parçaya bağlama ve `Kroki` kurma

**Dosyalar:**
- Değiştir: `mimarlik/eslestirme.py`
- Test: `tests/test_eslestirme.py`

**Arayüzler:**

```python
def bagla(bolge: Bolge, sonuc: KenarSonucu, h: float) -> tuple[Parca | None, str | None]
    # neden: "isaret" | "temas" | "en_yakin" | None
def anlam(parca: Parca, kenar: Kenar) -> str   # "uzunluk" | "bilinmiyor"
def kroki_kur(sonuc: KenarSonucu, atanmis: list[tuple[Bolge, int]], yeri_bulunamayan: list[int],
              okunmamis: list[Bolge], h: float) -> Kroki
```

**Sıra** (spec 5.5):
1. **`isaret`:** Bir işaret adayının `bit` ucu, bölge kutusunun h/2 genişletilmişinin içindeyse
   `parcayi_bul(isaret.bas, …, h/2)`.
2. **`temas`:** `bolge.temas` varsa `parcayi_bul(temas, …, h/2)`.
3. **`en_yakin`:** Bölge merkezine `nokta_parca_mesafesi` en küçük parça, mesafe ≤ 6h. Yoksa
   `(None, None)`.

Not: Bütün dataclass'lar (`KenarSonucu` dahil) `eslestirme.py`'de. `kenar_bulma` ve `bolge_bulma`
`eslestirme`'yi import eder, tersi değil. Testler `kenarlari_bul`'u test dosyasında çağırır.

- [ ] **Adım 1: Testleri yaz** (`sentetik_kroki(0)` → `kenarlari_bul` → `bolge_olustur`):
  - "180" → AB parçası, `neden == "isaret"`.
  - "240" → DE parçası, `neden == "isaret"`.
  - "60" → EF parçası, `neden == "en_yakin"`.
  - "102" (Review Focus 4) → EF parçası, `neden` `"temas"` ya da `"isaret"`; `None` değil.
  - `anlam`:
    - FA'nın açıklık parçası → `"bilinmiyor"`
    - FA'nın duvar parçası → `"bilinmiyor"` (çok parçalı kenar)
    - AB → `"uzunluk"`
  - `kroki_kur`: `len(olculer) == len(atanmis)`, `yeri_bulunamayan` aynen geçer, sonuç
    `kroki_sozluk` ile JSON'a çevrilir.
- [ ] **Adım 2:** Çalıştır → FAIL.
- [ ] **Adım 3:** Uygula.
- [ ] **Adım 4:** `.venv/Scripts/python -m pytest -q` → hepsi PASS.
- [ ] **Adım 5:** Commit: `Bağlama (işaret, temas, en yakın) ve Kroki çıktısı`.

### Görev 8: Ölçüm puanlama kütüphanesi

**Dosyalar:**
- Oluştur: `deneyler/eslestirme/puanlama_eslestirme.py`
- Test: `deneyler/eslestirme/test_puanlama_eslestirme.py`

**Arayüzler:**

```python
def gercek_kenarlar(kod: str) -> KenarSonucu   # gercek_eslestirme.KENARLAR/KONTUR -> dataclass;
                                                # isaretler=() ; yon: |dx|>|dy| ise "yatay"
def gercek_ciftler(kod: str) -> list[tuple[int, str]]          # (değer, gerçek parça id), 24 toplam
def mimara_bagli_ciftler(kod: str) -> list[tuple[int, str]]     # ANLAM_BILINMIYOR ∪ KAPSAM_BELIRSIZ
def parcalari_eslestir(bulunan: KenarSonucu, gercek: KenarSonucu, tol: float = 25) -> dict[str, str]
    # bulunan parça id -> gerçek parça id; iki uç da ≤ tol (yön fark etmez); bire bir, en yakın önce
def kenar_puani(bulunan, gercek, tol=25) -> dict
    # {"bulunan", "kaciran", "fazla", "tur_dogru", "kontur_dogru": bool}
def ciftleri_cevir(ciftler, eslesme: dict[str, str]) -> list[tuple[int, str]]
    # bulunan id'leri gerçek id'ye; eşleşmeyen "F:<id>" olur
def eslestirme_puani(tahmin, gercek, kenar_duzeyi=False, haric=()) -> int
    # Counter kesişimi; kenar_duzeyi'nde "K3.2" -> "K3"; haric çiftler iki taraftan da bir kez çıkarılır
def bolge_puani(bolgeler: list[Bolge], gercek_kutular: list[Kutu]) -> dict
    # {"bulunan", "yazi_olmayan", "bolunmus", "birlesmis"}; bulunan: kutu alanının ≥ %50'si tek bölgede
```

- [ ] **Adım 1: Testleri yaz:**
  - `len(gercek_ciftler("01")) == 10`, `len(gercek_ciftler("02")) == 14`
  - `len(mimara_bagli_ciftler("02")) == 4`
  - `parcalari_eslestir(gercek, gercek)` kimlik eşlemesi döner
  - Bir parça 30 px kaydırılınca o parça eşleşmez
  - `eslestirme_puani([(40,"K3.1"),(40,"K3.1")], [(40,"K3.1")]) == 1`
  - `kenar_duzeyi=True` ile `(300,"K1.1")` ↔ `(300,"K1.2")` → 1
  - `haric` ile mimara bağlı çiftler düşünce payda da düşer
- [ ] **Adım 2:** `deneyler/.venv/Scripts/python -m pytest deneyler/eslestirme -v` → FAIL.
- [ ] **Adım 3:** Uygula. `mimarlik` paketine erişim: dosya başında
  `sys.path.insert(0, str(REPO))`.
- [ ] **Adım 4:** Aynı komut → PASS.
- [ ] **Adım 5:** Commit: `Eşleştirme ölçümü: puanlama kütüphanesi`.

### Görev 9: Ölçüm betiği: Ü, A, G katmanları ve Y3

**Dosyalar:**
- Oluştur: `deneyler/eslestirme/olcum.py`, sonuç `sonuclar/olcum.json`, `olcumler.md`
- Oluştur: görseller `gorseller/{kenarlar,bolgeler,bag_U,bag_A,bag_G<n>_hane,bag_G<n>_ipucusuz}_{kod}.jpg`

**Akış** (her kroki için):
1. **Hazırlık:** `bgr → maske → h`; `bulunan = kenarlari_bul(maske, h)`; `gercek = gercek_kenarlar(kod)`;
   `kenar_puani` hesaplanır.
2. **Ü:** Her gerçek kutu → `bolge_olustur(maske, kutu, gercek, h)` → `bagla(…, gercek, h)` →
   (gerçek değer, parça). Katı/gevşek puan, mimara bağlılar dahil/hariç, neden dağılımı.
3. **A:** Aynısı, `bulunan` ile. Parça id'leri `ciftleri_cevir` ile gerçek kimliğe çevrilir.
4. **G:**
   - `bolgeler = bolgeleri_bul(maske, bulunan, h)`; `bolge_puani` hesaplanır.
   - `qwen_konum.json`'un 3 çalıştırmasının her biri için:
     - öğeler `piksele_cevir` ile pikselleştirilir
       (`deneyler/konum_deneyi/konum_istem.py`);
     - `degerleri_ata` hem `W_HANE` hem `0` ile çalıştırılır;
     - doğru değer alan bölge sayısı: bölgenin örtüştüğü gerçek kutunun değeriyle karşılaştırılır;
     - `bagla` → puanlar.
5. **Y3:** Aynı 3 çalıştırma. Kutu merkezine en yakın parça, `gercek` ve `bulunan` için ayrı.
6. **Süre:** `time.perf_counter` ile bulma + atama + bağlama, kroki başına.
7. **Çıktı:** `olcumler.md`'de her katman için tek tablo. Ayrıca `y2.json` varsa Y2 tablosu
   (Görev 10).

Görseller: doğru yeşil, yanlış kırmızı, mimara bağlı turuncu; etikette değer → parça ve neden.

- [ ] **Adım 1:** Yaz ve çalıştır: `PYTHONIOENCODING=utf-8 deneyler/.venv/Scripts/python deneyler/eslestirme/olcum.py`.
  Beklenen: `olcumler.md` ve `sonuclar/olcum.json` yazıldı, hata yok.
- [ ] **Adım 2:** Görselleri aç ve kontrol et. Kenar bulma görselinde gerçek ve bulunan parçalar üst
  üste. Eşikler gerekirse **h cinsinden** ayarlanır; her değişiklik gerekçesiyle raporda yazılır
  (spec anti-hedefi).
- [ ] **Adım 3:** `git status --porcelain -uall` → görsel yok. Commit: `Eşleştirme ölçümü: Ü/A/G katmanları ve taban çizgisi`.

### Görev 10: Y2: numaralı parçaları Qwen'e sormak

**Dosyalar:**
- Oluştur: `deneyler/eslestirme/calistir_y2.py` → `sonuclar/y2.json`, görsel `gorseller/y2_girdi_{kod}.jpg`

**Ayrıntılar:**
- **Girdi görseli:** `cizgileri_sil` çıktısının üstüne gerçek parçalar ince kırmızı çizgiyle çizilir.
  Etiketler `P1…Pn`, gerçek parça sırasıyla; parça ortasında beyaz zeminli 22 pt etiket.
  Eşleme `{"P1": "K1.1", …}` json'a yazılır.
- **İstem (sabit):**

  > "Bu, elle çizilmiş bir mimari kroki. Duvar parçaları kırmızı çizgilerle P1, P2… diye
  > numaralandı. Her parçanın yanına el yazısıyla yazılmış ölçü sayılarını (cm) bul. Sadece bir JSON
  > nesnesi döndür, başka bir şey yazma. Biçim: {"P1": [180], "P2": []}. Bir parçanın sayısı yoksa
  > boş liste yaz."

- **Ayarlar:** `qwen3-vl:4b-instruct`, `num_ctx` 8192, kroki başına 3 çalıştırma, aradaki
  çalıştırmalarda `keep_alive=0`. Ayrıştırma: ilk `{…}` json; bozuksa çalıştırma 0 puan, ham cevap
  saklanır.
- **Çıktı:** her çalıştırma için (değer, gerçek parça id) çiftleri ve süre.

- [ ] **Adım 1:** Ayrıştırma fonksiyonu için test yaz: `y2_ciftleri(metin, eslem) -> list[tuple[int,str]]`
  (geçerli json, kod bloğu içinde json, bozuk json → `[]`). FAIL → uygula → PASS.
- [ ] **Adım 2:** Arka planda çalıştır: `PYTHONIOENCODING=utf-8 deneyler/.venv/Scripts/python deneyler/eslestirme/calistir_y2.py`
  (~6–8 dk). Sonra `olcum.py`'yi yeniden çalıştır; Y2 tablosu `olcumler.md`'de görünür.
- [ ] **Adım 3:** `git status` kontrolü. Commit: `Eşleştirme ölçümü: Y2 (numaralı parçaları Qwen'e sorma)`.

### Görev 11: Rapor, günlük, push

**Dosyalar:**
- Oluştur: `deneyler/eslestirme/RAPOR.md`
- Değiştir: `CLAUDE.md` ilerleme günlüğü (bir satır)

**Rapor bölümleri:**
- **Kısa cevap:** Hangi yaklaşım, kaç/24 katı ve gevşek.
- **Kenar bulma puanı.**
- **Katman tablosu:** Ü/A/G/Y2/Y3; dahil ve hariç mimara bağlı.
- **Hata nereden geliyor:** Ü→A farkı kenar bulmaya, A→G farkı bölge ve değer atamaya ait.
- **Hane ipucunun etkisi.**
- **Neden dağılımı:** işaret / temas / en yakın, her birinin doğruluğu.
- **Ayarlanan eşikler ve gerekçeleri.**
- **Mimara sorular M1–M5** (spec bölüm 3).
- **Sonraki adım önerisi.**

- [ ] **Adım 1:** Raporu yaz; `olcumler.md`'deki sayılarla tutarlı olduğunu kontrol et.
- [ ] **Adım 2:** Tüm testler:
  - `.venv/Scripts/python -m pytest -q`
  - `deneyler/.venv/Scripts/python -m pytest deneyler -q`

  İkisi de PASS.
- [ ] **Adım 3:** `git status --porcelain -uall` → görsel/fotoğraf yok. Commit + `git push`.
