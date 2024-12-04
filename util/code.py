import re

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