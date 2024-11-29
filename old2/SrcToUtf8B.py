import argparse
from old2.common import convert_and_check_utf8


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True, help='Path of the file to convert.')
    parser.add_argument('--checks', action='store_true', help='Enable checks for the utf8 file')

    args = parser.parse_args()


    convert_and_check_utf8(args.path, args.checks)



if __name__ == "__main__":
    main()
