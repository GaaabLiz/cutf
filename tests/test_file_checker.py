from pathlib import Path

from cutf.controller.fileChecker import check_illegal_chars


def test_check_illegal_chars_detects_comment_and_code(tmp_path: Path):
    file_path = tmp_path / "sample.c"
    data = b"\xef\xbb\xbf// bad \xef\xbf\xbd\nvalue = 1; \xef\xbf\xbd\n"
    file_path.write_bytes(data)

    results = check_illegal_chars(str(file_path), "utf-8")

    assert len(results) == 2
    assert results[0].is_commented is True
    assert results[1].is_commented is False
    assert results[0].file_name == "sample.c"

