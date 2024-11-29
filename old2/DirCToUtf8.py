import argparse
import os

import rich

from old2.common import convert_and_check_utf8
from old2.util.log import format_log_error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True, help='Path of the file to convert.')
    parser.add_argument('--checks', action='store_true', help='Enable checks for the utf8 file')

    args = parser.parse_args()

    # Chiedi conferma all'utente
    confirm = input(f"Your about to replace current encoding to (UTF-8 with BOM) in: {args.path}\nProceed? (y/n): ")
    if confirm.lower() != 'y':
        rich.print("Operation cancelled.")
        return

    # Check path
    if not os.path.exists(args.path):
        rich.print(format_log_error("Path does not exist."))

    # Cycle files
    result_array = []
    for root, dirs, files in os.walk(args.path):
        for file in files:
            if file.endswith((".cpp", ".h", ".cs", ".ini")):
                file_path = os.path.join(root, file)
                result = convert_and_check_utf8(file_path, args.checks)
                result_array.append(result)
    rich.print("\n\n")


    # print encoding before






if __name__ == "__main__":
    main()
