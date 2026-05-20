import pytest

from cutf import app
from tests.fixture_manifest import FIXTURE_CASES, TEST_OUTPUT_DIR
from tests.support import ICONV_AVAILABLE, assert_case_content, copied_output_tree


def test_fixture_corpus_has_expected_matrix():
    assert len(FIXTURE_CASES) == 36
    assert {case.extension for case in FIXTURE_CASES} == {".py", ".cpp", ".cs"}


@pytest.mark.skipif(not ICONV_AVAILABLE, reason="iconv not available")
def test_main_converts_legacy_sources_in_output_and_cleans_up():
    legacy_cases = [case for case in FIXTURE_CASES if case.should_convert]

    with copied_output_tree() as output_dir:
        rc = app.main(
            ["--path", str(output_dir), "--convert", "--extensions", ".PY", ".Cpp", ".CS"],
            confirm_fn=lambda: None,
        )

        assert rc == 0
        for case in legacy_cases:
            assert_case_content(case, output_dir)

    assert not TEST_OUTPUT_DIR.exists()


@pytest.mark.skipif(not ICONV_AVAILABLE, reason="iconv not available")
def test_main_preserves_current_utf_inputs_in_output_tree():
    skipped_cases = [case for case in FIXTURE_CASES if not case.should_convert]

    with copied_output_tree() as output_dir:
        rc = app.main(
            ["--path", str(output_dir), "--convert", "--extensions", ".py", ".cpp", ".cs"],
            confirm_fn=lambda: None,
        )

        assert rc == 0
        for case in skipped_cases:
            assert_case_content(case, output_dir)

    assert not TEST_OUTPUT_DIR.exists()