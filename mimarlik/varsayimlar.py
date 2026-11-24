"""Krokiyi yorumlarken yaptığımız, MİMARIN CEVABINA BAĞLI varsayımlar.

Mimara gönderilen soru listesi (output/mimara_sorular.pdf, 19.11.2026) cevaplanınca
yalnızca bu dosya değişir. Her varsayımın yanında ilgili soru numarası (S1, S3, S6…) yazar.
Mimarın cevapları: 24.11.2026 (mimar_cevaplari.pdf). Her kuralın yanında durumu yazar:
KESİN = mimar cevapladı, AÇIK = cevap yok, eski varsayım duruyor.

Tüm uzunluklar cm cinsindendir.
"""

# --- S6: ölçü türü ve duvar kalınlığı --------------------------------------------------------------
# Ölçüler İÇ ölçü: duvar yüzünden duvar yüzüne. Krokide çizilen tek çizgi duvarın iç yüzü sayılır,
# dış yüz DIS_DUVAR_KALINLIGI kadar dışarıda çizilir.
OLCULER_IC_OLCU = True
DIS_DUVAR_KALINLIGI = 25
IC_DUVAR_KALINLIGI = 10

# --- S1: bir kenardaki açıklık ---------------------------------------------------------------------
# Arka arkaya yazılan üç sayı "duvar – kapı boşluğu – duvar"; kapı sayısı net geçiş; toplamları
# kenarın boyu. Açıklık kapı sayılır, içeri açılır, menteşe açıklığın kontur yönündeki başında.
ACIKLIK_KAPIDIR = True

# --- S3: iç duvarın birleştiği kenara yazılan sayı (KESİN, mimar 24.11.2026: "B") ------------------
# Sayı, iç duvarın birleştiği noktadan köşeye kadarki PARÇANIN ölçüsüdür (02'deki üst 300 tüm duvar değil).
# Kenarın diğer parçaları kapanmadan hesaplanır, olmazsa ölçekten tahmin edilir.
# True: eski varsayım A (tek sayı kenarın köşeden köşeye tamamı); mimar bunu reddetti.
TEK_SAYI_KENARIN_TAMAMI = False

# --- S4: toplamlar tutmuyor ------------------------------------------------------------------------
# Karşılıklı duvar toplamları arasındaki bu kadar farka "tutuyor" denir (fark yine de raporlanır).
KAPANMA_TOLERANSI = 5

# --- Eşleştirme (mimara değil, ölçüme bağlı; 2026-11-18 kararı) ------------------------------------
# Y2'nin değer yazdığı parça "gürültü" sayılırsa kullanıcıya sorulur: konturda olmayan kenar ya da
# GURULTU_EN_KISA * h'den kısa parça (h: karakter yüksekliği, px).
GURULTU_EN_KISA = 2


def kenar_boyu(parca_degerleri: list[int | None]) -> tuple[int | None, bool]:
    """Bir kenarın parçalarına bağlanan değerlerden kenar boyu.

    parca_degerleri: kenar yönünde sıralı, her parça için değer ya da None.
    Döner: (boy ya da None, tek_sayi_tamami). Boy None ise kenar bu kurallarla çözülemedi
    (hiç değer yok ya da bazı parçalar eksik); geometri adımı eksikleri kapanmadan / ölçekten bulur.
    """
    dolu = [d for d in parca_degerleri if d is not None]
    if not dolu:
        return None, False
    if len(dolu) == len(parca_degerleri):           # S1: parçaların toplamı
        return sum(dolu), False
    if len(dolu) == 1 and TEK_SAYI_KENARIN_TAMAMI:  # S3: tek sayı köşeden köşeye
        return dolu[0], True
    return None, False
