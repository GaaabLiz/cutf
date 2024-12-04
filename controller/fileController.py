import os

import chardet
import rich

from controller.fileChecker import check_illegal_chars
from model.FileScanResult import FileScanResult
from util.log import format_log_path
from util.path import copy_old_encoded_file


def handle_file(
        file_path: str,
        checks: bool,
        convert: bool,
        copy_old: bool,
        supported_extension: list[str]
) -> FileScanResult:

    # Starting
    file_name = os.path.basename(file_path)
    rich.print(f"## Checking file \"{format_log_path(file_name)}\"...")

    try:
        # Checking extension
        _, extension = os.path.splitext(file_path)
        has_supported_extension = extension in supported_extension
        if not has_supported_extension:
            rich.print(f"File {file_name} has no supported extension ({extension}). Skipping...")
            return FileScanResult(
                file_path=file_path,
                file_name=file_name,
                skipped=True,
            )

        # Load encoding
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']

        # Check encoding
        if encoding is None:
            raise RuntimeError(f"Cannot detect encoding of {file_name}")
        is_already_utf8 = (encoding == "utf-8") or (encoding.lower() == 'utf-8-sig')

        # Check if need to be converted
        needs_convert = is_already_utf8 == False and convert

        # Copy old encoded (if enabled and needed)
        if needs_convert and copy_old:
            old_copy_path = copy_old_encoded_file(file_path)
            rich.print(f"Copied old encoded file to {format_log_path(old_copy_path)}")

        # Exec operations
        if needs_convert:
            output_encoding = "utf-8"
            missing_chars = check_illegal_chars(file_path, encoding)
        elif checks:
            missing_chars = check_illegal_chars(file_path, encoding)
            return FileScanResult(
                file_path=file_path,
                file_name=file_name,
                encoding_before=encoding,
                check_missing_char=missing_chars,
            )
        else:
            rich.print(f"No operation to do on {file_name}")

    except RuntimeError as e:
        rich.print(f"\t[bold red]Conversion/checking of {file_name} interrupted because of an error: {e}[/bold red]")
