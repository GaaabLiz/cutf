import argparse

from loguru import logger


def main():

    # Get CLI params
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', type=str, required=True, help='Path of the file/directory to scan/convert.')
    parser.add_argument('--checks', action='store_true', help='Enable checks for the file')
    parser.add_argument('--convert', action='store_true', help='Enable conversion from current encoding to UTF-8')
    parser.add_argument('--all', action='store_true', help='Enable both conversion and checks')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    args = parser.parse_args()

    # Check CLI params
    if args.checks == False and args.convert == False:
        print("")






if __name__ == "__main__":
    main()
