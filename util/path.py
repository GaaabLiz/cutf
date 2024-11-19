import os
import shutil
import tempfile


def copy_old_encoded_file(file_path):

    # Controlliamo se il file esiste
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Il file {file_path} non esiste.")

    # Otteniamo la cartella temporanea di Windows (solitamente la variabile d'ambiente TEMP)
    temp_dir = tempfile.gettempdir()

    # Creiamo un percorso per la copia del file nella cartella temporanea
    file_name = os.path.basename(file_path)
    temp_file_path = os.path.join(temp_dir, "SrcChE")

    if not os.path.exists(temp_file_path):
        os.makedirs(temp_file_path)

    # Copiamo il file nella cartella temporanea
    dest = shutil.copy2(file_path, temp_file_path)

    # Restituire il percorso del file temporaneo
    return dest