import os
import subprocess
import tempfile
from collections import Counter
from dataclasses import dataclass
from logging import exception

import chardet
import rich
import shutil

from rich.text import Text

from rich.console import Console
from rich.text import Text
import os



def check_utf8_new_old(
        old_file_path: str,
        old_file_encoding: str,
        new_file_path: str,
        new_file_encoding: str,
):
    rich.print(f"\tChecking utf-8 file difference from old to new.")
    #rich.print(f"\tOld encoded file: {old_file_path}.")
    #rich.print(f"\tNew encoded file: {new_file_path}.")

    # Funzione per rimuovere il BOM, se presente
    def remove_bom(file_path, encoding):
        with open(file_path, 'rb') as f:
            raw_data = f.read()

        # Verifica se c'è un BOM (per UTF-8 è 0xEF 0xBB 0xBF)
        bom = b'\xef\xbb\xbf'
        if raw_data.startswith(bom):
            raw_data = raw_data[len(bom):]  # Rimuovi il BOM

        # Decodifica il contenuto rimanente
        return raw_data.decode(encoding)

    # Rimuove il BOM dai file, se presente
    contenuto1 = remove_bom(old_file_path, old_file_encoding)
    contenuto2 = remove_bom(new_file_path, new_file_encoding)

    # Controlla la lunghezza dei file per evitare errori durante il confronto
    if len(contenuto1) != len(contenuto2):
        rich.print(f"\t[bold yellow]Files has different lengths[/bold yellow]: {len(contenuto1)} vs {len(contenuto2)}")

    # Confronto carattere per carattere
    #rich.print("\tChecking characters of both files...")
    for i in range(len(contenuto1)):
        if contenuto1[i] != contenuto2[i]:
            rich.print(f"Difference found at position {i}: '{contenuto1[i]}' (file 1) vs '{contenuto2[i]}' (file 2)")
            # test = input("continue?")



@dataclass
class MissingCharResult:
    is_commented: bool
    string: str
    line: int
    file_name: str
    char_position: int
    char_found: bool
    byte_sequence_file_pos: int


def is_line_commented(file_path, line_number):
    in_block_comment = False
    with open(file_path, 'r') as file:
        for current_line_number, line in enumerate(file, start=1):
            # Se siamo nella linea di interesse
            if current_line_number == line_number:
                # Verifica se la linea è commentata
                line = line.strip()
                if in_block_comment:
                    return True  # La riga è dentro un blocco di commento
                # Commenti su singola riga (//)
                if line.startswith("//"):
                    return True
                # Controllo se la riga è dentro un commento di blocco
                if "/*" in line:
                    in_block_comment = True
                    if "*/" in line:
                        in_block_comment = False
                    return False
                return False  # La riga non è commentata
            # Gestisci l'inizio e la fine di un blocco di commento
            if in_block_comment:
                if "*/" in line:
                    in_block_comment = False
                continue
            if "/*" in line:
                in_block_comment = True

    return False  # Se non troviamo mai la linea, significa che non è commentata



def check_illegal_chars(file_path, source_encoding):
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



def check_uft8_illegal_chars(file_path: str, utf8_encoding: str) -> list[MissingCharResult]:
    rich.print(f"\tChecking utf-8 file {os.path.basename(file_path)} for illegal characters...")

    array = check_illegal_chars(file_path, utf8_encoding)
    size = len(array)

    if size > 0:
        rich.print(f"\tFound {size} illegal characters on utf-8 file.")
        #test = input("continue?")

    return array


