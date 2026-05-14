from pathlib import Path

import pytest

from cuft.util.path import copy_old_encoded_file


def test_copy_old_encoded_file_success(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("content", encoding="utf-8")

    copied_path = copy_old_encoded_file(str(source))
    copied = Path(copied_path)

    assert copied.exists()
    assert copied.read_text(encoding="utf-8") == "content"


def test_copy_old_encoded_file_missing(tmp_path: Path):
    missing = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        copy_old_encoded_file(str(missing))

