# CUFT
Little script to convert the encoding of any text into UTF-8 (With BOM).

## Installation

#### Method 1 (Python)
```bash
pip install cuft
```

#### Method 2 (Download pre-built)
Download the pre-built binaries in release page.

## Requirements
- Iconv installed on your system
  - On Windows, you can install it with [GnuWin](https://gnuwin32.sourceforge.net/packages/libiconv.htm)
 
If you are on Windows you can download the pre-built .exe (but still requires icon v)

## Usage
```bash
usage: cuft [-h] --path PATH [--checks] [--convert] [--copyOld] [--printMissingCharString] [--printAllSkippedFile] [--all] [--verbose] [--only-relevant]
            [--extensions EXTENSIONS [EXTENSIONS ...]]

options:
  -h, --help            show this help message and exit
  --path PATH           Path of the file/directory to scan/convert.
  --checks              Enable checks for the file
  --convert             Enable conversion from current encoding to UTF-8
  --copyOld             Copy old encoded file to temp folder before converting.
  --printMissingCharString
                        Print the string where the missing char has been found
  --printAllSkippedFile
                        Print all the skipped files because no action was required
  --all                 Enable both conversion and checks
  --verbose             Enable extended logging
  --only-relevant       Print only relevant result. (Disable missing chars in comment and missing chars invisible in code)
  --extensions EXTENSIONS [EXTENSIONS ...]
                        List of extension to scan, for example: .cpp .h .cs .ini

```
