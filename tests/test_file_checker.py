from pathlib import Path

from cutf.controller.fileChecker import check_illegal_chars
from cutf.util.code import COMMENT_CONTEXT_CODE, COMMENT_CONTEXT_COMMENT, COMMENT_CONTEXT_UNSUPPORTED


def test_check_illegal_chars_detects_comment_and_code(tmp_path: Path):
    file_path = tmp_path / "sample.c"
    data = b"\xef\xbb\xbf// bad \xef\xbf\xbd\nvalue = 1; \xef\xbf\xbd\n"
    file_path.write_bytes(data)

    results = check_illegal_chars(str(file_path), "utf-8")

    assert len(results) == 2
    assert results[0].is_commented is True
    assert results[1].is_commented is False
    assert results[0].comment_context == COMMENT_CONTEXT_COMMENT
    assert results[1].comment_context == COMMENT_CONTEXT_CODE
    assert results[0].file_name == "sample.c"


def test_check_illegal_chars_detects_inline_comment_context_on_mixed_cpp_line(tmp_path: Path):
    file_path = tmp_path / "sample.cpp"
    file_path.write_text("if (isAtomSectionId) { // Se param � un section id atom\n", encoding="utf-8")

    results = check_illegal_chars(str(file_path), "utf-8")

    assert len(results) == 1
    assert results[0].comment_context == COMMENT_CONTEXT_COMMENT
    assert results[0].is_commented is True


def test_check_illegal_chars_keeps_comment_markers_inside_strings_as_code(tmp_path: Path):
    file_path = tmp_path / "sample.cpp"
    file_path.write_text('printf("// not a comment �");\nprintf("/* still code � */");\n', encoding="utf-8")

    results = check_illegal_chars(str(file_path), "utf-8")

    assert len(results) == 2
    assert all(result.comment_context == COMMENT_CONTEXT_CODE for result in results)
    assert all(result.is_commented is False for result in results)


def test_check_illegal_chars_marks_python_hash_comments_and_strings_correctly(tmp_path: Path):
    file_path = tmp_path / "sample.py"
    file_path.write_text('value = 1  # comment �\nprint("# not a comment �")\n', encoding="utf-8")

    results = check_illegal_chars(str(file_path), "utf-8")

    assert len(results) == 2
    assert results[0].comment_context == COMMENT_CONTEXT_COMMENT
    assert results[1].comment_context == COMMENT_CONTEXT_CODE


def test_check_illegal_chars_marks_unsupported_extensions_explicitly(tmp_path: Path):
    file_path = tmp_path / "sample.txt"
    file_path.write_text("plain text �\n", encoding="utf-8")

    results = check_illegal_chars(str(file_path), "utf-8")

    assert len(results) == 1
    assert results[0].comment_context == COMMENT_CONTEXT_UNSUPPORTED
    assert results[0].is_commented is False


def test_check_illegal_chars_marks_hidden_raw_replacement_bytes_as_not_visible(tmp_path: Path):
    file_path = tmp_path / "sample.cpp"
    file_path.write_bytes(b"// hidden \xef\xbf\xbd sequence\n")

    results = check_illegal_chars(str(file_path), "cp1252")

    assert len(results) == 1
    assert results[0].char_found is False
    assert results[0].char_position == -1
    assert results[0].comment_context == COMMENT_CONTEXT_COMMENT
    assert results[0].absolute_char_index is None


def test_check_illegal_chars_ignores_utf7_decode_artifacts_without_raw_replacement_bytes(tmp_path: Path):
    file_path = tmp_path / "sample.cpp"
    file_path.write_text("value = left + right;\nmore = one + two;\n", encoding="ascii")

    results = check_illegal_chars(str(file_path), "utf-7")

    assert results == []

