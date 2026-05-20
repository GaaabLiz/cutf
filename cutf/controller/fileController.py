import os

import chardet
import rich

from cutf.controller.aiFixController import fix_wrong_chars_with_ai
from cutf.controller.fileChecker import check_illegal_chars
from cutf.model.AppSetting import AppSetting
from cutf.model.FileScanResult import FileScanResult
from cutf.util.iconv import convert_to_utf8_with_iconv
from cutf.util.log import format_log_path
from cutf.util.path import copy_old_encoded_file


def handle_file(file_path: str, setting: AppSetting) -> FileScanResult:
    """Scan and optionally convert a single file according to current settings.

    Args:
        file_path: Full path of the file to process.
        setting: Runtime application options that control checks/conversion behavior.

    Returns:
        FileScanResult: Structured outcome including conversion, checks, and errors.
    """
    # Starting
    file_name = os.path.basename(file_path)
    encoding = None

    try:
        # Checking extension
        _, extension = os.path.splitext(file_path)
        normalized_extensions = {value.lower() for value in setting.extensions}
        has_supported_extension = extension.lower() in normalized_extensions
        if not has_supported_extension:
            if setting.verbose:
                rich.print(f"File {file_name} has no supported extension ({extension}). Skipping...")
            return FileScanResult(
                file_path=file_path,
                file_name=file_name,
                skipped=True,
            )
        # Load encoding
        if setting.verbose:
            rich.print(f"## Checking file \"{format_log_path(file_path)}\"...")

        if setting.verbose:
            rich.print(f"Opening file \"{file_path}\"...")
        with open(file_path, "rb") as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result["encoding"]

        # Check encoding
        if encoding is None:
            raise RuntimeError(f"Cannot detect encoding of {file_name}")
        is_already_utf8 = (
            encoding.lower() in {"utf-8", "utf-8-sig", "utf-16", "utf-16le", "utf-16be"}
        )

        if setting.fix_wrong_with_ai:
            rich.print(
                f"File \"{file_name}\" has encoding {encoding}. Proceeding to interactively fix replacement characters..."
            )
            ai_summary = fix_wrong_chars_with_ai(file_path, encoding, setting)
            if setting.verbose:
                rich.print(f"Finished AI fixing flow for file \"{file_name}\"!")
            return FileScanResult(
                file_path=file_path,
                file_name=file_name,
                encoding_before=encoding,
                check_missing_char=ai_summary.remaining_occurrences,
                skipped=ai_summary.total_missing_chars == 0,
                ai_fix_enabled=True,
                ai_total_missing_chars=ai_summary.total_missing_chars,
                ai_applied_fixes=ai_summary.applied_fixes,
                ai_skipped_fixes=ai_summary.skipped_fixes,
                ai_retry_count=ai_summary.retry_count,
                ai_failed_fixes=ai_summary.failed_fixes,
            )

        # Check if need to be converted
        needs_convert = (not is_already_utf8) and setting.convert

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
            if setting.verbose:
                rich.print(f"Finished checking and converting file \"{file_name}\"!")
            return FileScanResult(
                file_path=file_path,
                file_name=file_name,
                encoding_before=encoding,
                encoding_after=f"{output_encoding}(BOM)",
                check_missing_char=missing_chars,
                converted=True,
            )
        elif setting.checks:
            rich.print(f"File \"{file_name}\" has encoding {encoding}. Proceeding to check...")
            missing_chars = check_illegal_chars(file_path, encoding)
            if setting.verbose:
                rich.print(f"Finished checking file \"{file_name}\"!")
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
                skipped=True,
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
