import os
import subprocess

import rich

from cuft.util.log import format_log_path


def convert_to_utf8_with_iconv(path: str, source_encoding: str, target_encoding: str):
    """Convert a file encoding with iconv and write UTF-8 BOM output in place.

    The function invokes the ``iconv`` executable, writes converted content to a
    temporary file, prepends UTF-8 BOM bytes, and atomically replaces the original file.

    Args:
        path: File path to convert in place.
        source_encoding: Input encoding used by iconv (``-f``).
        target_encoding: Output encoding used by iconv (``-t``), usually ``utf-8``.
    """
    file_name = os.path.basename(path)
    rich.print(f"Converting {file_name} to {target_encoding} with iconv...")

    temp_file_path = path + ".tmp"
    temp_bom_file_path = path + ".bom"

    try:
        command = ["iconv", "-f", source_encoding, "-t", target_encoding, path]

        with open(temp_file_path, "w", encoding=target_encoding) as temp_file:
            subprocess.run(command, stdout=temp_file, stderr=subprocess.PIPE, check=True)

        # Aggiungi il BOM al file convertito
        with open(temp_bom_file_path, "wb") as bom_file:
            bom_file.write(b"\xef\xbb\xbf")  # Scrivi il BOM (UTF-8)
            with open(temp_file_path, "rb") as temp_file:
                bom_file.write(temp_file.read())  # Aggiungi il contenuto del file convertito

        # Sostituisci il file originale con il file con BOM
        os.replace(temp_bom_file_path, path)
        rich.print(f"Conversion completed for {format_log_path(os.path.basename(path))}")

    except subprocess.CalledProcessError as e:
        rich.print(f"Errore nella conversione di {path}: {e}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
    finally:
        # Cancella i file temporanei, se esistono
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if os.path.exists(temp_bom_file_path):
            os.remove(temp_bom_file_path)