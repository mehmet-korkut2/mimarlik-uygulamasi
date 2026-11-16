# Faz 2 Deneyi — El Yazısı Ölçü Sayılarını Okuma (Spike)

Tarih: 2026-11-16 · Durum: onaylandı (2026-11-16) · Tür: **deney (spike)** — kod atılabilir, ana modüle girmez.

## Amaç ve neden

Faz 2'nin en riskli parçası krokideki el yazısı ölçü sayılarını okumak (CLAUDE.md Faz 2:
"Klasik OCR ile görüntü anlayan bir modeli 01–02 üzerinde karşılaştır; doğruluk, maliyet ve
bağımlılık açısından seç"). Mimarla görüşmeye bağlı değil, şimdi yapılabilir. Deney şu soruya
cevap verir: **Yerel model ile bulut model arasındaki fark ne kadar? Fark küçükse ürün yerel
yoldan gider** (kullanıcının tercihi: veri dışarı çıkmaz, ücretsiz, internet gerekmez).

## Karşılaştırılanlar (kullanıcı kararı)

| # | Yöntem | Nerede çalışır | Çalıştırma sayısı |
|---|---|---|---|
| 1 | **EasyOCR** | Yerel, CPU | 1 (deterministik); süre için ayrıca yükleme süresi ölçülür |
| 2 | **Gemini `gemini-3.8-flash`**, ücretsiz katman | Google bulutu | Krokide 3 |
| 3 | **Qwen3-VL `qwen3-vl:4b-instruct`**, Ollama | Yerel, GTX 1650 4 GB (+CPU) | Krokide 3 |

Claude API ve Tesseract bu deneyde yok (kullanıcı kararı: ödeme gerekiyor / el yazısında zayıf).

### Model seçimleri (benim kararlarım)

- **Gemini `gemini-3.8-flash`:** Google'ın dokümanına göre ücretsiz katmanı olan en yeni
  *kararlı* Flash modeli (önizleme değil); görüntü girişi destekliyor. Paket `google-genai`,
  anahtar `GEMINI_API_KEY` ortam değişkeninden okunur, koda yazılmaz. Ücretsiz katmanın dakika/gün
  sınırları yalnızca AI Studio'da (giriş gerekiyor) görünüyor; deney toplam 6 istek attığı için
  sorun beklemiyorum.
- **Qwen3-VL 4B (instruct, q4_K_M, 3,3 GB):** 4 GB'a "sığan" en büyük boyut. Gerekçe:
  - 8B (6,2 GB) kartın iki katı; çoğu CPU'da çalışır, çok yavaş olur.
  - 4B'nin ağırlıkları 3,3 GB; buna görüntü kodlayıcı, fotoğrafın ürettiği görüntü token'ları
    (2048×1152 bir fotoğraf ≈ 2.300 token) ve bellek önbelleği eklenince 4 GB'ı **biraz aşabilir**.
    Ollama bu durumda katmanların bir kısmını CPU'ya otomatik verir (kullanıcının izin verdiği
    GPU+CPU karışık çalışma). Hız kaybı olur ama 2B'ye göre okuma kalitesi belirgin şekilde daha
    iyi olmalı; deneyin sorusu kalite olduğu için 4B'yi seçiyorum.
  - **Instruct, "thinking" değil:** `qwen3-vl:4b` kısa adı "thinking" sürümüne gidiyor. Thinking
    sürümü matematik/akıl yürütme için uzun ara düşünce üretir; sayıları okumak için gereksiz ve
    GTX 1650'de dakikalar sürebilir.
  - **Yedek:** 4B GPU'ya hiç yüklenemezse ya da kroki başına 5 dakikayı aşarsa `qwen3-vl:2b-instruct`
    (1,9 GB, tamamen GPU'ya sığar) ile ölçerim ve raporda belirtirim.
  - Gerekenler: Ollama ≥ 0.12.7, güncel NVIDIA sürücüsü (512.89 eski — kullanıcı güncelliyor).
    Raporda `ollama ps` çıktısıyla GPU/CPU payı yazılır.

## Kurallar (adil karşılaştırma)

- **Girdi:** Ham fotoğraf, ön işleme yok — hepsine aynı. (Ön işlemenin etkisi bu deneyin konusu değil.)
- **Aynı istem (prompt)** iki görüntü modeline: "Bu el çizimi krokideki tüm el yazısı sayıları
  (ölçüleri) listele. Okuyamadığın sayıyı tahmin etme. Sadece JSON dizi döndür: [180, 50, ...]".
  Model sıcaklığı/rastgeleliği varsayılan bırakılır (tutarlılık zaten ölçülüyor).
- **EasyOCR:** `allowlist="0123456789"` (el yazısı "4"ün "u" okunmasını engeller),
  `rotation_info=[90, 180, 270]` (yan yazılmış sayılar için). CPU'da çalışır (PyTorch'un CUDA
  sürümü 2,5 GB ek indirme; deneyin sorusu için gerekmez). Süre CPU süresi olarak raporlanır.
