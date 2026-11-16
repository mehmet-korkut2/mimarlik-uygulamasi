"""Krokilerdeki ölçü sayılarının doğru cevapları (kullanıcıdan, 2026-11-16). Sıra önemsiz."""

KROKILER = {
    "01": "ornekler/01_kolay_tek_oda_180x140.jpg",
    "02": "ornekler/02_kolay_tek_oda_300x240.jpg",
}

DOGRU = {
    "01": [180, 50, 40, 108, 120, 120, 15, 90, 10, 140],
    "02": [15, 300, 45, 45, 90, 40, 45, 200, 240, 40, 40, 40, 102, 200],
}

# 01'de okunuşu belirsiz sayılar (CLAUDE.md: mimara sorulacak); raporda ayrıca gösterilir.
BELIRSIZ = {"01": [15, 90, 10]}
