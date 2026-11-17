<!-- olcum.py üretir; elle düzenleme. -->
# Eşleştirme ölçümleri

## Kenar bulma

| Kroki | h (px) | Eksen (°) | Gerçek parça | Bulunan (eşleşen) | Kaçırılan | Fazla | Tür doğru | Kontur doğru |
|---|---|---|---|---|---|---|---|---|
| 01 | 37.0 | -3.7 | 10 | 6 | 4 | 0 | 6 | hayır |
| 02 | 23.5 | -4.8 | 16 | 11 | 5 | 11 | 11 | hayır |

## Bölge bulma (gerçekçi katman)

| Kroki | Gerçek sayı | Bulunan (≥ %50 kapsanan) | Bölge sayısı | Yazı olmayan | Bölünmüş | Birleşmiş |
|---|---|---|---|---|---|---|
| 01 | 10 | 10 | 13 | 3 | 0 | 0 |
| 02 | 14 | 14 | 28 | 13 | 1 | 1 |

## Eşleştirme (01 + 02; katı/gevşek /24, mimara bağlılar hariç /17)

Çalıştırmalı satırlarda değerler çalıştırma başına (1/2/3).

Fazla: doğru olmayan bağlama sayısı (yanlış parça, uydurma ya da fazla okunan değer); tasarım 7.3'e göre fazla değerin bir yere bağlanması hatadır.

| Katman | Kenarlar | Yerler | Değerler | Katı | Gevşek | Katı (hariç) | Gevşek (hariç) | Fazla |
|---|---|---|---|---|---|---|---|---|
| **Ü** üst sınır | gerçek | gerçek kutu | gerçek | 19 | 19 | 15 | 15 | 5 |
| **A** ara | bulunan | gerçek kutu | gerçek | 14 | 15 | 13 | 13 | 10 |
| **G** gerçekçi, hane ipuçlu | bulunan | bulunan bölge | Qwen | 13/14/10 | 14/14/11 | 12/13/9 | 12/13/9 | 14/15/15 |
| **G** gerçekçi, ipuçsuz | bulunan | bulunan bölge | Qwen | 13/14/10 | 14/14/11 | 12/13/9 | 12/13/9 | 14/15/15 |
| Y3 taban | gerçek | Qwen kutusu | Qwen | 13/15/17 | 13/16/17 | 9/13/13 | 9/13/13 | 14/14/8 |
| Y3 taban | bulunan | Qwen kutusu | Qwen | 9/13/13 | 10/14/14 | 8/12/12 | 8/12/12 | 18/16/12 |
| Y2 numaralı parçalar (kontur sırası) | gerçek | — | Qwen | 21/22/22 | 22/22/22 | 16/16/16 | 16/16/16 | 5/4/4 |
| Y2 numaralı parçalar (karışık sıra) | gerçek | — | Qwen | 19/18/19 | 20/21/19 | 14/15/14 | 14/15/14 | 7/8/7 |

### Kroki kroki (katı)

| Katman | 01 /10 | 02 /14 |
|---|---|---|
| U | 8 | 11 |
| A | 4 | 10 |
| G_hane | 5/5/3 | 8/9/7 |
| G_ipucusuz | 5/5/3 | 8/9/7 |
| Y3_gercek | 8/6/9 | 5/9/8 |
| Y3_bulunan | 5/4/6 | 4/9/7 |
| Y2 | 10/10/10 | 11/12/12 |
| Y2_karisik | 8/6/8 | 11/12/11 |

## Değer atama (G; doğru değeri alan bölge / atanan, çalıştırma başına)

| Kroki | Hane ipuçlu | İpuçsuz | Yeri bulunamayan (ipuçlu) | Okunmamış bölge (ipuçlu) |
|---|---|---|---|---|
| 01 | 10÷10/8÷10/7÷11 | 10÷10/9÷10/7÷11 | 0/0/0 | 3/3/2 |
| 02 | 10÷17/10÷19/9÷14 | 10÷17/10÷19/8÷14 | 0/0/0 | 11/9/14 |

