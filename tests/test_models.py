from cutf.model.AppSetting import AppSetting
from cutf.model.FileScanResult import FileScanResult
from cutf.model.MissingCharResult import MissingCharResult


def test_app_setting_defaults():
    setting = AppSetting(input_path="/tmp/sample.txt", is_file=True, extensions=[".txt"])

    assert setting.checks is False
    assert setting.convert is False
    assert setting.copy_old_encoded is False
    assert setting.fix_wrong_with_ai is False
    assert setting.ai_ollama_url is None


def test_missing_char_result_fields():
    result = MissingCharResult(
        is_commented=True,
        string="// bad char",
        line=12,
        file_name="sample.c",
        char_position=3,
        char_found=True,
        byte_sequence_file_pos=42,
        absolute_char_index=42,
    )

    assert result.file_name == "sample.c"
    assert result.line == 12
    assert result.char_found is True


def test_file_scan_result_flags():
    result = FileScanResult(file_path="/tmp/a.cpp", file_name="a.cpp", converted=True)

    assert result.converted is True
    assert result.skipped is False
    assert result.ai_fix_enabled is False

