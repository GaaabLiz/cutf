def is_line_commented(file_path: str, line_number: int) -> bool:
    """Determine whether a specific line is inside a comment block.

    Supports C-like single-line comments (``//``) and block comments
    delimited by ``/*`` and ``*/``.

    Args:
        file_path: Path to the source file.
        line_number: 1-based target line index.

    Returns:
        bool: ``True`` if the line is recognized as commented, otherwise ``False``.
    """
    in_block_comment = False
    with open(file_path, "r", encoding="utf-8", errors="replace") as file:
        for current_line_number, line in enumerate(file, start=1):
            # Se siamo nella linea di interesse
            if current_line_number == line_number:
                # Verifica se la linea e commentata
                line = line.strip().lstrip("\ufeff")
                if in_block_comment:
                    # La riga e dentro un blocco di commento
                    return True
                # Commenti su singola riga (//)
                if line.startswith("//"):
                    return True
                # Controllo se la riga e dentro un commento di blocco
                if "/*" in line:
                    in_block_comment = True
                    if "*/" in line:
                        in_block_comment = False
                    return False
                # La riga non e commentata
                return False
            # Gestisci l'inizio e la fine di un blocco di commento
            if in_block_comment:
                if "*/" in line:
                    in_block_comment = False
                continue
            if "/*" in line:
                in_block_comment = True

    return False  # Se non troviamo mai la linea, significa che non e commentata
