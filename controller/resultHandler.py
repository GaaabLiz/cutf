from collections import Counter

import rich

from model.AppSetting import AppSetting
from model.FileScanResult import FileScanResult
from util.log import format_log_error


def __print_encoding_before(results: list[FileScanResult]):
    encoding_counter = Counter()

    # Scorri ogni FileScanResult
    for result in results:
        # Aggiungi l'encoding_before se non è None
        if result.encoding_before:
            encoding_counter[result.encoding_before] += 1

    # Stampa ogni encoding e il numero di occorrenze
    rich.print(f"@ List of encodings found during scanning ({len(encoding_counter.items())}):")
    for encoding, count in encoding_counter.items():
        rich.print(f"{encoding}: {count}")

def __print_converted_files(results: list[FileScanResult]):
    count = 0
    rich.print(f"@ List of converted files:")
    for result in results:
        if result.converted:
            count += 1
            rich.print(f"Converted file {result.file_name} from encoding {result.encoding_before} to encoding {result.encoding_after}.")
    if count == 0:
        rich.print("0 Files converted.")

def __print_skipped_files(results: list[FileScanResult], print_all: bool):
    count = 0
    rich.print(f"@ List of skipped files:")
    if print_all:
        for result in results:
            if result.skipped:
                count += 1
                rich.print(f"File {result.file_name} skipped because no action is required.")
        if count == 0:
            rich.print("0 skipped file founds.")
    else:
        for result in results:
            if result.skipped:
                count += 1
        if count == 0:
            rich.print("0 skipped file founds.")
        else:
            rich.print(f"{count} file skipped because no action was required.")

def __print_skipped_error_files(results: list[FileScanResult]):
    count = 0
    rich.print(f"@ List of skipped files (from errors):")
    for result in results:
        if result.error_skipped:
            count += 1
            rich.print(format_log_error(f"File {result.file_path} skipped because of an error: {result.error_description}"))
    if count == 0:
        rich.print("0 errors founds.")

def __print_missing_chars_on_comments(results: list[FileScanResult], print_mis_char_string: bool):
    rich.print(f"@ List of missing chars found on comments:")
    for result in results:
        if result.check_missing_char is not None:
            for file in result.check_missing_char:
                if file.is_commented:
                    rich.print(f"File = {file.file_name} | Missing char Visibile = {file.char_found} | Line = {file.line} | Line Pos = {file.char_position} | File pos = {file.byte_sequence_file_pos}")
                    if print_mis_char_string:
                        rich.print(f"String = {file.string}")
                        rich.print("-------------------")

def __print_missing_chars_on_code(results: list[FileScanResult], print_mis_char_string: bool, only_relevant: bool):
    rich.print(f"@ List of missing chars found on code:")
    count = 0
    for result in results:
        if result.check_missing_char is not None:
            for file in result.check_missing_char:
                if not file.is_commented:
                    count += 1
                    if file.char_found:
                        rich.print(f"File = {file.file_name} | Missing char Visibile = {file.char_found} | Line = {file.line} | Line Pos = {file.char_position} | File pos = {file.byte_sequence_file_pos}")
                    else:
                        if not only_relevant:
                            rich.print(f"File = {file.file_name} | Missing char Visibile = {file.char_found} | Line = {file.line} | Line Pos = {file.char_position} | File pos = {file.byte_sequence_file_pos}")
                    if print_mis_char_string:
                        rich.print(f"String = {file.string}")
                        rich.print("-------------------")
    if count == 0:
        rich.print("0 missing chars on code founds.")

def print_results(results: list[FileScanResult], setting: AppSetting):

    rich.print("\n\n")

    rich.print("########################################################") if setting.verbose else None
    rich.print("### START OF RESULTS ###################################")
    rich.print("########################################################") if setting.verbose else None

    # Print list of encoding before all
    __print_encoding_before(results)
    rich.print("\n")

    # Print file converted
    __print_converted_files(results)
    rich.print("\n")

    # File skipped
    __print_skipped_files(results, setting.print_skipped_file_no_action)
    rich.print("\n")

    # File skipped (Error)
    __print_skipped_error_files(results)
    rich.print("\n")

    # Missing chars (comments)
    if not setting.print_result_only_relevant:
        __print_missing_chars_on_comments(results, setting.print_missing_char_str)
        rich.print("\n")

    # Missing chars (code)
    __print_missing_chars_on_code(results, setting.print_missing_char_str, setting.print_result_only_relevant)

    rich,print("\n\n")
    rich.print("########################################################") if setting.verbose else None
    rich.print("### END OF RESULTS #####################################")
    rich.print("########################################################")if setting.verbose else None