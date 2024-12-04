import argparse
import os.path
import rich
from pylizlib.os import pathutils
from controller.fileController import handle_file
from util.log import format_log_error, format_log_path



def main():

    # Get CLI params
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True, help='Path of the file/directory to scan/convert.')
    parser.add_argument('--checks', action='store_true', help='Enable checks for the file')
    parser.add_argument('--convert', action='store_true', help='Enable conversion from current encoding to UTF-8')
    parser.add_argument('--copyOld', action='store_true', help='Copy old encoded file to temp folder before converting.')
    parser.add_argument('--all', action='store_true', help='Enable both conversion and checks')
    parser.add_argument(
        '--extensions',  # Nome dell'argomento
        type=str,  # Tipo stringa
        nargs='+',  # Permette di passare più estensioni separando con uno spazio
        help="List of extension to scan, for example: .cpp .h .cs .ini"
    )
    args = parser.parse_args()

    # Check CLI params
    if args.checks == False and args.convert == False and args.all == False:
        rich.print(format_log_error("At least one of --checks or --convert must be set."))
        exit(1)
    if not args.extensions:
        rich.print(format_log_error("At least one of file extensions must be provided with --extensions."))
        exit(1)

    # Get and Print CLI params
    path = args.path
    enable_checks = True if (args.checks == True or args.all) else False
    enable_convert = True if (args.convert == True or args.all) else False
    rich.print(f"Path to scan: {format_log_path(args.path)}")
    rich.print(f"Checks enabled: {enable_checks}")
    rich.print(f"Conversion enabled: {enable_convert}")
    rich.print(f"Extensions to scan: {args.extensions}")
    rich.print(f"Copy old encoded: {args.copyOld}")
    rich.print("\n")

    # Check path is valid and if it's a dir/file
    is_file = os.path.isfile(path)
    if is_file:
        pathutils.check_path_file(path)
    else:
        pathutils.check_path_dir(path)

    # Handle file/dir and get results
    results = []
    rich.print(f"Scanning \"{format_log_path(path)}\"...")
    if is_file:
        scan_result = handle_file(path, args.checks, args.convert, args.copyOld, args.extensions)
        results.append(scan_result)
    else:
        for root, dirs, files in os.walk(path):
            for file in files:
                scan_result = handle_file(file, args.checks, args.convert, args.copyOld, args.extensions)
                results.append(scan_result)



if __name__ == "__main__":
    main()
