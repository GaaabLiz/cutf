import os

import rich

from model.MissingCharResult import MissingCharResult
from util.code import is_line_commented


def check_illegal_chars(file_path, source_encoding) -> list[MissingCharResult]:
    results = []
    with open(file_path, 'rb') as f:
        raw_data = f.read()

    # Verifica e gestisci il BOM per UTF-8
    bom = b'\xef\xbb\xbf'
    if raw_data.startswith(bom):
        raw_data = raw_data[len(bom):]  # Rimuovi il BOM

    # Decodifica i byte usando l'encoding specificato (per esempio UTF-8)
    try:
        text_data = raw_data.decode(source_encoding, errors='replace')
    except UnicodeDecodeError as e:
        # Se c'è un errore di decodifica, avvisa l'utente
        rich.print(f"\t[bold red]Error decoding file {os.path.basename(file_path)} with encoding {source_encoding}.[/bold red]")
        raise RuntimeError(f"Error decoding file {os.path.basename(file_path)} during check_illegal_chars().")


    # Itera sui caratteri per trovare il carattere illegale
    for idx in range(len(raw_data) - 2):  # -2 per evitare di uscire fuori dal range durante il confronto
        if raw_data[idx] == 0xEF and raw_data[idx + 1] == 0xBF and raw_data[idx + 2] == 0xBD:
            line_start = text_data.rfind('\n', 0, idx)
            line_end = text_data.find('\n', idx)

            # Ottieni la riga completa dove è presente l'errore
            if line_end == -1:
                line_end = len(text_data)

            line = text_data[line_start + 1:line_end]
            # Trova la posizione relativa all'interno della riga
            char_pos_in_line = line.find('�')

            line_number = text_data.count('\n', 0, idx) + 1

            # Creiamo una versione evidenziata della riga
            #highlighted_line = (line[:char_pos_in_line] +f"[bold red]{line[char_pos_in_line]}[/bold red]" +line[char_pos_in_line + 1:])

            # Stampa il risultato formattato
            rich.print(f"\t[bold yellow]Found illegal character at position {idx}, line {line_number} in file {os.path.basename(file_path)}[/bold yellow]")
            #rich.print("\t" + highlighted_line)

            # Aggiungi il risultato all'array, utilizzando MissingCharResult
            result = MissingCharResult(
                is_commented=is_line_commented(file_path, line_number),
                string=line.lstrip(' \t'),
                line=line_number,
                file_name=os.path.basename(file_path),
                char_position=char_pos_in_line,
                char_found=char_pos_in_line != -1,
                byte_sequence_file_pos=idx
            )

            results.append(result)

    return results