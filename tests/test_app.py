import pytest

from cutf import app


def test_main_requires_operation_flag():
    with pytest.raises(SystemExit) as exc:
        app.main(["--path", "/tmp", "--extensions", ".txt"], confirm_fn=lambda: None)

    assert exc.value.code == 1


def test_main_requires_extensions():
    with pytest.raises(SystemExit) as exc:
        app.main(["--path", "/tmp", "--checks"], confirm_fn=lambda: None)

    assert exc.value.code == 1


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
    assert handled_paths == ["/tmp/src/a.py", "/tmp/src/nested/b.cpp"]


