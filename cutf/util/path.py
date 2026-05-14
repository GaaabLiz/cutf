import os
import shutil
import tempfile


def copy_old_encoded_file(file_path: str) -> str:
    """Copy a source file to the system temp backup folder.

    The destination folder is ``<tempdir>/SrcChE`` and is created on demand.

    Args:
        file_path: Path of the file that should be copied.

    Returns:
        str: Full path of the copied backup file.

    Raises:
        FileNotFoundError: If ``file_path`` does not exist.
    """

    # Controlliamo se il file esiste
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File {file_path} does not exist.")

    # Otteniamo la cartella temporanea di Windows (solitamente la variabile d'ambiente TEMP)
    temp_dir = tempfile.gettempdir()

    # Creiamo un percorso per la copia del file nella cartella temporanea
    temp_file_path = os.path.join(temp_dir, "SrcChE")

    if not os.path.exists(temp_file_path):
        os.makedirs(temp_file_path)

    # Copiamo il file nella cartella temporanea
    dest = shutil.copy2(file_path, temp_file_path)

    # Restituire il percorso del file temporaneo
    return dest