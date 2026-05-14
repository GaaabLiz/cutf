from pathlib import Path

from cuft.util.code import is_line_commented


def test_is_line_commented_single_line_comment(tmp_path: Path):
    file_path = tmp_path / "file.c"
    file_path.write_text("int a = 1;\n// comment\nint b = 2;\n", encoding="utf-8")

    assert is_line_commented(str(file_path), 2) is True
    assert is_line_commented(str(file_path), 1) is False


def test_is_line_commented_inside_block_comment(tmp_path: Path):
    file_path = tmp_path / "file.c"
    file_path.write_text("/*\ninside\n*/\nint x = 0;\n", encoding="utf-8")

    assert is_line_commented(str(file_path), 2) is True
    assert is_line_commented(str(file_path), 4) is False

