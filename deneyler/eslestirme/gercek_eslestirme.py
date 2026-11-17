"""01 ve 02'nin gerçek kenar parçaları ve "sayı -> kenar parçası" cevabı (elle, 2026-11-17; kullanıcı tarafından onaylandı).

Koordinatlar orijinal fotoğraf pikseli (1152x2048). Kenar: köşeden köşeye düz duvar çizgisi.
Parça: kenarın köşe, T-birleşim ya da açıklık ucuyla ayrılan bölümü; tür "duvar" ya da "aciklik"
(mürekkepte boşluk). Sayı adları ../bul_kes_okut/konumlar.py ile aynı.
"""

# kenar id -> [(parça id, tür, başlangıç, bitiş)]  (kenar, parçaların birleşimi)
KENARLAR = {
    "01": {
        "K1": [("K1.1", "duvar", (90, 628), (523, 596))],
        "K2": [("K2.1", "duvar", (523, 596), (525, 720))],
        "K3": [("K3.1", "duvar", (525, 720), (705, 715))],
        "K4": [("K4.1", "duvar", (705, 715), (718, 1022))],
        "K5": [("K5.1", "duvar", (718, 1022), (272, 1058))],
        "K6": [("K6.1", "duvar", (272, 1058), (268, 1025)),
               ("K6.2", "aciklik", (268, 1025), (257, 912)),
               ("K6.3", "duvar", (257, 912), (255, 862))],
        "K7": [("K7.1", "duvar", (255, 862), (95, 850))],
        "K8": [("K8.1", "duvar", (95, 850), (90, 628))],
    },
    "02": {
        "K1": [("K1.1", "duvar", (200, 515), (345, 505)),      # X işaretli parça
               ("K1.2", "duvar", (345, 505), (805, 465))],
        "K2": [("K2.1", "duvar", (805, 465), (818, 545))],
        "K3": [("K3.1", "duvar", (818, 545), (900, 538))],
        "K4": [("K4.1", "duvar", (900, 538), (970, 1000))],
        "K5": [("K5.1", "duvar", (970, 1000), (600, 1008))],
        "K6": [("K6.1", "duvar", (600, 1008), (590, 920))],
        "K7": [("K7.1", "duvar", (590, 920), (412, 930))],
        "K8": [("K8.1", "duvar", (412, 930), (435, 1045))],
        "K9": [("K9.1", "duvar", (435, 1045), (240, 1045))],
        "K10": [("K10.1", "duvar", (240, 1045), (218, 710)),
                ("K10.2", "duvar", (218, 710), (200, 515))],   # X işaretli parça
        "K11": [("K11.1", "duvar", (218, 710), (360, 698))],   # iç duvar
        "K12": [("K12.1", "duvar", (345, 505), (350, 525)),    # iç duvar, üstte kapı açıklığı
                ("K12.2", "aciklik", (350, 525), (362, 630)),
                ("K12.3", "duvar", (362, 630), (360, 698))],
    },
}

# Dış kontur (saat yönünde); iç duvarlar (02: K11, K12) konturda değil.
KONTUR = {
    "01": ["K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8"],
    "02": ["K1", "K2", "K3", "K4", "K5", "K6", "K7", "K8", "K9", "K10"],
}

# sayı adı (konumlar.py) -> parça id
ESLESME = {
    "01": {"180": "K1.1", "50": "K2.1", "40": "K3.1", "120 sağ": "K4.1", "140": "K5.1",
           "10": "K6.1", "90": "K6.2", "15": "K6.3", "120 sol": "K7.1", "108": "K8.1"},
    "02": {"300": "K1.2", "45 üst sol": "K2.1", "45 üst sağ": "K3.1", "240": "K4.1", "200 alt": "K5.1",
           "40 sağ alt": "K6.1", "40 orta": "K7.1", "40 sol alt": "K8.1", "102": "K9.1", "200 sol": "K10.1",
           "45 alt": "K11.1", "15": "K12.1", "90": "K12.2", "40 üst": "K12.3"},
}

# Anlamı mimara bağlı: parçaya bağlandı ama ne ölçtüğü bilinmiyor (duvar–kapı–duvar hipotezi).
ANLAM_BILINMIYOR = {"01": {"10", "90", "15"}, "02": {"15", "90"}}

# Kapsamı belirsiz: sayı bir parçaya yazılmış ama tüm kenarı ölçüyor olabilir (mimara).
KAPSAM_BELIRSIZ = {"01": set(), "02": {"300", "200 sol"}}