def convert_encoding_with_iconv(file_path, source_encoding, target_encoding="UTF-8"):
    rich.print(f"\tConverting [bold magenta]{os.path.basename(file_path)}[/bold magenta] da [bold green]{source_encoding} a UTF-8 [/bold green]")
    temp_file_path = file_path + ".tmp"
    temp_bom_file_path = file_path + ".bom"

    array_of_missing = check_illegal_chars(file_path, source_encoding)
    illegal_before: int = len(array_of_missing)

    if illegal_before > 0:
        rich.print(f"\tFound {illegal_before} illegal characters before encoding changes.")
        confirm = input(f"\tContinue converting? [y/N] ")
        if confirm.lower() != 'y':
            rich.print(f"\t[bold yellow]File {os.path.basename(file_path)} skipped![/bold yellow]")
            return

    try:
        command = ["iconv", "-f", source_encoding, "-t", target_encoding, file_path]

        with open(temp_file_path, 'w', encoding=target_encoding) as temp_file:
            subprocess.run(command, stdout=temp_file, stderr=subprocess.PIPE, check=True)

        # Aggiungi il BOM al file convertito
        with open(temp_bom_file_path, 'wb') as bom_file:
            bom_file.write(b'\xef\xbb\xbf')  # Scrivi il BOM (UTF-8)
            with open(temp_file_path, 'rb') as temp_file:
                bom_file.write(temp_file.read())  # Aggiungi il contenuto del file convertito

        # Sostituisci il file originale con il file con BOM
        os.replace(temp_bom_file_path, file_path)
        rich.print(f"\tConversion completed for [bold magenta]{os.path.basename(file_path)}[/bold magenta]")

    except subprocess.CalledProcessError as e:
        rich.print(f"Errore nella conversione di {file_path}: {e}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
    finally:
        # Cancella i file temporanei, se esistono
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        if os.path.exists(temp_bom_file_path):
            os.remove(temp_bom_file_path)


def copy_old_encoded_file(file_path):
    # Controlliamo se il file esiste
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Il file {file_path} non esiste.")

    # Otteniamo la cartella temporanea di Windows (solitamente la variabile d'ambiente TEMP)
    temp_dir = tempfile.gettempdir()

    # Creiamo un percorso per la copia del file nella cartella temporanea
    file_name = os.path.basename(file_path)
    temp_file_path = os.path.join(temp_dir, "CppToUtf8")

    if not os.path.exists(temp_file_path):
        os.makedirs(temp_file_path)

    # Copiamo il file nella cartella temporanea
    dest = shutil.copy2(file_path, temp_file_path)
    rich.print(f"\tCopied file {os.path.basename(file_path)} into {dest}")

    # Restituire il percorso del file temporaneo
    return dest


def handle_file(root: str, file: str) :
    if file.endswith((".cpp", ".h", ".cs", ".ini")):
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

        target_encoding = 'utf-8'

        has_old_encoding = ((encoding == 'windows-1252') or (encoding == 'ISO-8859-1') or (encoding == 'ascii')
                            or (encoding == 'Windows-1252') or (encoding == 'ISO-8859-9') or (encoding == 'MacRoman'))
        is_already_utf8 = (encoding == target_encoding) or (encoding.lower() == 'utf-8-sig')

        if has_old_encoding:
            old_copy_path = copy_old_encoded_file(file_path)
            convert_encoding_with_iconv(file_path, encoding.lower(), 'utf-8')
            #check_utf8_new_old(old_copy_path, encoding, file_path, 'utf-8')
            array_of_missing = check_uft8_illegal_chars(file_path, "utf-8")
            return True, encoding, array_of_missing
        elif is_already_utf8:
            array_of_missing = check_uft8_illegal_chars(file_path, encoding)
            return False, encoding, array_of_missing
        else:
            rich.print(f"\t[bold yellow]File {os.path.basename(file_path)} has not a supported encoding ({encoding}). Skipping.[/bold yellow]")
            return False, encoding, None
        #rich.print(f"File {file} has not supported extension. Skipping.")

    return False, None, None


def main():
    source_dir = input("Choose directory to convert: ")

    if not os.path.isdir(source_dir):
        rich.print("Directory don't exist.")
        return

    file_mask = ("*.cpp", "*.h")
    count_converted = 0
    encodings_found = []
    skipped_files = []
    missing_chars_results = []

    # Chiedi conferma all'utente
    confirm = input(f"Your about to replace current encoding to (UTF-8) in: {source_dir}\nProceed? (y/n): ")
    if confirm.lower() != 'y':
        rich.print("Operazion cancelled.")
        return

    # Scansione dei file .cpp e .h
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            try:
                converted, file_encoding, array_of_missing = handle_file(root, file)
                if converted:
                    count_converted += 1
                encodings_found.append(file_encoding) if file_encoding is not None else None
                if array_of_missing is not None:
                    missing_chars_results.extend(array_of_missing)
            except PermissionError as e:
                rich.print(f"\t[bold red]Conversion of {os.path.basename(file)} interruped because of an error: {e}[/bold red]")
                skipped_files.append(os.path.join(root, file))
            except RuntimeError as e:
                rich.print(f"\t[bold red]Conversion of {os.path.basename(file)} interruped because of an error: {e}[/bold red]")
                skipped_files.append(os.path.join(root, file))
            except UnicodeDecodeError:
                rich.print(f"\t[bold red]Conversion of {os.path.basename(file)} interruped because of an error[/bold red]")
                skipped_files.append(os.path.join(root, file))

    rich.print("\n")
    rich.print(f"Operation completed!! Converted {count_converted} file(s).")

    # Stampo encoding
    encoding_counts = Counter(encodings_found)
    rich.print("\nEncoding before conversions:")
    for encoding, count in encoding_counts.items():
        rich.print(f"[bold green]{encoding}[/bold green]: {count} file")

    # Stampo tutti gli errori file
    rich.print("\nFile skipped because of an error:")
    for file in skipped_files:
        rich.print(f"[bold red]{file}[/bold red]")

    # Calcolo i missing chars nei comment e codice
    missing_chars_on_comments = []
    missing_chars_on_lines = []
    for file in missing_chars_results:
        if file.is_commented and file.char_found:
            missing_chars_on_comments.append(file)
        elif file.is_commented == False:
            missing_chars_on_lines.append(file)

    # Stampo missing char nei commenti
    rich.print(f"\nMissing chars founds on comments ({len(missing_chars_on_comments)}):")
    for file in missing_chars_on_comments:
        rich.print(f"File = {file.file_name} | Missing char Visibile = {file.char_found} | Pos = {file.char_position} | File pos = {file.byte_sequence_file_pos}")
        rich.print(f"String = {file.string}")
        rich.print("-------------------")

    # Stampo missing char nel codice compilabile
    rich.print(f"\nMissing chars founds on code ({len(missing_chars_on_lines)}):")
    for file in missing_chars_on_lines:
        rich.print(f"File = {file.file_name} | Line = {file.line} | Missing char Visibile = {file.char_found} | Pos = {file.char_position} | File pos = {file.byte_sequence_file_pos}")
        rich.print(f"String = {file.string}")
        rich.print("--------------------")



if __name__ == "__main__":
    main()