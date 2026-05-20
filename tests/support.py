import shutil
from contextlib import contextmanager
from pathlib import Path

from tests.fixture_manifest import TEST_DATA_DIR, TEST_OUTPUT_DIR, UTF8_BOM, FixtureCase


ICONV_AVAILABLE = shutil.which("iconv") is not None


@contextmanager
def copied_output_tree():
    if TEST_OUTPUT_DIR.exists():
        shutil.rmtree(TEST_OUTPUT_DIR)

    shutil.copytree(TEST_DATA_DIR, TEST_OUTPUT_DIR, ignore=shutil.ignore_patterns("__pycache__"))
    try:
        yield TEST_OUTPUT_DIR
    finally:
        if TEST_OUTPUT_DIR.exists():
            shutil.rmtree(TEST_OUTPUT_DIR)


def assert_case_content(case: FixtureCase, output_root: Path) -> None:
    output_path = output_root / case.relative_path
    assert output_path.exists(), f"Missing output file: {output_path}"

    data = output_path.read_bytes()
    if case.should_convert:
        assert data.startswith(UTF8_BOM)
        assert data.decode("utf-8-sig") == case.expected_text
        return

    if case.encoding == "utf-8":
        assert not data.startswith(UTF8_BOM)
        assert data.decode("utf-8") == case.expected_text
        return

    if case.encoding == "utf-8-sig":
        assert data.startswith(UTF8_BOM)
        assert data.decode("utf-8-sig") == case.expected_text
        return

    if case.encoding == "utf-16":
        assert data[:2] in {b"\xff\xfe", b"\xfe\xff"}
        assert data.decode("utf-16") == case.expected_text
        return

    raise AssertionError(f"Unhandled fixture encoding for assertions: {case.encoding}")