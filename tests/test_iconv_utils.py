from pathlib import Path

from cutf.util.iconv import convert_to_utf8_with_iconv


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

