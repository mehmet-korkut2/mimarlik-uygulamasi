"""DXF -> DWG (B-12: kullanıcıya DWG teslim edilir).

DWG kapalı bir biçim; dönüşümü ücretsiz ODA File Converter yapar (ezdxf'in `odafc` eklentisi çağırır).
Program kurulu değilse DWG atlanır, DXF yine yazılır. Dönüştürücünün yeri, öncelik sırasıyla:
  1. ODAFC_YOLU ortam değişkeni (ODAFileConverter.exe'nin tam yolu),
  2. ODA_KLASORU altındaki en yeni sürüm: ODA her sürümü ayrı klasöre kurar ("ODAFileConverter 27.10.0");
     sürüm numarası sayı olarak karşılaştırılır (27.10.0 > 27.9.1),
  3. ezdxf'in varsayılanı (sürümsüz klasör: Program Files/ODA/ODAFileConverter/ODAFileConverter.exe).
"""

import os
import re
from pathlib import Path

import ezdxf
from ezdxf.addons import odafc

from mimarlik.standartlar import DWG_SURUMU

KURULUM_NOTU = ("DWG yazılmadı: ODA File Converter bulunamadı. Ücretsiz indirme: "
                "https://www.opendesign.com/guestfiles/oda_file_converter — kurduktan sonra yeniden çalıştırın "
                r"(C:\Program Files\ODA dışına kurulduysa ODAFC_YOLU ortam değişkenine exe yolunu yazın).")


ODA_KLASORU = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "ODA"


def _surum(klasor: Path) -> tuple[int, ...]:
    """Klasör adındaki sürüm: "ODAFileConverter 27.10.0" -> (27, 10, 0); sürümsüz klasör en eski sayılır."""
    eslesme = re.search(r"(\d+(?:\.\d+)*)\s*$", klasor.name)
    return tuple(int(x) for x in eslesme.group(1).split(".")) if eslesme else ()


def en_yeni_oda(kok: Path | None = None) -> Path | None:
    """kok (varsayılan ODA_KLASORU) altındaki en yeni ODAFileConverter.exe; yoksa None."""
    kok = ODA_KLASORU if kok is None else kok
    adaylar = [exe for exe in kok.glob("ODAFileConverter*/ODAFileConverter.exe") if exe.is_file()]
    return max(adaylar, key=lambda exe: _surum(exe.parent), default=None)


def _yolu_ayarla() -> None:
    yol = os.environ.get("ODAFC_YOLU") or en_yeni_oda()
    if yol:
        yol = str(yol)
        ezdxf.options.set("odafc-addon", "win_exec_path", yol)
        ezdxf.options.set("odafc-addon", "unix_exec_path", yol)


def kurulu_mu() -> bool:
    _yolu_ayarla()
    return odafc.is_installed()


def dwg_yaz(dxf: str | Path, surum: str = DWG_SURUMU) -> Path | None:
    """DXF'in yanına aynı adla .dwg yazar. Döner: DWG yolu ya da (dönüştürücü yoksa) None."""
    if not kurulu_mu():
        return None
    dxf = Path(dxf)
    dwg = dxf.with_suffix(".dwg")
    odafc.convert(dxf, dwg, version=surum, replace=True)
    return dwg
