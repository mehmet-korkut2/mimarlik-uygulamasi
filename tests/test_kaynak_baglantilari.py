"""araclar.kaynak_baglantilari: kaynak listesinden yalnız bağlantılar kopyalanır."""

from araclar.kaynak_baglantilari import BASLIK, baglantilar, yaz


def test_yalniz_baglantilar_sirali_tekrarsiz():
    metin = ("kroki_03.jpg  https://ornek.org/plan?id=3  (izinli, not)\n"
             "kroki_04.png - kaynak: http://site.com/a/b.png.\n"
             "tekrar https://ornek.org/plan?id=3, ve <https://x.io/y>\n"
             "bağlantısız satır, dosya adı gizli_musteri.jpg\n")
    assert baglantilar(metin) == ["https://ornek.org/plan?id=3", "http://site.com/a/b.png", "https://x.io/y"]


def test_hedefe_baslik_ve_baglantilar_yazilir_baska_metin_yok(tmp_path):
    kaynak, hedef = tmp_path / "kaynaklar.txt", tmp_path / "cikti" / "kaynaklar.txt"
    kaynak.write_text("a.jpg https://a.com/1 telifli notu\nb.jpg\n", encoding="utf-8")
    assert yaz(kaynak, hedef) == 1
    metin = hedef.read_text(encoding="utf-8")
    assert metin == BASLIK + "https://a.com/1\n"
    assert "a.jpg" not in metin and "telifli" not in metin
