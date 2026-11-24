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
KATMAN_KONTROL = "KONTROL"  # programın emin olmadığı yerler (kapanmayan duvarlar, "emin değilim")

# Katman -> AutoCAD renk numarası (ACI). 7 beyaz/siyah, 2 sarı, 4 camgöbeği, 3 yeşil.
KATMAN_RENKLERI = {
    KATMAN_DUVAR: 7,
    KATMAN_KAPI: 2,
    KATMAN_PENCERE: 4,
    KATMAN_OLCU: 3,
    KATMAN_KONTROL: 1,  # kırmızı
}

# Katman -> çizgi kalınlığı (DXF lineweight, 1/100 mm: 50 = 0,50 mm).
# B-10 (KESİN, mimar 24.11.2026): kalınlık yukarıdan aşağı incelir — duvar (ve kolon) en kalın, kapı/pencere
# orta, ölçü ince (zemin seramiği en ince; henüz çizilmiyor). SIRA kesin; mm DEĞERLERİ bizim varsayımımız
# (yaygın mimari kalem takımı 0,50 / 0,25 / 0,13), mimarın şablonu gelince burada değiştir.
# Yalnız DXF'in izin verdiği değerler: 0, 5, 9, 13, 15, 18, 20, 25, 30, 35, 40, 50, 53, 60, 70, 80, 90, 100…
KATMAN_KALINLIKLARI = {
    KATMAN_DUVAR: 50,
    KATMAN_KAPI: 25,
    KATMAN_PENCERE: 25,
    KATMAN_OLCU: 13,
    KATMAN_KONTROL: 18,  # program notu; baskıya girmez, okunur kalsın diye ölçüden biraz kalın
}

# --- Teslim dosyası ---------------------------------------------------------
# B-12 (KESİN): kullanıcıya DWG teslim edilir (DXF ara dosya). B-11 (KESİN): en eski sürüm AutoCAD 2017;
# AutoCAD 2017'nin açabildiği en yeni DWG biçimi 2013 biçimi (AC1027), 2018 biçimini açamaz.
DWG_SURUMU = "R2013"

# --- Mimari ölçüler (cm) ----------------------------------------------------
# Duvar kalınlıkları mimara soruldu (S6): değerleri varsayimlar.py'de değiştir.
from mimarlik.varsayimlar import DIS_DUVAR_KALINLIGI, IC_DUVAR_KALINLIGI  # noqa: E402,F401
KAPI_GENISLIGI = 90
PENCERE_GENISLIGI = 120

# --- Ölçülendirme -----------------------------------------------------------
OLCU_STILI = "MIMARI"
# Ölçü yazılarının yazı stili. Çizimde tanımlı olmalı: yoksa AutoCAD ölçüyü
# yeniden oluştururken yazıyı çizemez (ölçü çizgisi görünür, 450 yazısı görünmez).
OLCU_YAZI_STILI = "Standard"
OLCU_YAZI_YUKSEKLIGI = 15  # cm; 1/50 baskıda 3 mm
