# Uçtan uca iskelet: `python -m mimarlik.kroki <fotoğraf>` → DXF (onaylandı 2026-11-19)

Akış: çizgi silme → Qwen-1 (sayılar + kutular) → kenar bulma, bölgeler, değer atama, geometrik bağlama
→ Qwen-2 / Y2 (numaralı parçalar) → birleştirme (tire varsa geometrik, yoksa Y2; çelişki ya da Y2 gürültü
parçası → "emin değilim") → geometri (dış kontur) → DXF + JSON rapor.

| Görev | İçerik |
|---|---|
| 1 | `mimarlik/varsayimlar.py` (S1, S3, S6, tolerans, gürültü); kalınlıklar oraya taşındı; KONTROL katmanı; `yazi_ekle`; `ollama` bağımlılığı |
| 2 | `mimarlik/okuma.py`: iki Qwen istemi, cevap ayrıştırma, parça görseli; Ollama yalnızca çağrıda yüklenir |
| 3 | `mimarlik/birlestirme.py`: ölçü başına parça, kaynak, emin/sebep |
| 4 | `mimarlik/geometri.py`: kenar boyları, kapanmadan tek bilinmeyen, ölçekten tahmin, kapanma kontrolü |
| 5 | `mimarlik/kroki.py`: DXF (DUVAR iç+dış yüz, KAPI, OLCU, KONTROL) + JSON; `--okuma <json>` |
| 6 | Uçtan uca sentetik test, 01–02 gerçek çalıştırma, günlük satırı |

Kullanıcı kararları: kalınlıklar `varsayimlar.py`'de; gürültü = konturda değil ya da 2h'den kısa; tolerans
5 cm, tolerans içindeki farklar da JSON'a yazılır; her görevden sonra dala push, main'e birleştirme yok.

Kapsam dışı: iç duvarların ölçülendirilmesi (KONTROL'de ölçekten "ölçüsüz" çizilir), düzeltme arayüzü,
kenar bulma iyileştirmesi.
