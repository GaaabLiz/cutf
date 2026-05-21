import argparse
from collections import Counter
import os
import sys
from pathlib import Path
from shutil import which

import rich
from rich.table import Table

from cutf.controller.fileController import handle_file
from cutf.controller.resultHandler import print_results
from cutf.model.AppSetting import AppSetting
from cutf.util.log import format_log_error, format_log_path, format_log_warning

DEFAULT_OLLAMA_MODEL = "qwen2.5:1.5b-instruct"
NO_EXTENSION_LABEL = "(no extension)"


def get_executable_directory() -> Path:
    """Return the directory that should host runtime sidecar files like ``.env``."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(sys.argv[0]).resolve().parent


def load_dotenv_from_executable_directory() -> dict[str, str]:
    """Load simple ``KEY=VALUE`` entries from ``.env`` near the executable."""
    env_path = get_executable_directory() / ".env"
    if not env_path.is_file():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key:
            values[key] = value
    return values


def load_windows_user_environment() -> dict[str, str]:
    """Load current-user environment variables from the Windows registry when available."""
    if os.name != "nt":
        return {}

    try:
        import winreg
    except ImportError:
        return {}

    values: dict[str, str] = {}
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            index = 0
            while True:
                name, value, _ = winreg.EnumValue(key, index)
                values[name] = value
                index += 1
    except OSError:
        return values
    return values


def resolve_ollama_url(cli_value: str | None) -> str | None:
    """Resolve the Ollama base URL from CLI, ``.env``, and environment fallbacks."""
    if cli_value:
        return cli_value.strip()

    dotenv_values = load_dotenv_from_executable_directory()
    dotenv_value = dotenv_values.get("OLLAMA_URL")
    if dotenv_value:
        return dotenv_value.strip()

    env_value = os.environ.get("OLLAMA_URL")
    if env_value:
        return env_value.strip()

    windows_user_value = load_windows_user_environment().get("OLLAMA_URL")
    if windows_user_value:
        return windows_user_value.strip()

    return None


def check_path_file(path: str) -> None:
    """Validate that the provided path exists and is a file.

    Args:
        path: Candidate file path.

    Raises:
        FileNotFoundError: If the path does not exist as a file.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")


def check_path_dir(path: str) -> None:
    """Validate that the provided path exists and is a directory.

    Args:
        path: Candidate directory path.

    Raises:
        NotADirectoryError: If the path does not exist as a directory.
    """
    if not os.path.isdir(path):
        raise NotADirectoryError(f"Directory not found: {path}")


def is_command_available(command: str) -> bool:
    """Check whether an executable is available on PATH.

    Args:
        command: Executable name.

    Returns:
        bool: ``True`` if the command can be resolved via ``PATH``.
    """
    return which(command) is not None


def collect_extensions(path: str, is_file: bool, skip_dirs: list[str]) -> tuple[Counter[str], int]:
    """Collect file-extension counts for the selected file or directory tree.

    Args:
        path: Input file or directory path.
        is_file: ``True`` when ``path`` is a single file.
        skip_dirs: Directory names to prune during recursive walks.

    Returns:
        tuple[Counter[str], int]: Extension counts and number of scanned files.
    """
    extension_counter: Counter[str] = Counter()
    scanned_files = 0

    def add_file(file_name: str) -> None:
        extension = os.path.splitext(file_name)[1].lower() or NO_EXTENSION_LABEL
        extension_counter[extension] += 1

    if is_file:
        scanned_files = 1
        add_file(path)
        return extension_counter, scanned_files

    skip_dir_names = set(skip_dirs)
    for root, dirs, files in os.walk(path):
        skipped_dirs = [dir_name for dir_name in dirs if os.path.normcase(dir_name) in skip_dir_names]
        if skipped_dirs:
            dirs[:] = [dir_name for dir_name in dirs if os.path.normcase(dir_name) not in skip_dir_names]
            for dir_name in skipped_dirs:
                skipped_path = os.path.join(root, dir_name)
                rich.print(f"{format_log_warning('Skipping directory')} {format_log_path(skipped_path)}")
        for file_name in files:
            scanned_files += 1
            add_file(file_name)

    return extension_counter, scanned_files