## Bağlama nedeni (adet / doğru)

| Katman | işaret | temas | en yakın | bağlanamadı |
|---|---|---|---|---|
| U | 9 / 9 | 0 / 0 | 15 / 10 | 0 / 0 |
| A | 9 / 8 | 1 / 0 | 14 / 6 | 0 / 0 |
| G ipuçlu (3 çalıştırma toplamı) | 36 / 20 | 16 / 5 | 28 / 11 | 1 / 0 |

## Süre (kroki başına, Qwen hariç)

- 01: kenar + bölge bulma 0.36 s, atama + bağlama 147 ms
- 02: kenar + bölge bulma 0.85 s, atama + bağlama 1 ms
- Y2 (Qwen, kroki başına): 70, 70, 68, 78, 78, 79 s
- Y2_karisik (Qwen, kroki başına): 59, 67, 66, 78, 78, 79 s

## Ayrıntı: Ü ve A katmanında her sayı

| Kroki | Sayı | Gerçek parça | Ü | Ü nedeni | A | A nedeni |
|---|---|---|---|---|---|---|
| 01 | 180 | K1.1 | ✓ K1.1 | isaret | ✓ K1.1 | isaret |
| 01 | 108 | K8.1 | ✗ K1.1 | en_yakin | ✗ K1.1 | en_yakin |
| 01 | 120 sol | K7.1 | ✓ K7.1 | en_yakin | ✗ K8.1 | en_yakin |
| 01 | 15 (mimara) | K6.3 | ✓ K6.3 | en_yakin | ✗ K5.1 | en_yakin |
| 01 | 90 (mimara) | K6.2 | ✓ K6.2 | en_yakin | ✗ K5.1 | en_yakin |
| 01 | 10 (mimara) | K6.1 | ✗ K5.1 | en_yakin | ✗ K5.1 | en_yakin |
| 01 | 140 | K5.1 | ✓ K5.1 | en_yakin | ✓ K5.1 | en_yakin |
| 01 | 50 | K2.1 | ✓ K2.1 | isaret | ✓ K2.1 | isaret |
| 01 | 40 | K3.1 | ✓ K3.1 | en_yakin | ✗ K4.1 | en_yakin |
| 01 | 120 sağ | K4.1 | ✓ K4.1 | isaret | ✓ K4.1 | isaret |
| 02 | 15 (mimara) | K12.1 | ✗ K1.2 | en_yakin | ✗ K1.1 | en_yakin |
| 02 | 300 (mimara) | K1.2 | ✓ K1.2 | isaret | ✗ K1.1 | isaret |
| 02 | 45 üst sol | K2.1 | ✗ K3.1 | en_yakin | ✗ K3.1 | en_yakin |
| 02 | 45 üst sağ | K3.1 | ✓ K3.1 | en_yakin | ✓ K3.1 | en_yakin |
| 02 | 90 (mimara) | K12.2 | ✗ K1.2 | en_yakin | ✗ K12.1 | temas |
| 02 | 40 üst | K12.3 | ✓ K12.3 | isaret | ✓ K12.3 | isaret |
| 02 | 45 alt | K11.1 | ✓ K11.1 | isaret | ✓ K11.1 | isaret |
| 02 | 200 sol (mimara) | K10.1 | ✓ K10.1 | isaret | ✓ K10.1 | isaret |
| 02 | 40 orta | K7.1 | ✓ K7.1 | en_yakin | ✓ K7.1 | en_yakin |
| 02 | 40 sol alt | K8.1 | ✓ K8.1 | isaret | ✓ K8.1 | isaret |
| 02 | 40 sağ alt | K6.1 | ✓ K6.1 | isaret | ✓ K6.1 | isaret |
| 02 | 240 | K4.1 | ✓ K4.1 | en_yakin | ✓ K4.1 | en_yakin |
| 02 | 102 | K9.1 | ✓ K9.1 | en_yakin | ✓ K9.1 | en_yakin |
| 02 | 200 alt | K5.1 | ✓ K5.1 | en_yakin | ✓ K5.1 | en_yakin |
