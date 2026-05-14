from pathlib import Path

from cuft.controller.fileController import handle_file
from cuft.model.AppSetting import AppSetting


def _setting(**kwargs):
    base = dict(
        input_path="/tmp",
        is_file=True,
        extensions=[".txt", ".py"],
        checks=False,
        convert=False,
        copy_old_encoded=False,
        print_missing_char_str=False,
        print_skipped_file_no_action=False,
        print_result_only_relevant=False,
        verbose=False,
    )
    base.update(kwargs)
    return AppSetting(**base)


def test_handle_file_skips_unsupported_extension(tmp_path: Path):
    file_path = tmp_path / "a.bin"
    file_path.write_bytes(b"x")

    result = handle_file(str(file_path), _setting())

    assert result.skipped is True
    assert result.converted is False


def test_handle_file_returns_error_when_encoding_unknown(tmp_path: Path, monkeypatch):
    file_path = tmp_path / "a.txt"
    file_path.write_bytes(b"x")

    monkeypatch.setattr("cuft.controller.fileController.chardet.detect", lambda _: {"encoding": None})

    result = handle_file(str(file_path), _setting())

    assert result.error_skipped is True
    assert "Cannot detect encoding" in (result.error_description or "")


def test_handle_file_convert_flow(tmp_path: Path, monkeypatch):
    file_path = tmp_path / "a.txt"
    file_path.write_bytes(b"x")

    monkeypatch.setattr("cuft.controller.fileController.chardet.detect", lambda _: {"encoding": "latin-1"})

    calls = {"convert": 0, "check": 0}

    def fake_convert(path, src, dst):
        _ = (path, src, dst)
        calls["convert"] += 1

    def fake_check(path, enc):
        _ = (path, enc)
        calls["check"] += 1
        return []

    monkeypatch.setattr("cuft.controller.fileController.convert_to_utf8_with_iconv", fake_convert)
    monkeypatch.setattr("cuft.controller.fileController.check_illegal_chars", fake_check)

    result = handle_file(str(file_path), _setting(convert=True))

    assert result.converted is True
    assert calls == {"convert": 1, "check": 1}


def test_handle_file_checks_only_flow(tmp_path: Path, monkeypatch):
    file_path = tmp_path / "a.txt"
    file_path.write_bytes(b"x")

    monkeypatch.setattr("cuft.controller.fileController.chardet.detect", lambda _: {"encoding": "windows-1252"})
    monkeypatch.setattr("cuft.controller.fileController.check_illegal_chars", lambda *_: [])

    result = handle_file(str(file_path), _setting(checks=True))

    assert result.converted is False
    assert result.check_missing_char == []


def test_handle_file_copy_old_encoded(tmp_path: Path, monkeypatch):
    file_path = tmp_path / "a.txt"
    file_path.write_bytes(b"x")

    monkeypatch.setattr("cuft.controller.fileController.chardet.detect", lambda _: {"encoding": "cp1252"})
    monkeypatch.setattr("cuft.controller.fileController.convert_to_utf8_with_iconv", lambda *_: None)
    monkeypatch.setattr("cuft.controller.fileController.check_illegal_chars", lambda *_: [])

    copied = {"count": 0}

    def fake_copy(_):
        copied["count"] += 1
        return "/tmp/backup.txt"

    monkeypatch.setattr("cuft.controller.fileController.copy_old_encoded_file", fake_copy)

    handle_file(str(file_path), _setting(convert=True, copy_old_encoded=True))

    assert copied["count"] == 1

