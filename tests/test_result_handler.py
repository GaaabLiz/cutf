from cutf.controller.resultHandler import print_results
from cutf.model.AppSetting import AppSetting
from cutf.model.FileScanResult import FileScanResult
from cutf.model.MissingCharResult import MissingCharResult
from rich.table import Table


def test_print_results_runs_without_errors(monkeypatch):
    printed_args = []

    def fake_print(*args, **kwargs):
        _ = kwargs
        printed_args.extend(args)

    monkeypatch.setattr("cutf.controller.resultHandler.rich.print", fake_print)

    missing_code = MissingCharResult(
        is_commented=False,
        comment_context="code",
        string="x � y",
        line=10,
        file_name="a.cpp",
        char_position=2,
        char_found=True,
        byte_sequence_file_pos=15,
    )
    missing_comment = MissingCharResult(
        is_commented=True,
        comment_context="comment",
        string="// note �",
        line=12,
        file_name="a.cpp",
        char_position=8,
        char_found=True,
        byte_sequence_file_pos=40,
    )
    missing_hidden = MissingCharResult(
        is_commented=False,
        comment_context="code",
        string="value = left + right;",
        line=14,
        file_name="a.cpp",
        char_position=-1,
        char_found=False,
        byte_sequence_file_pos=55,
    )
    missing_unsupported = MissingCharResult(
        is_commented=False,
        comment_context="unsupported",
        string="plain � text",
        line=3,
        file_name="note.txt",
        char_position=6,
        char_found=True,
        byte_sequence_file_pos=9,
    )
    results = [
        FileScanResult(
            file_path="/tmp/a.cpp",
            file_name="a.cpp",
            encoding_before="cp1252",
            converted=True,
            encoding_after="utf-8(BOM)",
            check_missing_char=[missing_code, missing_comment, missing_hidden],
            ai_fix_enabled=True,
            ai_total_missing_chars=2,
            ai_applied_fixes=1,
            ai_skipped_fixes=1,
            ai_retry_count=0,
            ai_failed_fixes=0,
        ),
        FileScanResult(file_path="/tmp/b.cpp", file_name="b.cpp", skipped=True),
        FileScanResult(
            file_path="/tmp/note.txt",
            file_name="note.txt",
            error_skipped=True,
            error_description="decode failure",
            check_missing_char=[missing_unsupported],
        ),
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

    tables = [arg for arg in printed_args if isinstance(arg, Table)]

    assert any("START OF RESULTS" in str(arg) for arg in printed_args if isinstance(arg, str))
    assert tables

    tables_by_title = {str(table.title): table for table in tables}
    assert "Encodings found during scanning (1/3 files with detected encoding)" in tables_by_title
    assert "AI fix summary" in tables_by_title
    assert "Converted files" in tables_by_title
    assert "Skipped files" in tables_by_title
    assert "Skipped files from errors" in tables_by_title
    assert "Missing chars found in comments" in tables_by_title
    assert "Missing chars found in code" in tables_by_title
    assert "Missing chars in unsupported comment-analysis files" in tables_by_title

    comment_table = tables_by_title["Missing chars found in comments"]
    assert [column.header for column in comment_table.columns] == [
        "File",
        "Visible",
        "Line",
        "Line Pos",
        "File Pos",
        "String",
    ]
    assert comment_table.columns[0]._cells == ["a.cpp"]
    assert comment_table.columns[5]._cells == ["// note �"]

    code_table = tables_by_title["Missing chars found in code"]
    assert code_table.columns[1]._cells == ["True", "False"]
    assert code_table.columns[3]._cells == ["2", "-1"]

    unsupported_table = tables_by_title["Missing chars in unsupported comment-analysis files"]
    assert unsupported_table.columns[0]._cells == ["note.txt"]

