"""dwg: ODA File Converter yoksa DWG atlanır; varsa doğru sürümle çağrılır (dönüştürücü çağrılmaz, sahte)."""

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
