import argparse
import os
from shutil import which

import rich

from cutf.controller.fileController import handle_file
from cutf.controller.resultHandler import print_results
from cutf.model.AppSetting import AppSetting
from cutf.util.log import format_log_error, format_log_path


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


def build_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser.

    Returns:
        argparse.ArgumentParser: Configured parser for CUFT command-line options.
    """
    # Get CLI params
    parser = argparse.ArgumentParser(
        description="Convert source files from legacy encodings to UTF-8 with BOM."
    )
    parser.add_argument("--path", type=str, required=True, help="Path of the file/directory to scan/convert.")
    parser.add_argument("--checks", action="store_true", help="Enable checks for the file")
    parser.add_argument("--convert", action="store_true", help="Enable conversion from current encoding to UTF-8")
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
    if not (args.checks or args.convert or args.all):
        rich.print(format_log_error("At least one of --checks or --convert must be set."))
        raise SystemExit(1)
    if not args.extensions:
        rich.print(format_log_error("At least one file extension must be provided with --extensions."))
        raise SystemExit(1)

    # Get and Print CLI params
    path = args.path
    enable_checks = bool(args.checks or args.all)
    enable_convert = bool(args.convert or args.all)

    rich.print(f"Path to scan: {format_log_path(path)}")
    rich.print(f"Checks enabled: {enable_checks}")
    rich.print(f"Conversion enabled: {enable_convert}")
    rich.print(f"Extensions to scan: {args.extensions}")
    rich.print(f"Copy old encoded: {args.copyOld}")
    rich.print("\n")

    # Check path is valid and if it's a dir/file
    is_file = os.path.isfile(path)
    if is_file:
        check_path_file(path)
    else:
        check_path_dir(path)

    # Check iconv in path
    if not is_command_available("iconv"):
        rich.print(format_log_error("Iconv executable not found on your system PATH."))
        raise SystemExit(1)

    # Ask user confirmation
    if is_file:
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

    # Create setting object
    setting = AppSetting(
        input_path=path,
        is_file=is_file,
        extensions=args.extensions,
        checks=enable_checks,
        convert=enable_convert,
        copy_old_encoded=args.copyOld,
        print_missing_char_str=args.printMissingCharString,
        verbose=args.verbose,
        print_skipped_file_no_action=args.printAllSkippedFile,
        print_result_only_relevant=args.only_relevant,
    )

    # Handle file/dir and get results
    count_from_files = 0
    results = []
    rich.print(f"Scanning \"{format_log_path(path)}\"...")
    if is_file:
        count_from_files += 1
        results.append(handle_file(setting.input_path, setting))
    else:
        for root, _, files in os.walk(path):
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
