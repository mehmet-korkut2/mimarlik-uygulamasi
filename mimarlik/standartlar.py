"""Çizim standartları: katman adları, renkler ve mimari ölçüler.

Mimardan cevap gelince değerleri BURADA değiştir; başka hiçbir dosyada
katman adı ya da ölçü elle yazılmaz.

Tüm uzunluklar cm cinsindendir.
"""

# --- Katman adları (ASCII) --------------------------------------------------
KATMAN_DUVAR = "DUVAR"
KATMAN_KAPI = "KAPI"
KATMAN_PENCERE = "PENCERE"
KATMAN_OLCU = "OLCU"

# Katman -> AutoCAD renk numarası (ACI). 7 beyaz/siyah, 2 sarı, 4 camgöbeği, 3 yeşil.
KATMAN_RENKLERI = {
    KATMAN_DUVAR: 7,
    KATMAN_KAPI: 2,
    KATMAN_PENCERE: 4,
    KATMAN_OLCU: 3,
}

# --- Mimari ölçüler (cm) ----------------------------------------------------
DIS_DUVAR_KALINLIGI = 25
IC_DUVAR_KALINLIGI = 10
KAPI_GENISLIGI = 90
PENCERE_GENISLIGI = 120

# --- Ölçülendirme -----------------------------------------------------------
OLCU_STILI = "MIMARI"
# Ölçü yazılarının yazı stili. Çizimde tanımlı olmalı: yoksa AutoCAD ölçüyü
# yeniden oluştururken yazıyı çizemez (ölçü çizgisi görünür, 450 yazısı görünmez).
OLCU_YAZI_STILI = "Standard"
OLCU_YAZI_YUKSEKLIGI = 15  # cm; 1/50 baskıda 3 mm
