from collections import Counter
import os

import pytest
from rich.table import Table

from cutf import app


def test_main_requires_operation_flag():
    with pytest.raises(SystemExit) as exc:
        app.main(["--path", "/tmp", "--extensions", ".txt"], confirm_fn=lambda: None)

    assert exc.value.code == 1


def test_main_requires_extensions():
    with pytest.raises(SystemExit) as exc:
        app.main(["--path", "/tmp", "--checks"], confirm_fn=lambda: None)

    assert exc.value.code == 1


def test_main_list_extension_mode_single_file_does_not_require_extensions(monkeypatch):
    captured = {}

    monkeypatch.setattr("cutf.app.os.path.isfile", lambda _: True)
    monkeypatch.setattr("cutf.app.check_path_file", lambda _: None)

    def fail_iconv(_):
        raise AssertionError("iconv should not be checked in list-extension mode")

    def fake_collect_extensions(path, is_file, skip_dirs):
        captured["collect_args"] = (path, is_file, skip_dirs)
        return {app.NO_EXTENSION_LABEL: Counter({"files": 1, app.TEXT_FILE_KIND: 1})}, 1

    def fake_print_extension_table(extension_counts, scanned_files, path):
        captured["counts"] = {
            extension: dict(stats) for extension, stats in extension_counts.items()
        }
        captured["scanned_files"] = scanned_files
        captured["path"] = path

    monkeypatch.setattr("cutf.app.is_command_available", fail_iconv)
    monkeypatch.setattr("cutf.app.collect_extensions", fake_collect_extensions)
    monkeypatch.setattr("cutf.app.print_extension_table", fake_print_extension_table)

    rc = app.main(
        ["--path", "/tmp/README", "--list-extension"],
        confirm_fn=lambda: pytest.fail("confirm_fn should not be called in list-extension mode"),
    )

    assert rc == 0
    assert captured == {
        "collect_args": ("/tmp/README", True, []),
        "counts": {app.NO_EXTENSION_LABEL: {"files": 1, app.TEXT_FILE_KIND: 1}},
        "scanned_files": 1,
        "path": "/tmp/README",
    }


def test_main_requires_iconv(monkeypatch):
    monkeypatch.setattr("cutf.app.os.path.isfile", lambda _: True)
    monkeypatch.setattr("cutf.app.check_path_file", lambda _: None)
    monkeypatch.setattr("cutf.app.is_command_available", lambda _: False)

    with pytest.raises(SystemExit) as exc:
        app.main(["--path", "/tmp/a.txt", "--checks", "--extensions", ".txt"], confirm_fn=lambda: None)

    assert exc.value.code == 1


def test_main_rejects_ai_mode_with_other_operation_flags(monkeypatch):
    monkeypatch.setattr("cutf.app.os.path.isfile", lambda _: True)
    monkeypatch.setattr("cutf.app.check_path_file", lambda _: None)

    with pytest.raises(SystemExit) as exc:
        app.main(
            [
                "--path",
                "/tmp/a.txt",
                "--checks",
                "--fix-wrong-with-ai",
                "--ai-ollama-url",
                "http://localhost:11434",
                "--extensions",
                ".txt",
            ],
            confirm_fn=lambda: None,
        )

    assert exc.value.code == 1


@pytest.mark.parametrize(
    "extra_args",
    [
        ["--checks"],
        ["--extensions", ".txt"],
        ["--verbose"],
        ["--fix-wrong-with-ai", "--ai-ollama-url", "http://localhost:11434"],
    ],
)
def test_main_rejects_list_extension_with_other_flags(monkeypatch, extra_args):
    monkeypatch.setattr("cutf.app.os.path.isfile", lambda _: True)
    monkeypatch.setattr("cutf.app.check_path_file", lambda _: None)

    with pytest.raises(SystemExit) as exc:
        app.main(["--path", "/tmp/a.txt", "--list-extension", *extra_args], confirm_fn=lambda: None)

    assert exc.value.code == 1


def test_main_ai_mode_does_not_require_iconv(monkeypatch):
    called = {"handle": 0, "results": 0}

    monkeypatch.setattr("cutf.app.os.path.isfile", lambda _: True)
    monkeypatch.setattr("cutf.app.check_path_file", lambda _: None)
    monkeypatch.setattr("cutf.app.is_command_available", lambda _: False)

    def fake_handle(path, setting):
        _ = path
        called["handle"] += 1
        assert setting.fix_wrong_with_ai is True
        assert setting.ai_ollama_url == "http://localhost:11434"
        return "ok"

    def fake_print_results(results, setting):
        _ = setting
        called["results"] += 1
        assert results == ["ok"]

    monkeypatch.setattr("cutf.app.handle_file", fake_handle)
    monkeypatch.setattr("cutf.app.print_results", fake_print_results)

    rc = app.main(
        [
            "--path",
            "/tmp/a.txt",
            "--fix-wrong-with-ai",
            "--ai-ollama-url",
            "http://localhost:11434",
            "--extensions",
            ".txt",
        ],
        confirm_fn=lambda: None,
    )

    assert rc == 0
    assert called == {"handle": 1, "results": 1}