- **"Sadece sayıları al" filtresi** (üç yönteme aynı): çıktıdaki her metinden `\d+` ile tam sayılar
  çıkarılır; 1–9999 dışı atılır.

## Puanlama (tekrarları doğru sayan)

Her kroki ve her çalıştırma için, okunan sayılar ile doğru cevap **çoklu küme** olarak karşılaştırılır:
- **Doğru** = her değer için min(okunan adet, gerçek adet) toplamı.
  (02'de dört tane 40 var; 40'ı bir kez okuyan 1 doğru alır, altı kez okuyan 4 doğru + 2 fazla.)
- **Fazla/uydurma** = okunan toplam − doğru.
- **Kaçırılan** = gerçek toplam − doğru.
- **01'in belirsiz sayıları (15, 90, 10)** ayrıca gösterilir: her yöntem bunları okudu mu, neyle karıştırdı.

Doğru cevaplar (kullanıcıdan, sıra önemsiz):
- 01: 180, 50, 40, 108, 120, 120, 15, 90, 10, 140 (10 sayı)
- 02: 15, 300, 45, 45, 90, 40, 45, 200, 240, 40, 40, 40, 102, 200 (14 sayı)

**Tutarlılık** (görüntü modelleri, 3 çalıştırma): 3 sonucun birebir aynı olup olmadığı; aynı değilse
her çalıştırmanın doğru/fazla/kaçırılan sayıları ve hangi sayıların değiştiği.

## Ölçülenler

Doğru / fazla / kaçırılan · süre (kroki başına; EasyOCR ve Qwen için model yükleme ayrı) ·
maliyet (EasyOCR ve Qwen: 0; Gemini ücretsiz katmanda 0, ücretli katmanda olsaydı: dönen token
sayısı × $0,75/$3,75 per 1M — 31.12.2026'ya kadar geçerli fiyat) · bağımlılık (kurulum boyutu,
internet, hesap gereksinimi).

## Dosyalar

```
deneyler/
  .venv/                       # deneye özel ortam (git'e girmez; .gitignore'daki .venv/ kuralı)
  ocr_karsilastirma/
    README.md                  # nasıl çalıştırılır
    requirements.txt           # easyocr, google-genai, ollama, pytest
    dogru_cevaplar.py          # yukarıdaki listeler + belirsiz sayılar
    puanlama.py                # filtre + çoklu küme puanlama
    test_puanlama.py           # puanlamanın küçük testleri (yanlış puanlama tüm sonucu bozar)
    calistir_easyocr.py
    calistir_gemini.py
    calistir_qwen.py
    rapor.py                   # sonuclar/*.json -> RAPOR.md
    sonuclar/                  # ham çıktılar (JSON; fotoğraf yok, sadece metin) — commit edilir
    RAPOR.md
```

**Ayrı ortam neden:** EasyOCR `opencv-python-headless` kurar; ana ortamdaki `opencv-python 5.0` ile
aynı `cv2` adını paylaşıp çakışır. PyTorch da yüzlerce MB. Ana ürünün `requirements.txt`'si temiz kalır.

**Fotoğraflar:** Kod `ornekler/`'den okur, hiçbir yere kopyalamaz; `sonuclar/` yalnızca metin içerir.
Commit'ten önce `git status` ile fotoğraf olmadığı kontrol edilir.

## Rapor (`RAPOR.md`)

1. Tablo: yöntem × kroki → doğru / fazla / kaçırılan, süre, maliyet.
2. 01'in belirsiz sayıları (15/90/10) yöntem yöntem.
3. Tutarlılık (Gemini, Qwen: 3 çalıştırma).
4. Bağımlılıklar ve veri: **Gemini ücretsiz katmanında gönderilen içerik Google tarafından ürün
   geliştirmede kullanılabilir** ("Content used to improve our products"); 01–02 için kullanıcı
   onaylı, gerçek müşteri krokileri için uygun değil.
5. **Cevap: yerel (Qwen3-VL 4B) ile bulut (Gemini Flash) arasındaki fark ne kadar, yerel yol ürün
   için yeterli mi?** Sayılarla, iki örnek üzerinden — ve 24 sayılık bir örneklemin sınırı açıkça
   belirtilerek.

## Hedef dışı

Sayıyı duvarla eşleştirme, ön işleme denemeleri, istem (prompt) iyileştirme turları, 03–07 krokileri,
ana modüle entegrasyon. Deney sonucunda seçilen yol Faz 2 planına ayrı bir tasarımla girer.

## Sıra

1. (Başladı, kullanıcı izniyle) `deneyler/.venv` + EasyOCR kurulumu.
2. `dogru_cevaplar.py`, `puanlama.py` + testleri.
3. EasyOCR çalıştırma → `sonuclar/easyocr.json`.
4. Kullanıcı `GEMINI_API_KEY`'i ayarlayınca: Gemini × 2 kroki × 3.
5. Kullanıcı Ollama'yı kurup sürücüyü güncelleyince: `ollama pull qwen3-vl:4b-instruct`, Qwen × 2 × 3.
6. `RAPOR.md`, commit (fotoğrafsız), push — onayla.
