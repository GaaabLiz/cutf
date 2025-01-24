import argparse
import os.path
import rich
from pylizlib.os import pathutils
from pylizlib.os.osutils import is_command_available_with_run, is_command_available

from controller.fileController import handle_file
from controller.resultHandler import print_results
from model.AppSetting import AppSetting
from util.log import format_log_error, format_log_path



def main():

    # Get CLI params
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True, help='Path of the file/directory to scan/convert.')
    parser.add_argument('--checks', action='store_true', help='Enable checks for the file')
    parser.add_argument('--convert', action='store_true', help='Enable conversion from current encoding to UTF-8')
    parser.add_argument('--copyOld', action='store_true', help='Copy old encoded file to temp folder before converting.')
    parser.add_argument('--printMissingCharString', action='store_true', help='Print the string where the missing char has been found')
    parser.add_argument('--printAllSkippedFile', action='store_true', help='Print all the skipped files because no action was required')
    parser.add_argument('--all', action='store_true', help='Enable both conversion and checks')
    parser.add_argument('--verbose', action='store_true', help='Enable extended logging')
    parser.add_argument('--only-relevant', action='store_true', help='Print only relevant result. (Disable missing chars in comment and missing chars invisible in code)')
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

    # Check iconv in path
    iconv_ok = is_command_available("iconv")
    if not iconv_ok:
        rich.print(format_log_error("Iconv exe not found on your system path!"))
        exit(1)

    # Ask user confirmation
    if is_file:
        rich.print(f"File \"{format_log_path(path)}\" will be checked and converted to UTF-8 (with BOM). Proceed? (Enter to continue or CTRL-C to exit)")
    else:
        rich.print(f"All files inside \"{format_log_path(path)}\" will be checked and converted to UTF-8 (with BOM). Proceed? (Enter to continue or CTRL-C to exit)")
    input()

    # Create setting object
    setting = AppSetting(
        input_path=path,
        is_file = is_file,
        extensions=args.extensions,
        checks=enable_checks,
        convert=enable_convert,
        copy_old_encoded=args.copyOld,
        print_missing_char_str=args.printMissingCharString,
        verbose=args.verbose,
        print_skipped_file_no_action=args.printAllSkippedFile,
        print_result_only_relevant=args.only_relevant,
    )

    # Handle file/dir and get results
    count_from_files = 0
    results = []
    rich.print(f"Scanning \"{format_log_path(path)}\"...")
    if is_file:
        count_from_files += 1
        scan_result = handle_file(setting.input_path, setting)
        results.append(scan_result)
    else:
        for root, dirs, files in os.walk(path):
            for file in files:
                count_from_files += 1
                full_file_path = os.path.join(root, file)
                scan_result = handle_file(full_file_path, setting)
                results.append(scan_result)
    rich.print("-------------------------------")

    # Handle results
    print_results(results, setting)

    # Print count result
    if setting.is_file:
        rich.print(f"\nThis software scanned file {format_log_path(path)}.\n")
    else:
        rich.print(f"\nThis software scanned {len(results)}/{count_from_files} files inside {format_log_path(path)}.\n")


if __name__ == "__main__":
    main()
