from pathlib import Path

import pytest

from cutf.controller.fileController import handle_file
from cutf.model.AppSetting import AppSetting


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
        fix_wrong_with_ai=False,
        ai_ollama_url=None,
        ai_model="qwen2.5:1.5b-instruct",
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

    monkeypatch.setattr("cutf.controller.fileController.chardet.detect", lambda _: {"encoding": None})

    result = handle_file(str(file_path), _setting())

    assert result.error_skipped is True
    assert "Cannot detect encoding" in (result.error_description or "")


def test_handle_file_convert_flow(tmp_path: Path, monkeypatch):
    file_path = tmp_path / "a.txt"
    file_path.write_bytes(b"x")

    monkeypatch.setattr("cutf.controller.fileController.chardet.detect", lambda _: {"encoding": "latin-1"})

    calls = {"convert": 0, "check": 0}

    def fake_convert(path, src, dst):
        _ = (path, src, dst)
        calls["convert"] += 1

    def fake_check(path, enc):
        _ = (path, enc)
        calls["check"] += 1
        return []

    monkeypatch.setattr("cutf.controller.fileController.convert_to_utf8_with_iconv", fake_convert)
    monkeypatch.setattr("cutf.controller.fileController.check_illegal_chars", fake_check)

    result = handle_file(str(file_path), _setting(convert=True))

    assert result.converted is True
    assert calls == {"convert": 1, "check": 1}


def test_handle_file_checks_only_flow(tmp_path: Path, monkeypatch):
    file_path = tmp_path / "a.txt"
    file_path.write_bytes(b"x")

    monkeypatch.setattr("cutf.controller.fileController.chardet.detect", lambda _: {"encoding": "windows-1252"})
    monkeypatch.setattr("cutf.controller.fileController.check_illegal_chars", lambda *_: [])

    result = handle_file(str(file_path), _setting(checks=True))

    assert result.converted is False
    assert result.check_missing_char == []


def test_handle_file_ai_fix_flow(tmp_path: Path, monkeypatch):
    file_path = tmp_path / "a.txt"
    file_path.write_text("questo � un esempio\n", encoding="utf-8")

    monkeypatch.setattr("cutf.controller.fileController.chardet.detect", lambda _: {"encoding": "utf-8"})

    class FakeSummary:
        total_missing_chars = 1
        applied_fixes = 1
        skipped_fixes = 0
        retry_count = 1
        failed_fixes = 0
        remaining_occurrences = []

    monkeypatch.setattr("cutf.controller.fileController.fix_wrong_chars_with_ai", lambda *_: FakeSummary())
    monkeypatch.setattr("cutf.controller.fileController.check_illegal_chars", lambda *_: ["should-not-run"])

    result = handle_file(
        str(file_path),
        _setting(fix_wrong_with_ai=True, ai_ollama_url="http://localhost:11434"),
    )

    assert result.ai_fix_enabled is True
    assert result.ai_total_missing_chars == 1
    assert result.ai_applied_fixes == 1
    assert result.check_missing_char == []
    assert result.converted is False


def test_handle_file_copy_old_encoded(tmp_path: Path, monkeypatch):
    file_path = tmp_path / "a.txt"
    file_path.write_bytes(b"x")

    monkeypatch.setattr("cutf.controller.fileController.chardet.detect", lambda _: {"encoding": "cp1252"})
    monkeypatch.setattr("cutf.controller.fileController.convert_to_utf8_with_iconv", lambda *_: None)
    monkeypatch.setattr("cutf.controller.fileController.check_illegal_chars", lambda *_: [])

    copied = {"count": 0}

    def fake_copy(_):
        copied["count"] += 1
        return "/tmp/backup.txt"

    monkeypatch.setattr("cutf.controller.fileController.copy_old_encoded_file", fake_copy)

    handle_file(str(file_path), _setting(convert=True, copy_old_encoded=True))

    assert copied["count"] == 1


def test_handle_file_matches_extensions_case_insensitively(tmp_path: Path, monkeypatch):
    file_path = tmp_path / "a.PY"
    file_path.write_bytes(b"x")

    monkeypatch.setattr("cutf.controller.fileController.chardet.detect", lambda _: {"encoding": "latin-1"})

    calls = {"convert": 0, "check": 0}

    def fake_convert(path, src, dst):
        _ = (path, src, dst)
        calls["convert"] += 1

    def fake_check(path, enc):
        _ = (path, enc)
        calls["check"] += 1
        return []

    monkeypatch.setattr("cutf.controller.fileController.convert_to_utf8_with_iconv", fake_convert)
    monkeypatch.setattr("cutf.controller.fileController.check_illegal_chars", fake_check)

    result = handle_file(str(file_path), _setting(convert=True, extensions=[".py"]))

    assert result.converted is True
    assert calls == {"convert": 1, "check": 1}


@pytest.mark.parametrize("encoding", ["utf-8", "utf-8-sig", "utf-16", "utf-16le", "utf-16be"])
def test_handle_file_skips_utf_compatible_encodings_during_convert(tmp_path: Path, monkeypatch, encoding: str):
    file_path = tmp_path / "a.py"
    file_path.write_bytes(b"x")

    monkeypatch.setattr("cutf.controller.fileController.chardet.detect", lambda _: {"encoding": encoding})

    calls = {"convert": 0, "check": 0}

    def fake_convert(path, src, dst):
        _ = (path, src, dst)
        calls["convert"] += 1

    def fake_check(path, enc):
        _ = (path, enc)
        calls["check"] += 1
        return []

    monkeypatch.setattr("cutf.controller.fileController.convert_to_utf8_with_iconv", fake_convert)
    monkeypatch.setattr("cutf.controller.fileController.check_illegal_chars", fake_check)

    result = handle_file(str(file_path), _setting(convert=True, extensions=[".py"]))

    assert result.skipped is True
    assert result.converted is False
    assert calls == {"convert": 0, "check": 0}

