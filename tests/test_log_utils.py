from cutf.util.log import format_log_error, format_log_path, format_log_warning


def test_format_log_path():
    assert format_log_path("a/b") == "[bold magenta]a/b[/bold magenta]"


def test_format_log_warning():
    assert format_log_warning("warn") == "[bold yellow]warn[/bold yellow]"


def test_format_log_error():
    assert format_log_error("err") == "[bold red]err[/bold red]"

