import os

import rich

from model.MissingCharResult import MissingCharResult
from util.code import is_line_commented
from util.log import format_log_path, format_log_warning


def check_illegal_chars(file_path, source_encoding, is_before_conversion: bool) -> list[MissingCharResult]:

    if source_encoding is None:
        raise RuntimeError(f'Cannot proceed checking illegal chars of file {os.path.basename(file_path)} because encoding is None')

    if is_before_conversion:
        rich.print(f"Checking for illegal character(s) file {format_log_path(file_path)} before conversion...")
    else:
        rich.print(f"Checking for illegal character(s) file {format_log_path(file_path)}...")

    array = []
    with open(file_path, 'rb') as f:
        raw_data = f.read()

    # Verifica e gestisci il BOM per UTF-8
    bom = b'\xef\xbb\xbf'
    if raw_data.startswith(bom):
        raw_data = raw_data[len(bom):]  # Rimuovi il BOM

    # Decodifica i byte usando l'encoding specificato (per esempio UTF-8)
    try:
        text_data = raw_data.decode(source_encoding)
    except UnicodeDecodeError as e:
        # Se c'è un errore di decodifica, avvisa l'utente
        # rich.print(f"\t[bold red]Error decoding file {os.path.basename(file_path)} with encoding {source_encoding}.[/bold red]")
        raise RuntimeError(f"Error decoding file {os.path.basename(file_path)} during check_illegal_chars().")

    missing_chars = []

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

            is_commented = is_line_commented(file_path, line_number)

            # Creiamo una versione evidenziata della riga
            #highlighted_line = (line[:char_pos_in_line] +f"[bold red]{line[char_pos_in_line]}[/bold red]" +line[char_pos_in_line + 1:])

            # Stampa il risultato formattato
            rich.print(format_log_warning(f"Found illegal character at position {idx}, line {line_number} in file {os.path.basename(file_path)}"))
            #rich.print("\t" + highlighted_line)

            # Crea un oggetto MissingCharResult con le informazioni rilevanti
            result = MissingCharResult(
                is_commented=is_commented,
                string=line,
                line=line_number,
                file_name=os.path.basename(file_path),
            )

            # Aggiungi il risultato alla lista
            missing_chars.append(result)

            array.append(idx)

    count = len(array)
    if count > 0:
        rich.print(f"Found {count} illegal characters before encoding changes.")
        confirm = input(f"Continue? [y/N] ")
        if confirm.lower() != 'y':
            raise InterruptedError(f"Conversion of file {os.path.basename(file_path)} interrupted from user during check_illegal_chars().")

    return len(array)