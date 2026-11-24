"""DXF -> DWG (B-12: kullanıcıya DWG teslim edilir).

DWG kapalı bir biçim; dönüşümü ücretsiz ODA File Converter yapar (ezdxf'in `odafc` eklentisi çağırır).
Program kurulu değilse DWG atlanır, DXF yine yazılır. Kurulum yeri farklıysa ODAFC_YOLU ortam değişkeni
ODAFileConverter.exe'nin tam yolunu gösterir.
"""

import os
from pathlib import Path

import ezdxf
from ezdxf.addons import odafc

from mimarlik.standartlar import DWG_SURUMU

KURULUM_NOTU = ("DWG yazılmadı: ODA File Converter bulunamadı. Ücretsiz indirme: "
                "https://www.opendesign.com/guestfiles/oda_file_converter — kurduktan sonra yeniden çalıştırın "
                "(farklı klasöre kurulduysa ODAFC_YOLU ortam değişkenine exe yolunu yazın).")


def _yolu_ayarla() -> None:
    yol = os.environ.get("ODAFC_YOLU")
    if yol:
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
