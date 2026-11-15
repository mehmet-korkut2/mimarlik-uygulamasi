# Faz 1 — DXF Yazıcı Modülü Uygulama Planı

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `(x1, y1, x2, y2)` çizgi listesini katman ve birimle DXF'e yazan küçük bir fonksiyon modülü ve onu kullanan örnek oda demosu.

**Architecture:** `mimarlik/standartlar.py` tüm sabitleri (katman adları, renkler, ölçüler) tutar; `mimarlik/dxf_yazici.py` ezdxf üzerine ince fonksiyonlar sunar; `mimarlik/demo_oda.py` geometriyi saf bir fonksiyonla hesaplayıp modülle yazar. Testler üretilen dosyayı ezdxf ile geri okur.

**Tech Stack:** Python 3.13, ezdxf 1.4.5, numpy 2.5.4 (sadece testte), pytest 9.2.0.

**Spec:** `docs/superpowers/specs/2026-11-15-faz1-dxf-yazici-design.md`

## Global Constraints

- DXF sürümü R2010 (`ezdxf.new("R2010", setup=False)`, `doc.dxfversion == "AC1024"`).
- Varsayılan birim cm → `$INSUNITS = 5`; desteklenen birimler `{"mm": 4, "cm": 5, "m": 6}`; `$MEASUREMENT = 1`.
- Katman adları ASCII: `DUVAR`, `KAPI`, `PENCERE`, `OLCU` — yalnızca `standartlar.py`'de tanımlı, başka hiçbir dosyada string olarak yazılmaz.
- Sınıf yok; yalnızca modül düzeyinde fonksiyonlar.
- Tüm uzunluklar cm: dış duvar 25, iç duvar 10, kapı 90, pencere 120.
- Komutlar repo kökünden: `.venv/Scripts/python -m pytest ...` (Git Bash).
- Çıktı `output/` altına (git'e girmez).

## Review Focus

1. **numpy sayıları** (Faz 2'de OpenCV `np.int32`/`np.float64` döndürür) `cizgi_ekle`'ye verilince sorunsuz yazılmalı → Task 2 testi.
2. **Sıfır uzunluklu çizgi** (`x1==x2 and y1==y2`, gürültüden gelir) → `ValueError` (benim kararım: sessizce atlamak hatayı gizler; filtreleme Faz 2'nin işi) → Task 2 testi.
3. **Yanlış biçimli çizgi** (4 değil 3 eleman) → anlaşılır mesajlı `ValueError` → Task 2 testi.
4. **Büyük/küçük harf hatası** (`"duvar"`) → `ValueError`, yeni katman açmamalı → Task 2 testi.
5. **Var olmayan iç içe klasöre kaydetme** (`output/a/b/x.dxf`) → klasörler oluşturulur → Task 2 testi.

---

### Task 1: İskelet, standartlar ve `yeni_cizim`

**Files:**
- Create: `pytest.ini`, `mimarlik/__init__.py` (boş), `mimarlik/standartlar.py`, `mimarlik/dxf_yazici.py`
- Test: `tests/test_dxf_yazici.py`

**Interfaces:**
- Produces (`standartlar.py`):
  `KATMAN_DUVAR = "DUVAR"`, `KATMAN_KAPI = "KAPI"`, `KATMAN_PENCERE = "PENCERE"`, `KATMAN_OLCU = "OLCU"`;
  `KATMAN_RENKLERI: dict[str, int] = {KATMAN_DUVAR: 7, KATMAN_KAPI: 2, KATMAN_PENCERE: 4, KATMAN_OLCU: 3}`;
  `DIS_DUVAR_KALINLIGI = 25`, `IC_DUVAR_KALINLIGI = 10`, `KAPI_GENISLIGI = 90`, `PENCERE_GENISLIGI = 120`;
  `OLCU_STILI = "MIMARI"`, `OLCU_YAZI_YUKSEKLIGI = 15`.
  Dosyanın başında: "Mimardan cevap gelince değerleri burada değiştir" yorumu.
- Produces (`dxf_yazici.py`): `yeni_cizim(birim: str = "cm") -> ezdxf.document.Drawing`, `BIRIM_KODLARI = {"mm": 4, "cm": 5, "m": 6}`.

- [ ] **Step 1: `pytest.ini` yaz** — içerik: `[pytest]`, `pythonpath = .`, `testpaths = tests`.

- [ ] **Step 2: Failing testleri yaz** (`tests/test_dxf_yazici.py`)

```python
def test_yeni_cizim_r2010():
    assert yeni_cizim().dxfversion == "AC1024"

def test_yeni_cizim_varsayilan_birim_cm():
    doc = yeni_cizim()
    assert doc.header["$INSUNITS"] == 5
    assert doc.header["$MEASUREMENT"] == 1

def test_yeni_cizim_mm_birimi():
    assert yeni_cizim("mm").header["$INSUNITS"] == 4

def test_yeni_cizim_bilinmeyen_birim_hata():
    with pytest.raises(ValueError):
        yeni_cizim("inc")

def test_dort_katman_dogru_renkle():
    doc = yeni_cizim()
    for ad, renk in KATMAN_RENKLERI.items():
        assert doc.layers.get(ad).color == renk

def test_olcu_stili_var():
    stil = yeni_cizim().dimstyles.get(OLCU_STILI)
    assert stil.dxf.dimtxt == OLCU_YAZI_YUKSEKLIGI
    assert stil.dxf.dimtsz > 0      # ok yerine tick

def test_bos_cizim_audit_temiz():
    assert not yeni_cizim().audit().has_errors
```

- [ ] **Step 3: Çalıştır, FAIL gör** — `.venv/Scripts/python -m pytest tests/test_dxf_yazici.py -v` → `ModuleNotFoundError: mimarlik...`

- [ ] **Step 4: `standartlar.py` ve `yeni_cizim` yaz.** `doc.units = BIRIM_KODLARI[birim]`; `doc.header["$MEASUREMENT"] = 1`; her katman `doc.layers.add(ad, color=renk)`; ölçü stili `doc.dimstyles.new(OLCU_STILI, dxfattribs={"dimtxt": OLCU_YAZI_YUKSEKLIGI, "dimtsz": 5, "dimdec": 0, "dimexe": 10, "dimexo": 5, "dimgap": 5})`.

- [ ] **Step 5: Çalıştır, PASS gör** (7 test).

- [ ] **Step 6: Commit** — `git add pytest.ini mimarlik tests && git commit -m "Faz 1: standartlar ve yeni_cizim"`

---

### Task 2: `cizgi_ekle` ve `kaydet`

**Files:** Modify `mimarlik/dxf_yazici.py`; Test `tests/test_dxf_yazici.py`

**Interfaces:**
- Consumes: `yeni_cizim`, `KATMAN_*` (Task 1).
- Produces: `cizgi_ekle(doc, cizgiler: Iterable[tuple[float, float, float, float]], katman: str) -> None`;
  `kaydet(doc, yol: str | pathlib.Path) -> pathlib.Path` (yazılan yolu döndürür).

- [ ] **Step 1: Failing testleri yaz**

```python
def test_cizgiler_geri_okunur(tmp_path):
    doc = yeni_cizim()
    cizgiler = [(0, 0, 450, 0), (450, 0, 450, 350)]
    cizgi_ekle(doc, cizgiler, KATMAN_DUVAR)
    okunan = ezdxf.readfile(kaydet(doc, tmp_path / "t.dxf"))
    lines = okunan.modelspace().query('LINE[layer=="DUVAR"]')
    assert len(lines) == 2
    assert lines[0].dxf.start == pytest.approx((0, 0, 0))
    assert lines[0].dxf.end == pytest.approx((450, 0, 0))

def test_numpy_koordinatlar(tmp_path):
    doc = yeni_cizim()
    cizgi_ekle(doc, [tuple(np.array([0, 0, 10, 0], dtype=np.int32))], KATMAN_DUVAR)
    okunan = ezdxf.readfile(kaydet(doc, tmp_path / "t.dxf"))
    assert len(okunan.modelspace().query("LINE")) == 1

def test_bos_liste_hata_vermez():
    cizgi_ekle(yeni_cizim(), [], KATMAN_DUVAR)

def test_tanimsiz_katman_hata():
    doc = yeni_cizim()
    katman_sayisi = len(doc.layers)
    with pytest.raises(ValueError):
        cizgi_ekle(doc, [(0, 0, 1, 0)], "duvar")
    assert len(doc.layers) == katman_sayisi
    assert len(doc.modelspace().query("LINE")) == 0

def test_sifir_uzunluk_hata():
    with pytest.raises(ValueError):
        cizgi_ekle(yeni_cizim(), [(5, 5, 5, 5)], KATMAN_DUVAR)

def test_yanlis_bicim_hata():
    with pytest.raises(ValueError):
        cizgi_ekle(yeni_cizim(), [(0, 0, 1)], KATMAN_DUVAR)

def test_ic_ice_klasor_olusturulur(tmp_path):
    yol = kaydet(yeni_cizim(), tmp_path / "a" / "b" / "x.dxf")
    assert yol.exists()
```

Not: ezdxf katman tablosu (AutoCAD gibi) büyük/küçük harf duyarsız — `"duvar" in doc.layers` True döner (doğrulandı). Bu yüzden katman kontrolü `doc.layers` ile değil, `KATMAN_RENKLERI` anahtarlarıyla **birebir** yapılır.

- [ ] **Step 2: Çalıştır, FAIL gör** — `ImportError: cannot import name 'cizgi_ekle'`.

- [ ] **Step 3: Yaz.** Katman kontrolü `katman not in KATMAN_RENKLERI` (birebir eşleşme) → `ValueError`; her çizgi önce 4 elemana açılır (değilse `ValueError`, mesajda hatalı çizgi), `float()` ile çevrilir, sıfır uzunlukta `ValueError`, sonra `msp.add_line((x1, y1), (x2, y2), dxfattribs={"layer": katman})`. Hatalı bir çizgi gelirse hiçbir çizgi eklenmemeli: önce tümünü doğrula, sonra ekle. `kaydet`: `Path(yol).parent.mkdir(parents=True, exist_ok=True)`, `doc.saveas(yol)`.

- [ ] **Step 4: Çalıştır, PASS gör** — tüm `test_dxf_yazici.py`.

- [ ] **Step 5: Commit** — `"Faz 1: cizgi_ekle ve kaydet"`

---

### Task 3: `yay_ekle` ve `olcu_ekle`

**Files:** Modify `mimarlik/dxf_yazici.py`; Test `tests/test_dxf_yazici.py`

**Interfaces:**
- Produces: `yay_ekle(doc, merkez: tuple[float, float], yaricap: float, bas_aci: float, bit_aci: float, katman: str) -> None` (açılar derece, saat yönü tersine);
  `olcu_ekle(doc, p1: tuple[float, float], p2: tuple[float, float], uzaklik: float, katman: str) -> None` (`uzaklik` > 0: p1→p2 yönünün solu, < 0: sağı).

- [ ] **Step 1: Failing testleri yaz**

```python
def test_yay_geri_okunur(tmp_path):
    doc = yeni_cizim()
    yay_ekle(doc, (75, 25), 90, 0, 90, KATMAN_KAPI)
    arc = ezdxf.readfile(kaydet(doc, tmp_path / "t.dxf")).modelspace().query('ARC[layer=="KAPI"]')[0]
    assert arc.dxf.radius == pytest.approx(90)
    assert (arc.dxf.start_angle, arc.dxf.end_angle) == pytest.approx((0, 90))

def test_olcu_degeri_ve_stili(tmp_path):
    doc = yeni_cizim()
    olcu_ekle(doc, (0, 0), (450, 0), -60, KATMAN_OLCU)
    dim = ezdxf.readfile(kaydet(doc, tmp_path / "t.dxf")).modelspace().query('DIMENSION[layer=="OLCU"]')[0]
    assert dim.get_measurement() == pytest.approx(450)
    assert dim.dxf.dimstyle == OLCU_STILI
    assert dim.dxf.defpoint[1] == pytest.approx(-60)

def test_yay_ve_olcu_tanimsiz_katman_hata():
    doc = yeni_cizim()
    with pytest.raises(ValueError):
        yay_ekle(doc, (0, 0), 1, 0, 90, "KAPII")
    with pytest.raises(ValueError):
        olcu_ekle(doc, (0, 0), (1, 0), 1, "OLCUU")

def test_olculu_cizim_audit_temiz():
    doc = yeni_cizim()
    olcu_ekle(doc, (0, 0), (450, 0), -60, KATMAN_OLCU)
    assert not doc.audit().has_errors
```

- [ ] **Step 2: Çalıştır, FAIL gör.**
- [ ] **Step 3: Yaz.** Katman kontrolünü Task 2'deki yardımcıyla paylaş (`_katmani_dogrula(katman)`). Yay: `msp.add_arc(...)`. Ölçü: `msp.add_aligned_dim(p1=..., p2=..., distance=uzaklik, dimstyle=OLCU_STILI, dxfattribs={"layer": katman}).render()` — `render()` olmadan AutoCAD ölçüyü göstermeyebilir.
- [ ] **Step 4: Çalıştır, PASS gör.**
- [ ] **Step 5: Commit** — `"Faz 1: yay_ekle ve olcu_ekle"`

---

### Task 4: Örnek oda demosu ve elle doğrulama

**Files:** Create `mimarlik/demo_oda.py`; Test `tests/test_demo_oda.py`; Modify `CLAUDE.md` (Bölüm 7 günlüğe satır)

**Interfaces:**
- Consumes: Task 1–3'ün tüm fonksiyonları ve sabitleri.
- Produces: `oda_geometrisi() -> dict` → anahtarlar `"cizgiler": dict[str, list[tuple4]]`, `"yaylar": list[(merkez, yaricap, bas_aci, bit_aci, katman)]`, `"olculer": list[(p1, p2, uzaklik, katman)]` (spec'teki "katman → çizgi sözlüğü"nü yay ve ölçüyü de taşıyacak şekilde genişletme — benim kararım);
  `oda_ciz(yol="output/oda_demo.dxf") -> pathlib.Path`; `if __name__ == "__main__":` → `oda_ciz()` ve yolu yazdır.
- Modül sabitleri (demoya özel, standart değil): `ODA_IC_GENISLIK = 400`, `ODA_IC_DERINLIK = 300`, `KAPI_KOSE_MESAFESI = 50`. Koordinatlar bu sabitlerden ve `standartlar`'dan **hesaplanır**, elle yazılmaz.

Beklenen geometri (mevcut değerlerle; testler bunları sabitler):
- Dış (0,0)–(450,350), iç (25,25)–(425,325).
- Kapı boşluğu güneyde x 75–165; pencere boşluğu kuzeyde x 165–285.
- DUVAR (16): dış güney `(0,0,75,0)`, `(165,0,450,0)`; dış doğu `(450,0,450,350)`; dış kuzey `(450,350,285,350)`, `(165,350,0,350)`; dış batı `(0,350,0,0)`; iç için aynısı y=25/325, x=25/425; söveler `(75,0,75,25)`, `(165,0,165,25)`, `(165,325,165,350)`, `(285,325,285,350)`.
- KAPI: kanat `(75,25,75,115)`, yay merkez (75,25), r=90, 0°→90°.
- PENCERE: `(165,350,285,350)`, `(165,337.5,285,337.5)`, `(165,325,285,325)`.
- OLCU: `((0,0),(450,0),-60)` ve `((450,0),(450,350),-60)` (sağ tarafa düşer).

- [ ] **Step 1: Failing testleri yaz** (`tests/test_demo_oda.py`; `oda_ciz(tmp_path / "oda.dxf")` ile üret, `ezdxf.readfile` ile oku)

```python
def test_duvar_16_cizgi(okunan):          assert len(msp.query('LINE[layer=="DUVAR"]')) == 16
def test_kapi_1_cizgi_1_yay(okunan):       # LINE KAPI == 1, ARC KAPI == 1, yay r == 90
def test_pencere_3_cizgi(okunan):          assert len(msp.query('LINE[layer=="PENCERE"]')) == 3
def test_olcu_450_ve_350(okunan):          # sorted(get_measurement()) == approx([350, 450])
def test_dis_sinir_450x350(okunan):        # DUVAR çizgilerinin min/max x,y == (0,0,450,350)
def test_tum_nesneler_4_katmanda(okunan):  # her entity.dxf.layer in KATMAN_RENKLERI
def test_audit_temiz(okunan):              assert not okunan.audit().has_errors
def test_geometri_tekrarsiz():             # oda_geometrisi()["cizgiler"]["DUVAR"] içinde aynı çizgi iki kez yok
```
(`okunan` bir pytest fixture'ı; `msp = okunan.modelspace()`.)

- [ ] **Step 2: Çalıştır, FAIL gör.**
- [ ] **Step 3: `demo_oda.py` yaz.**
- [ ] **Step 4: Tüm testleri çalıştır** — `.venv/Scripts/python -m pytest -v` → hepsi PASS.
- [ ] **Step 5: Demoyu çalıştır** — `.venv/Scripts/python -m mimarlik.demo_oda` → `output/oda_demo.dxf` yazıldı mesajı.
- [ ] **Step 6: Elle doğrulama (kullanıcı/mimar)** — AutoCAD'de aç; 4 katman, `UNITS` = cm, dış ölçü 450; bir duvarı taşı/uzat; ölçünün bağlı noktası değişince değeri güncelleniyor. Sonucu kullanıcı bildirir; bu adım kod tarafından "geçti" sayılmaz.
- [ ] **Step 7: `CLAUDE.md` günlüğe satır ekle** — `| 2026-11-xx | 1 | DXF yazıcı modülü + örnek oda | AutoCAD doğrulaması / Faz 2 hazırlığı |`
- [ ] **Step 8: Commit** — `"Faz 1: örnek oda demosu"`
