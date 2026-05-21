from pathlib import Path

from cutf.controller.aiFixController import fix_wrong_chars_with_ai
from cutf.model.AppSetting import AppSetting


def _setting(**kwargs):
    base = dict(
        input_path="/tmp",
        is_file=True,
        extensions=[".txt"],
        checks=False,
        convert=False,
        copy_old_encoded=False,
        print_missing_char_str=False,
        print_skipped_file_no_action=False,
        print_result_only_relevant=False,
        verbose=False,
        fix_wrong_with_ai=True,
        ai_ollama_url="http://localhost:11434",
        ai_model="qwen2.5:1.5b-instruct",
    )
    base.update(kwargs)
    return AppSetting(**base)


def test_fix_wrong_chars_with_ai_applies_change_and_preserves_utf8_bom(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_bytes(b"\xef\xbb\xbf// questo \xef\xbf\xbd un esempio\n")

    prompts = iter(["1"])

    summary = fix_wrong_chars_with_ai(
        str(file_path),
        "utf-8-sig",
        _setting(),
        input_fn=lambda _: next(prompts),
        propose_fn=lambda **_: "e",
    )

    data = file_path.read_bytes()
    assert data.startswith(b"\xef\xbb\xbf")
    assert data.decode("utf-8-sig") == "// questo e un esempio\n"
    assert summary.applied_fixes == 1
    assert summary.failed_fixes == 0
    assert summary.remaining_occurrences == []


def test_fix_wrong_chars_with_ai_preserves_utf16_bom(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("// questo � un esempio\n", encoding="utf-16")

    summary = fix_wrong_chars_with_ai(
        str(file_path),
        "utf-16",
        _setting(),
        input_fn=lambda _: "1",
        propose_fn=lambda **_: "è",
    )

    data = file_path.read_bytes()
    assert data[:2] in {b"\xff\xfe", b"\xfe\xff"}
    assert data.decode("utf-16") == "// questo è un esempio\n"
    assert summary.applied_fixes == 1
    assert summary.remaining_occurrences == []


def test_fix_wrong_chars_with_ai_retries_then_skips(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("// questo � un esempio\n", encoding="utf-8")

    responses = iter(["1", "2"])
    prompts = iter(["2", "3"])

    summary = fix_wrong_chars_with_ai(
        str(file_path),
        "utf-8",
        _setting(),
        input_fn=lambda _: next(prompts),
        propose_fn=lambda **_: next(responses),
    )

    assert file_path.read_text(encoding="utf-8") == "// questo � un esempio\n"
    assert summary.applied_fixes == 0
    assert summary.retry_count == 1
    assert summary.skipped_fixes == 1
    assert len(summary.remaining_occurrences or []) == 1


def test_fix_wrong_chars_with_ai_marks_unencodable_write_as_failure(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_bytes(b"// questo \x80 un esempio\n")

    summary = fix_wrong_chars_with_ai(
        str(file_path),
        "ascii",
        _setting(),
        input_fn=lambda _: "1",
        propose_fn=lambda **_: "è",
    )

    assert summary.applied_fixes == 0
    assert summary.failed_fixes == 1


def test_fix_wrong_chars_with_ai_skips_non_visible_replacement_sequences(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_bytes(b"// questo \xef\xbf\xbd esempio\n")

    summary = fix_wrong_chars_with_ai(
        str(file_path),
        "cp1252",
        _setting(),
        input_fn=lambda _: (_ for _ in ()).throw(AssertionError("input_fn should not be called")),
        propose_fn=lambda **_: (_ for _ in ()).throw(AssertionError("propose_fn should not be called")),
    )

    assert summary.total_missing_chars == 1
    assert summary.applied_fixes == 0
    assert summary.failed_fixes == 0
    assert len(summary.remaining_occurrences or []) == 1
    assert summary.remaining_occurrences[0].char_found is False