def test_resolve_ollama_url_prefers_dotenv_over_process_env(monkeypatch, tmp_path):
    executable_dir = tmp_path / "bin"
    executable_dir.mkdir()
    (executable_dir / ".env").write_text("OLLAMA_URL=http://dotenv:11434\n", encoding="utf-8")

    monkeypatch.setattr("cutf.app.get_executable_directory", lambda: executable_dir)
    monkeypatch.setenv("OLLAMA_URL", "http://process:11434")

    assert app.resolve_ollama_url(None) == "http://dotenv:11434"


def test_resolve_ollama_url_prefers_cli_value(monkeypatch):
    monkeypatch.setenv("OLLAMA_URL", "http://process:11434")

    assert app.resolve_ollama_url("http://cli:11434") == "http://cli:11434"


def test_main_single_file_flow(monkeypatch):
    called = {"handle": 0, "results": 0}

    monkeypatch.setattr("cutf.app.os.path.isfile", lambda _: True)
    monkeypatch.setattr("cutf.app.check_path_file", lambda _: None)
    monkeypatch.setattr("cutf.app.is_command_available", lambda _: True)

    def fake_handle(path, setting):
        _ = (path, setting)
        called["handle"] += 1
        return "ok"

    def fake_print_results(results, setting):
        _ = setting
        called["results"] += 1
        assert results == ["ok"]

    monkeypatch.setattr("cutf.app.handle_file", fake_handle)
    monkeypatch.setattr("cutf.app.print_results", fake_print_results)

    rc = app.main(["--path", "/tmp/a.txt", "--checks", "--extensions", ".txt"], confirm_fn=lambda: None)

    assert rc == 0
    assert called == {"handle": 1, "results": 1}


def test_main_directory_flow(monkeypatch):
    handled_paths = []

    monkeypatch.setattr("cutf.app.os.path.isfile", lambda _: False)
    monkeypatch.setattr("cutf.app.check_path_dir", lambda _: None)
    monkeypatch.setattr("cutf.app.is_command_available", lambda _: True)
    monkeypatch.setattr(
        "cutf.app.os.walk",
        lambda _: [
            ("/tmp/src", ["nested"], ["a.py"]),
            ("/tmp/src/nested", [], ["b.cpp"]),
        ],
    )

    def fake_handle(path, setting):
        _ = setting
        handled_paths.append(path)
        return path

    def fake_print_results(results, setting):
        _ = setting
        assert results == handled_paths

    monkeypatch.setattr("cutf.app.handle_file", fake_handle)
    monkeypatch.setattr("cutf.app.print_results", fake_print_results)

    rc = app.main(["--path", "/tmp/src", "--convert", "--extensions", ".py", ".cpp"], confirm_fn=lambda: None)

    assert rc == 0
    assert handled_paths == [os.path.join("/tmp/src", "a.py"), os.path.join("/tmp/src/nested", "b.cpp")]


def test_main_flattens_skip_dir_values(monkeypatch):
    captured_skip_dirs = []

    monkeypatch.setattr("cutf.app.os.path.isfile", lambda _: True)
    monkeypatch.setattr("cutf.app.check_path_file", lambda _: None)
    monkeypatch.setattr("cutf.app.is_command_available", lambda _: True)

    def fake_handle(path, setting):
        _ = path
        captured_skip_dirs.append(setting.skip_dirs)
        return "ok"

    def fake_print_results(results, setting):
        _ = setting
        assert results == ["ok"]

    monkeypatch.setattr("cutf.app.handle_file", fake_handle)
    monkeypatch.setattr("cutf.app.print_results", fake_print_results)

    rc = app.main(
        [
            "--path",
            "/tmp/a.txt",
            "--checks",
            "--extensions",
            ".txt",
            "--skip-dir",
            ".git",
            "node_modules",
            "--skip-dir",
            ".venv",
        ],
        confirm_fn=lambda: None,
    )

    assert rc == 0
    assert captured_skip_dirs == [[os.path.normcase(".git"), os.path.normcase("node_modules"), os.path.normcase(".venv")]]


