import os
import subprocess
from logging import exception

import chardet
import rich
import shutil

from rich.text import Text

from rich.console import Console
from rich.text import Text
import os



def check_illegal_chars(file_path, source_encoding):
    array = []
    with open(file_path, 'rb') as f:
        raw_data = f.read()

    # Decodifica i byte usando l'encoding specificato (per esempio UTF-8)
    try:
        text_data = raw_data.decode(source_encoding)
    except UnicodeDecodeError as e:
        # Se c'è un errore di decodifica, avvisa l'utente
        rich.print(f"\t[bold red]Error decoding file {os.path.basename(file_path)} with encoding {source_encoding}.[/bold red]")
        raise RuntimeError(f"Error decoding file {os.path.basename(file_path)} during check_illegal_chars().")


    # Itera sui caratteri per trovare il carattere illegale
    for idx, char in enumerate(raw_data):
        if char == 0xEF:  # Byte di inizio del carattere '�' (replacement character, UTF-8)
            line_start = text_data.rfind('\n', 0, idx)
            line_end = text_data.find('\n', idx)

            # Ottieni la riga completa dove è presente l'errore
            if line_end == -1:
                line_end = len(text_data)

            line = text_data[line_start + 1:line_end]
            # Trova la posizione relativa all'interno della riga
            char_pos_in_line = idx - line_start - 1

            line_number = text_data.count('\n', 0, idx) + 1

            # Creiamo una versione evidenziata della riga
            highlighted_line = (
                    line[:char_pos_in_line] +
                    f"[bold red]{line[char_pos_in_line]}[/bold red]" +
                    line[char_pos_in_line + 1:]
            )

            # Stampa il risultato formattato
            rich.print(f"\t[bold yellow]Found illegal character at position {idx}, line {line_number} in file {os.path.basename(file_path)}[/bold yellow]")
            rich.print("\t" + highlighted_line)

            array.append(idx)
    return len(array)




def convert_encoding_with_iconv(file_path, source_encoding, target_encoding="UTF-8"):
    temp_file_path = file_path + ".tmp"

    illegal_before: int = check_illegal_chars(file_path, source_encoding)
    rich.print(f"\tFound {illegal_before} illegal characters before encoding changes.")

    if illegal_before > 0:
        confirm = input(f"\tContinue converting? [y/N] ")
        if confirm.lower() != 'y':
            rich.print(f"\t[bold yellow]File {os.path.basename(file_path)} skipped![/bold yellow]")
            return

    try:
        # Esegui il comando iconv per la conversione
        command = ["iconv", "-f", source_encoding, "-t", target_encoding, file_path]
        with open(temp_file_path, 'w', encoding=target_encoding) as temp_file:
            subprocess.run(command, stdout=temp_file, stderr=subprocess.PIPE, check=True)
            # Sostituisci il file originale con il file convertito
        os.replace(temp_file_path, file_path)
        rich.print(f"\tConversion completed for [bold magenta]{os.path.basename(file_path)}[/bold magenta]")

    except subprocess.CalledProcessError as e:
        rich.print(f"Errore nella conversione di {file_path}: {e}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    illegal_after: int = check_illegal_chars(file_path, target_encoding)
    rich.print(f"\tFound {illegal_after} illegal characters after encoding changes.")

    if illegal_after > 0:
        rich.print(f"\t[bold yellow]File {os.path.basename(file_path)} contains some illegal chars after conversion![/bold yellow]")



def handle_file(root: str, file: str):
    if file.endswith((".cpp", ".h")):
        file_path = os.path.join(root, file)

        # Rileva l'encoding del file
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding']

        rich.print(f"Analyzing file [bold magenta]\"{file_path}\"[/bold magenta]. Current encoding is [bold green]{encoding}[/bold green]")

        if encoding is None:
            rich.print(f"\tCannot detect encoding of {file_path}")
            raise RuntimeError(f"\tCannot detect encoding of {file_path}")

        if (encoding == 'windows-1252') or (encoding == 'ISO-8859-1'):
            rich.print(f"\tConverting [bold magenta]{os.path.basename(file_path)}[/bold magenta] da [bold green]{encoding} a UTF-8 [/bold green]")
            convert_encoding_with_iconv(file_path, encoding.lower(), 'utf-8')
        else:
            rich.print(f"\t[bold yellow]File {file_path} is not Windows-1252 or ISO-8859-1. Skipping.[/bold yellow]")
    else:
        rich.print(f"File {file} has not supported extension. Skipping.")

def main():
    source_dir = input("Choose directory to convert: ")

    if not os.path.isdir(source_dir):
        rich.print("Directory don't exist.")
        return

    file_mask = ("*.cpp", "*.h")

    # Chiedi conferma all'utente
    confirm = input(f"Your about to replace current encoding to (UTF-8) in: {source_dir}\nProceed? (y/n): ")
    if confirm.lower() != 'y':
        rich.print("Operazion cancelled.")
        return

    # Scansione dei file .cpp e .h
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            try:
                handle_file(root, file)
            except PermissionError as e:
                rich.print(f"\t[bold red]Conversion of {os.path.basename(file)} interruped because of an error: {e}[/bold red]")
            except RuntimeError as e:
                rich.print(f"\t[bold red]Conversion of {os.path.basename(file)} interruped because of an error: {e}[/bold red]")

    rich.print("Operation completed!!")

if __name__ == "__main__":
    main()