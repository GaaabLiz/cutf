import shutil
import subprocess
from pathlib import Path

import pytest

from cutf.util.iconv import convert_to_utf8_with_iconv


ICONV_AVAILABLE = shutil.which("iconv") is not None


def test_convert_to_utf8_with_iconv_writes_bom(tmp_path: Path, monkeypatch):
    source = tmp_path / "sample.txt"
    source.write_text("hello", encoding="utf-8")

    def fake_run(command, stdout, stderr, check):
        _ = (command, stderr, check)
        stdout.write("converted")

    monkeypatch.setattr("cutf.util.iconv.subprocess.run", fake_run)

    convert_to_utf8_with_iconv(str(source), "latin-1", "utf-8")

    data = source.read_bytes()
    assert data.startswith(b"\xef\xbb\xbf")
    assert b"converted" in data


@pytest.mark.skipif(not ICONV_AVAILABLE, reason="iconv not available")
@pytest.mark.parametrize(
    ("source_encoding", "text"),
    [
        ("windows-1252", "label cp1252 citta € “quote” e perche gia"),
        ("iso-8859-1", "label iso citta perche gia deja e AEOU"),
    ],
)
def test_convert_to_utf8_with_iconv_real_encodings(tmp_path: Path, source_encoding: str, text: str):
    source = tmp_path / f"sample_{source_encoding}.txt"
    source.write_bytes(text.encode(source_encoding))

    convert_to_utf8_with_iconv(str(source), source_encoding, "utf-8")

    data = source.read_bytes()
    assert data.startswith(b"\xef\xbb\xbf")
    assert data.decode("utf-8-sig") == text
    assert not source.with_suffix(".txt.tmp").exists()
    assert not source.with_suffix(".txt.bom").exists()


def test_convert_to_utf8_with_iconv_cleans_temp_files_on_failure(tmp_path: Path, monkeypatch):
    source = tmp_path / "sample.txt"
    source.write_text("hello", encoding="utf-8")

    def fake_run(command, stdout, stderr, check):
        _ = (stderr, check)
        stdout.write("partial")
        raise subprocess.CalledProcessError(1, command)

    monkeypatch.setattr("cutf.util.iconv.subprocess.run", fake_run)

    convert_to_utf8_with_iconv(str(source), "latin-1", "utf-8")

    assert not source.with_suffix(".txt.tmp").exists()
    assert not source.with_suffix(".txt.bom").exists()

