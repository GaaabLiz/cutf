import argparse
import os

import chardet
import rich

from common import convert_and_check_utf8
from util.checks import check_illegal_chars
from util.log import format_log_error


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True, help='Path of the file to check.')

    args = parser.parse_args()

    # Check path
    if not os.path.exists(args.path):
        rich.print(format_log_error("Path does not exist."))

    # Cycle files
    result_array = []


    for root, dirs, files in os.walk(args.path):
        for file in files:
            try:
                if file.endswith((".cpp", ".h", ".cs", ".ini")):
                    file_path = os.path.join(root, file)
                    # Get encoding
                    with open(file_path, 'rb') as f:
                        raw_data = f.read()
                        result = chardet.detect(raw_data)
                        encoding = result['encoding']
                    result = check_illegal_chars(file_path, encoding, False)
                    result_array.append(result)
            except RuntimeError as e:
                rich.print(format_log_error(e))
    rich.print("\n\n")

    # print results
    comments = list(filter(lambda result: result.is_commented, result_array))
    codes = list(filter(lambda result: result.is_commented == False, result_array))

    rich.print("Missing chars found on commented code:")
    for comment in comments:
        rich.print("\t" + comment)

    rich.print("Missing chars found on compile code:")
    for code in codes:
        rich.print("\t" + code)



if __name__ == "__main__":
    main()
