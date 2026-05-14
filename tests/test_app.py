import pytest

from cuft import app


def test_main_requires_operation_flag():
    with pytest.raises(SystemExit) as exc:
        app.main(["--path", "/tmp", "--extensions", ".txt"], confirm_fn=lambda: None)

    assert exc.value.code == 1


def test_main_requires_extensions():
    with pytest.raises(SystemExit) as exc:
        app.main(["--path", "/tmp", "--checks"], confirm_fn=lambda: None)

    assert exc.value.code == 1


def test_main_requires_iconv(monkeypatch):
    monkeypatch.setattr("cuft.app.os.path.isfile", lambda _: True)
    monkeypatch.setattr("cuft.app.check_path_file", lambda _: None)
    monkeypatch.setattr("cuft.app.is_command_available", lambda _: False)

    with pytest.raises(SystemExit) as exc:
        app.main(["--path", "/tmp/a.txt", "--checks", "--extensions", ".txt"], confirm_fn=lambda: None)

    assert exc.value.code == 1


def test_main_single_file_flow(monkeypatch):
    called = {"handle": 0, "results": 0}

    monkeypatch.setattr("cuft.app.os.path.isfile", lambda _: True)
    monkeypatch.setattr("cuft.app.check_path_file", lambda _: None)
    monkeypatch.setattr("cuft.app.is_command_available", lambda _: True)

    def fake_handle(path, setting):
        _ = (path, setting)
        called["handle"] += 1
        return "ok"

    def fake_print_results(results, setting):
        _ = setting
        called["results"] += 1
        assert results == ["ok"]

    monkeypatch.setattr("cuft.app.handle_file", fake_handle)
    monkeypatch.setattr("cuft.app.print_results", fake_print_results)

    rc = app.main(["--path", "/tmp/a.txt", "--checks", "--extensions", ".txt"], confirm_fn=lambda: None)

    assert rc == 0
    assert called == {"handle": 1, "results": 1}


