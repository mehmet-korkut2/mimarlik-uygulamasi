"""dwg: ODA File Converter yoksa DWG atlanır; varsa doğru sürümle çağrılır (dönüştürücü çağrılmaz, sahte)."""

import pytest

from mimarlik import dwg
from mimarlik.standartlar import DWG_SURUMU


def test_donusturucu_yoksa_none(tmp_path, monkeypatch):
    monkeypatch.setattr(dwg.odafc, "is_installed", lambda: False)
    assert dwg.dwg_yaz(tmp_path / "a.dxf") is None


def test_donusturucu_varsa_autocad_2017_surumuyle(tmp_path, monkeypatch):
    cagri = {}

    def sahte_convert(kaynak, hedef, version, replace):
        cagri.update(kaynak=kaynak, hedef=hedef, version=version, replace=replace)

    monkeypatch.setattr(dwg.odafc, "is_installed", lambda: True)
    monkeypatch.setattr(dwg.odafc, "convert", sahte_convert)
    assert dwg.dwg_yaz(tmp_path / "a.dxf") == tmp_path / "a.dwg"
    assert cagri["version"] == DWG_SURUMU == "R2013" and cagri["replace"]   # AutoCAD 2017 açabilsin (B-11)


def test_odafc_yolu_ortam_degiskeninden(monkeypatch):
    ayarlanan = []
    monkeypatch.setenv("ODAFC_YOLU", r"D:\ODA\ODAFileConverter.exe")
    monkeypatch.setattr(dwg.ezdxf.options, "set", lambda *a: ayarlanan.append(a))
    monkeypatch.setattr(dwg.odafc, "is_installed", lambda: False)
    dwg.kurulu_mu()
    assert ("odafc-addon", "win_exec_path", r"D:\ODA\ODAFileConverter.exe") in ayarlanan


def _kur(kok, *klasorler):
    for ad in klasorler:
        (kok / ad).mkdir(parents=True)
        (kok / ad / "ODAFileConverter.exe").write_bytes(b"")


def test_en_yeni_surum_sayi_olarak_secilir(tmp_path):
    _kur(tmp_path, "ODAFileConverter", "ODAFileConverter 26.4.0", "ODAFileConverter 27.9.1",
         "ODAFileConverter 27.10.0")
    (tmp_path / "ODAFileConverter 28.0.0").mkdir()                     # exe'siz klasör sayılmaz
    assert dwg.en_yeni_oda(tmp_path) == tmp_path / "ODAFileConverter 27.10.0" / "ODAFileConverter.exe"


def test_kurulum_yoksa_none(tmp_path):
    assert dwg.en_yeni_oda(tmp_path) is None
    assert dwg.en_yeni_oda(tmp_path / "yok") is None


def _ayarlanan_yol(monkeypatch):
    ayarlanan = []
    monkeypatch.setattr(dwg.ezdxf.options, "set", lambda *a: ayarlanan.append(a))
    monkeypatch.setattr(dwg.odafc, "is_installed", lambda: False)
    dwg.kurulu_mu()
    return {a[2] for a in ayarlanan if a[1] == "win_exec_path"}


def test_odafc_yolu_bulunan_surumden_oncelikli(tmp_path, monkeypatch):
    _kur(tmp_path, "ODAFileConverter 27.10.0")
    monkeypatch.setattr(dwg, "ODA_KLASORU", tmp_path)
    monkeypatch.setenv("ODAFC_YOLU", r"D:\ODA\ODAFileConverter.exe")
    assert _ayarlanan_yol(monkeypatch) == {r"D:\ODA\ODAFileConverter.exe"}
    monkeypatch.delenv("ODAFC_YOLU")
    assert _ayarlanan_yol(monkeypatch) == {str(tmp_path / "ODAFileConverter 27.10.0" / "ODAFileConverter.exe")}


def test_hicbiri_yoksa_ezdxf_varsayilani_degismez(tmp_path, monkeypatch):
    monkeypatch.setattr(dwg, "ODA_KLASORU", tmp_path)
    monkeypatch.delenv("ODAFC_YOLU", raising=False)
    assert _ayarlanan_yol(monkeypatch) == set()


TURKCE = "KAPANMIYOR: çelişki, kapı ölçüsüz; ĞÜŞİÖÇ ğüşıöç İ ı"


@pytest.mark.skipif(not dwg.kurulu_mu(), reason="ODA File Converter kurulu değil")
def test_turkce_metin_dwg_gidis_donus_bozulmaz(tmp_path):
    """Gerçek dönüştürücüyle: DXF -> DWG -> geri okuma; metin ve Arial stili korunur (AutoCAD Web'de "?" idi)."""
    from mimarlik.dxf_yazici import kaydet, yazi_ekle, yeni_cizim
    from mimarlik.standartlar import YAZI_FONTU, YAZI_STILI
    doc = yeni_cizim()
    yazi_ekle(doc, TURKCE, (0, 0), 12, "KONTROL")
    yol = dwg.dwg_yaz(kaydet(doc, tmp_path / "turkce.dxf"))
    assert yol.read_bytes()[:6] == b"AC1027"                                    # AutoCAD 2013 biçimi
    geri = dwg.odafc.readfile(yol)
    assert [e.dxf.text for e in geri.modelspace().query("TEXT")] == [TURKCE]
    assert geri.styles.get(YAZI_STILI).dxf.font == YAZI_FONTU