def test_main_directory_flow_skips_named_directories(monkeypatch):
    handled_paths = []
    printed_messages = []

    monkeypatch.setattr("cutf.app.os.path.isfile", lambda _: False)
    monkeypatch.setattr("cutf.app.check_path_dir", lambda _: None)
    monkeypatch.setattr("cutf.app.is_command_available", lambda _: True)

    def fake_walk(_):
        dirs = [".git", "nested"]
        yield ("/tmp/src", dirs, ["a.py"])
        if ".git" in dirs:
            yield ("/tmp/src/.git", [], ["ignored.py"])
        if "nested" in dirs:
            yield ("/tmp/src/nested", [], ["b.cpp"])

    def fake_print(*args, **kwargs):
        _ = kwargs
        printed_messages.append(" ".join(str(arg) for arg in args))

    def fake_handle(path, setting):
        _ = setting
        handled_paths.append(path)
        return path

    def fake_print_results(results, setting):
        _ = setting
        assert results == handled_paths

    monkeypatch.setattr("cutf.app.os.walk", fake_walk)
    monkeypatch.setattr("cutf.app.rich.print", fake_print)
    monkeypatch.setattr("cutf.app.handle_file", fake_handle)
    monkeypatch.setattr("cutf.app.print_results", fake_print_results)

    rc = app.main(
        [
            "--path",
            "/tmp/src",
            "--convert",
            "--extensions",
            ".py",
            ".cpp",
            "--skip-dir",
            ".git",
        ],
        confirm_fn=lambda: None,
    )

    assert rc == 0
    assert handled_paths == [os.path.join("/tmp/src", "a.py"), os.path.join("/tmp/src/nested", "b.cpp")]
    assert any(
        "Skipping directory" in message and os.path.join("/tmp/src", ".git") in message
        for message in printed_messages
    )


def test_collect_extensions_skips_named_directories_and_tracks_file_kind(monkeypatch, tmp_path):
    printed_messages = []

    source_dir = tmp_path / "src"
    nested_dir = source_dir / "nested"
    skipped_dir = source_dir / ".git"
    source_dir.mkdir()
    nested_dir.mkdir()
    skipped_dir.mkdir()

    (source_dir / "a.py").write_text("print('ciao')\n", encoding="utf-8")
    (source_dir / "README").write_text("plain text\n", encoding="utf-8")
    (nested_dir / "b.cpp").write_text("int main() { return 0; }\n", encoding="utf-16")
    (nested_dir / "payload.bin").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00")
    (skipped_dir / "ignored.py").write_text("print('skip')\n", encoding="utf-8")

    def fake_print(*args, **kwargs):
        _ = kwargs
        printed_messages.append(" ".join(str(arg) for arg in args))

    monkeypatch.setattr("cutf.app.rich.print", fake_print)

    extension_stats, scanned_files = app.collect_extensions(
        str(source_dir),
        is_file=False,
        skip_dirs=[os.path.normcase(".git")],
    )

    assert {
        extension: dict(stats) for extension, stats in extension_stats.items()
    } == {
        ".py": {"files": 1, app.TEXT_FILE_KIND: 1},
        ".cpp": {"files": 1, app.TEXT_FILE_KIND: 1},
        ".bin": {"files": 1, app.BINARY_FILE_KIND: 1},
        app.NO_EXTENSION_LABEL: {"files": 1, app.TEXT_FILE_KIND: 1},
    }
    assert scanned_files == 4
    assert any(
        "Skipping directory" in message and os.path.join(str(source_dir), ".git") in message
        for message in printed_messages
    )


def test_print_extension_table_uses_rich_table(monkeypatch):
    printed_args = []

    def fake_print(*args, **kwargs):
        _ = kwargs
        printed_args.extend(args)

    monkeypatch.setattr("cutf.app.rich.print", fake_print)

    app.print_extension_table(
        {
            ".py": Counter({"files": 2, app.TEXT_FILE_KIND: 2}),
            ".bin": Counter({"files": 1, app.BINARY_FILE_KIND: 1}),
            ".mix": Counter({"files": 2, app.TEXT_FILE_KIND: 1, app.BINARY_FILE_KIND: 1}),
            app.NO_EXTENSION_LABEL: Counter({"files": 1, app.TEXT_FILE_KIND: 1}),
        },
        6,
        "/tmp/src",
    )

    assert any(isinstance(arg, Table) for arg in printed_args)
    table = next(arg for arg in printed_args if isinstance(arg, Table))
    assert [column.header for column in table.columns] == ["Extension", "Files", "Kind"]
    assert table.columns[0]._cells == [".mix", ".py", app.NO_EXTENSION_LABEL, ".bin"]
    assert table.columns[2]._cells == ["mixed (1 text / 1 binary)", "text", "text", "binary"]
    assert any(
        isinstance(arg, str)
        and arg == "If you want to convert current directory rerun this tool with --convert --extensions .mix .py"
        for arg in printed_args
    )


