import os

import chardet
import rich

from controller.fileChecker import check_illegal_chars
from model.AppSetting import AppSetting
from model.FileScanResult import FileScanResult
from util.iconv import convert_to_utf8_with_iconv
from util.log import format_log_path
from util.path import copy_old_encoded_file


def handle_file(file_path, setting: AppSetting) -> FileScanResult:

    # Starting
    file_name = os.path.basename(file_path)
    encoding = None

    try:
        # Checking extension
        _, extension = os.path.splitext(file_path)
        has_supported_extension = extension.lower() in setting.extensions
        if not has_supported_extension:
            rich.print(f"File {file_name} has no supported extension ({extension}). Skipping...") if setting.verbose else None
            return FileScanResult(
                file_path=file_path,
                file_name=file_name,
                skipped=True,
            )
        rich.print(f"## Checking file \"{format_log_path(file_path)}\"...") if setting.verbose else None

        # Load encoding
        rich.print(f"Opening file \"{file_path}\"...") if setting.verbose else None
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']

        # Check encoding
        if encoding is None:
            raise RuntimeError(f"Cannot detect encoding of {file_name}")
        is_already_utf8 = (encoding == "utf-8") or (encoding.lower() == 'utf-8-sig') or (encoding == "utf-16")

        # Check if need to be converted
        needs_convert = is_already_utf8 == False and setting.convert

        # Copy old encoded (if enabled and needed)
        if needs_convert and setting.copy_old_encoded:
            old_copy_path = copy_old_encoded_file(file_path)
            rich.print(f"Copied old encoded file to {format_log_path(old_copy_path)}")

        # Exec operations
        if needs_convert:
            rich.print(f"File \"{file_name}\" has encoding {encoding}. Proceeding to convert and check...")
            output_encoding = "utf-8"
            convert_to_utf8_with_iconv(file_path, encoding, output_encoding)
            missing_chars = check_illegal_chars(file_path, output_encoding)
            rich.print(f"Finished checking and converting file \"{file_name}\"!") if setting.verbose else None
            return FileScanResult(
                file_path=file_path,
                file_name=file_name,
                encoding_before=encoding,
                encoding_after=output_encoding + "(BOM)",
                check_missing_char=missing_chars,
                converted=True,
            )
        elif setting.checks:
            rich.print(f"File \"{file_name}\" has encoding {encoding}. Proceeding to check...")
            missing_chars = check_illegal_chars(file_path, encoding)
            rich.print(f"Finished checking file \"{file_name}\"!") if setting.verbose else None
            return FileScanResult(
                file_path=file_path,
                file_name=file_name,
                encoding_before=encoding,
                check_missing_char=missing_chars,
            )
        else:
            rich.print(f"No operation to do on {file_name}")
            return FileScanResult(
                file_path=file_path,
                file_name=file_name,
                skipped=True
            )

    except RuntimeError as e:
        rich.print(f"[bold red]Conversion/checking of {file_name} interrupted because of an error: {e}[/bold red]")
        return FileScanResult(
                file_path=file_path,
                file_name=file_name,
                encoding_before=encoding,
                error_skipped=True,
                error_description=str(e),
            )
    # except FileNotFoundError as e:
    #     rich.print(f"[bold red]Conversion/checking of {file_name} interrupted because of an error: {e}[/bold red]")
    #     return FileScanResult(
    #         file_path=file_path,
    #         file_name=file_name,
    #         encoding_before=encoding,
    #         error_skipped=True,
    #         error_description=str(e),
    #     )
