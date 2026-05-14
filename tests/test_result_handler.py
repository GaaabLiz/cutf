from cutf.controller.resultHandler import print_results
from cutf.model.AppSetting import AppSetting
from cutf.model.FileScanResult import FileScanResult
from cutf.model.MissingCharResult import MissingCharResult


def test_print_results_runs_without_errors(monkeypatch):
    captured = []
    monkeypatch.setattr("cutf.controller.resultHandler.rich.print", lambda *args, **kwargs: captured.append(args))

    missing = MissingCharResult(
        is_commented=False,
        string="x � y",
        line=10,
        file_name="a.cpp",
        char_position=2,
        char_found=True,
        byte_sequence_file_pos=15,
    )
    results = [
        FileScanResult(file_path="/tmp/a.cpp", file_name="a.cpp", encoding_before="cp1252", converted=True, encoding_after="utf-8(BOM)", check_missing_char=[missing]),
        FileScanResult(file_path="/tmp/b.cpp", file_name="b.cpp", skipped=True),
    ]
    setting = AppSetting(
        input_path="/tmp",
        is_file=False,
        extensions=[".cpp"],
        checks=True,
        convert=True,
        print_missing_char_str=True,
        print_skipped_file_no_action=True,
        print_result_only_relevant=False,
        verbose=True,
    )

    print_results(results, setting)

    assert captured
    assert any("START OF RESULTS" in " ".join(map(str, row)) for row in captured)