def print_extension_table(extension_counter: Counter[str], scanned_files: int, path: str) -> None:
    """Print a Rich table with all extensions found under the selected path."""
    table = Table(title=f"Extensions found in {path}")
    table.add_column("Extension", style="cyan")
    table.add_column("Files", justify="right", style="magenta")

    for extension, count in sorted(extension_counter.items(), key=lambda item: (-item[1], item[0])):
        table.add_row(extension, str(count))

    rich.print(table)
    rich.print(f"Files scanned for extension listing: {scanned_files}")
    rich.print(f"Unique extensions found: {len(extension_counter)}")


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser.

    Returns:
        argparse.ArgumentParser: Configured parser for CUFT command-line options.
    """
    # Get CLI params
    parser = argparse.ArgumentParser(
        description=(
            "Scan source files, convert legacy encodings to UTF-8 with BOM, "
            "and interactively fix replacement characters."
        )
    )
    parser.add_argument("--path", type=str, required=True, help="Path of the file/directory to scan/convert.")
    parser.add_argument("--checks", action="store_true", help="Enable checks for the file")
    parser.add_argument("--convert", action="store_true", help="Enable conversion from current encoding to UTF-8")
    parser.add_argument(
        "--fix-wrong-with-ai",
        action="store_true",
        help="Interactively fix replacement characters using Ollama AI without changing file encoding",
    )
    parser.add_argument(
        "--ai-ollama-url",
        type=str,
        help="Override the Ollama base URL used by --fix-wrong-with-ai",
    )
    parser.add_argument("--copyOld", action="store_true", help="Copy old encoded file before converting")
    parser.add_argument(
        "--printMissingCharString",
        action="store_true",
        help="Print the string where the missing char has been found",
    )
    parser.add_argument(
        "--printAllSkippedFile",
        action="store_true",
        help="Print all skipped files where no action was required",
    )
    parser.add_argument("--all", action="store_true", help="Enable both conversion and checks")
    parser.add_argument("--verbose", action="store_true", help="Enable extended logging")
    parser.add_argument(
        "--only-relevant",
        action="store_true",
        help="Print only relevant results (hides less relevant missing-char entries)",
    )
    parser.add_argument(
        "--extensions",
        # Nome dell'argomento
        type=str,
        # Tipo stringa
        nargs="+",
        # Permette di passare piu estensioni separando con uno spazio
        help="List of extensions to scan, for example: .cpp .h .cs .ini",
    )
    parser.add_argument(
        "--skip-dir",
        action="append",
        nargs="+",
        default=[],
        help="Directory names to skip during recursive scans, for example: .git node_modules",
    )
    parser.add_argument(
        "--list-extension",
        action="store_true",
        help="List all file extensions found under --path and print them in a Rich table.",
    )
    return parser


def main(argv: list[str] | None = None, confirm_fn=input) -> int:
    """Run the command-line application.

    Args:
        argv: Optional CLI argument list. When ``None``, arguments are read from ``sys.argv``.
        confirm_fn: Function used to prompt the user before processing files.

    Returns:
        int: Process exit code (``0`` on success).

    Raises:
        SystemExit: If user input is invalid or required system dependencies are missing.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Check CLI params
    if not (args.checks or args.convert or args.all or args.fix_wrong_with_ai or args.list_extension):
        rich.print(format_log_error("At least one operation flag must be set."))
        raise SystemExit(1)
    if args.fix_wrong_with_ai and (args.checks or args.convert or args.all or args.list_extension):
        rich.print(
            format_log_error(
                "--fix-wrong-with-ai cannot be combined with --checks, --convert, --all, or --list-extension."
            )
        )
        raise SystemExit(1)
    if args.list_extension and (args.checks or args.convert or args.all or args.fix_wrong_with_ai):
        rich.print(
            format_log_error(
                "--list-extension cannot be combined with --checks, --convert, --all, or --fix-wrong-with-ai."
            )
        )
        raise SystemExit(1)
    if args.list_extension and any(
        [
            args.ai_ollama_url,
            args.copyOld,
            args.printMissingCharString,
            args.printAllSkippedFile,
            args.verbose,
            args.only_relevant,
            args.extensions,
        ]
    ):
        rich.print(
            format_log_error("--list-extension can only be combined with --path and optional --skip-dir.")
        )
        raise SystemExit(1)
    if not args.list_extension and not args.extensions:
        rich.print(format_log_error("At least one file extension must be provided with --extensions."))
        raise SystemExit(1)

    # Get and Print CLI params
    path = args.path
    enable_checks = bool(args.checks or args.all)
    enable_convert = bool(args.convert or args.all)
    enable_ai_fix = bool(args.fix_wrong_with_ai)
    enable_list_extension = bool(args.list_extension)
    skip_dirs = list(
        dict.fromkeys(
            os.path.normcase(value.strip())
            for values in args.skip_dir
            for value in values
            if value.strip()
        )
    )
    ollama_url = resolve_ollama_url(args.ai_ollama_url) if enable_ai_fix else None

    if enable_ai_fix and not ollama_url:
        rich.print(
            format_log_error(
                "OLLAMA_URL is required for --fix-wrong-with-ai. Pass --ai-ollama-url or define OLLAMA_URL."
            )
        )
        raise SystemExit(1)

    rich.print(f"Path to scan: {format_log_path(path)}")
    rich.print(f"Directories to skip: {skip_dirs}")
    rich.print(f"List extension mode: {enable_list_extension}")
    if not enable_list_extension:
        rich.print(f"Checks enabled: {enable_checks}")
        rich.print(f"Conversion enabled: {enable_convert}")
        rich.print(f"AI fix enabled: {enable_ai_fix}")
        rich.print(f"Extensions to scan: {args.extensions}")
        rich.print(f"Copy old encoded: {args.copyOld}")
    if enable_ai_fix:
        rich.print(f"Ollama URL: {ollama_url}")
        rich.print(f"Ollama model: {DEFAULT_OLLAMA_MODEL}")
    rich.print("\n")

    # Check path is valid and if it's a dir/file
    is_file = os.path.isfile(path)
    if is_file:
        check_path_file(path)
    else:
        check_path_dir(path)

    # Create setting object
    setting = AppSetting(
        input_path=path,
        is_file=is_file,
        extensions=args.extensions or [],
        checks=enable_checks,
        convert=enable_convert,
        copy_old_encoded=args.copyOld,
        print_missing_char_str=args.printMissingCharString,
        verbose=args.verbose,
        print_skipped_file_no_action=args.printAllSkippedFile,
        print_result_only_relevant=args.only_relevant,
        skip_dirs=skip_dirs,
        fix_wrong_with_ai=enable_ai_fix,
        ai_ollama_url=ollama_url,
        ai_model=DEFAULT_OLLAMA_MODEL,
        list_extension=enable_list_extension,
    )

    if setting.list_extension:
        extension_counter, scanned_files = collect_extensions(setting.input_path, setting.is_file, setting.skip_dirs)
        print_extension_table(extension_counter, scanned_files, setting.input_path)
        return 0

    # Check iconv in path
    if not enable_ai_fix and not is_command_available("iconv"):
        rich.print(format_log_error("Iconv executable not found on your system PATH."))
        raise SystemExit(1)

    # Ask user confirmation
    if enable_ai_fix and is_file:
        rich.print(
            f"File \"{format_log_path(path)}\" will be scanned for replacement characters and fixed interactively "
            "with Ollama. Proceed? (Enter to continue or CTRL-C to exit)"
        )
    elif enable_ai_fix:
        rich.print(
            f"All files inside \"{format_log_path(path)}\" will be scanned for replacement characters and fixed "
            "interactively with Ollama. Proceed? (Enter to continue or CTRL-C to exit)"
        )
    elif is_file:
        rich.print(
            f"File \"{format_log_path(path)}\" will be checked and converted to UTF-8 "
            "(with BOM). Proceed? (Enter to continue or CTRL-C to exit)"
        )
    else:
        rich.print(
            f"All files inside \"{format_log_path(path)}\" will be checked and converted "
            "to UTF-8 (with BOM). Proceed? (Enter to continue or CTRL-C to exit)"
        )
    confirm_fn()

    # Handle file/dir and get results
    count_from_files = 0
    results = []
    rich.print(f"Scanning \"{format_log_path(path)}\"...")
    if is_file:
        count_from_files += 1
        results.append(handle_file(setting.input_path, setting))
    else:
        skip_dir_names = set(setting.skip_dirs)
        for root, dirs, files in os.walk(path):
            skipped_dirs = [dir_name for dir_name in dirs if os.path.normcase(dir_name) in skip_dir_names]
            if skipped_dirs:
                dirs[:] = [dir_name for dir_name in dirs if os.path.normcase(dir_name) not in skip_dir_names]
                for dir_name in skipped_dirs:
                    skipped_path = os.path.join(root, dir_name)
                    rich.print(
                        f"{format_log_warning('Skipping directory')} {format_log_path(skipped_path)}"
                    )
            for file_name in files:
                count_from_files += 1
                full_file_path = os.path.join(root, file_name)
                results.append(handle_file(full_file_path, setting))

    rich.print("-------------------------------")

    # Handle results
    print_results(results, setting)

    # Print count result
    if setting.is_file:
        rich.print(f"\nThis software scanned file {format_log_path(path)}.\n")
    else:
        rich.print(
            f"\nThis software scanned {len(results)}/{count_from_files} files inside "
            f"{format_log_path(path)}.\n"
        )

    return 0


if __name__ == "__main__":
    main()
