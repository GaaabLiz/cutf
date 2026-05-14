
def format_log_path(path: str) -> str:
    """Format a path string using a rich magenta style token.

    Args:
        path: Path text to format.

    Returns:
        str: Rich-markup styled path.
    """
    return f"[bold magenta]{path}[/bold magenta]"


def format_log_warning(string: str) -> str:
    """Format a warning message using a rich yellow style token.

    Args:
        string: Warning text to format.

    Returns:
        str: Rich-markup styled warning message.
    """
    return f"[bold yellow]{string}[/bold yellow]"


def format_log_error(string: str) -> str:
    """Format an error message using a rich red style token.

    Args:
        string: Error text to format.

    Returns:
        str: Rich-markup styled error message.
    """
    return f"[bold red]{string}[/bold red]"