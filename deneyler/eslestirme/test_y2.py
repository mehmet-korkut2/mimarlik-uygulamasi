import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from calistir_y2 import y2_ciftleri  # noqa: E402

ESLEM = {"P1": "K1.1", "P2": "K2.1"}


def test_gecerli_json():
    assert y2_ciftleri('{"P1": [180], "P2": [50, 40]}', ESLEM) == [(180, "K1.1"), (50, "K2.1"), (40, "K2.1")]


def test_kod_blogu_ve_metin_sayi():
    assert y2_ciftleri('```json\n{"P1": ["180"], "P2": []}\n```', ESLEM) == [(180, "K1.1")]


def test_bilinmeyen_parca_atlanir():
    assert y2_ciftleri('{"P9": [5], "P1": [7]}', ESLEM) == [(7, "K1.1")]


def test_bozuk_json_bos():
    assert y2_ciftleri('{"P1": [180', ESLEM) == []
    assert y2_ciftleri("bilmiyorum", ESLEM) == []
