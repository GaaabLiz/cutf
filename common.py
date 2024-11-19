import os
import shutil
import tempfile

import chardet
import rich

from util.checks import check_illegal_chars
from util.iconv import convert_to_utf8_with_iconv
from util.log import format_log_path, format_log_warning
from util.path import copy_old_encoded_file


def convert_and_check_utf8(path: str, checks: bool):

    file_name = os.path.basename(path)
    target_encoding = "utf-8"



    try:
        rich.print("[purple]################################[/purple]")

        rich.print(f"Checking file {format_log_path(path)}...")

        if not os.path.isdir(path):
            raise FileNotFoundError(f"Path {path} is not a directory")

        # Get encoding
        with open(path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']
        rich.print(f"File {format_log_path(file_name)} has {len(raw_data)} bytes, encoding is {encoding}")

        # Check encoding
        if encoding is None:
            raise RuntimeError(f"Cannot detect encoding of {path}")
        is_already_utf8 = (encoding == "utf-8") or (encoding.lower() == 'utf-8-sig')

        # Copy old encoded file
        old_copy_path = copy_old_encoded_file(path)

        # Convert the file
        if not is_already_utf8:
            check_illegal_chars(path, encoding, True) if checks else None
            convert_to_utf8_with_iconv(path, encoding, target_encoding)
        else:
            rich.print(format_log_warning(f"Skipping conversion of {file_name} because it is already UTF-8."))
            check_illegal_chars(path, encoding, False) if checks else None


    except RuntimeError as e:
        rich.print(f"\t[bold red]Conversion of {file_name} interrupted because of an error: {e}[/bold red]")
    except InterruptedError as e:
        rich.print(format_log_warning(f"Conversion of {file_name} interrupted by user"))

    rich.print("[purple]################################[/purple]")