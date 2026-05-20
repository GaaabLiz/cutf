# CUTF

cutf is a CLI tool that scans source files, detects legacy encodings, and converts them to **UTF-8 with BOM**.

It can also report replacement characters (`�`) introduced by decoding issues.
It can optionally fix those replacement characters interactively through Ollama while preserving the original file encoding.

## Features

- Scan one file or an entire directory tree.
- Filter files by extension.
- Detect source encoding with `chardet`.
- Convert files to UTF-8 with BOM through `iconv`.
- Interactively repair replacement characters through Ollama without changing file encoding.
- Optional backup copy of original files.
- Detailed report for converted, skipped, and problematic files.

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) *(only for local development)*
- `iconv` available in your system `PATH` when you use conversion mode
- Ollama available when you use `--fix-wrong-with-ai`

### Install `iconv`

- macOS: usually preinstalled (`iconv --version`)
- Linux: install from system package manager (for example `libc-bin` / `glibc` tools)
- Windows: download and install [GNU iconv for Windows (GnuWin32)](https://gnuwin32.sourceforge.net/packages/libiconv.htm) and make sure `iconv.exe` is in `PATH`

## Installation

### Option A – Install from PyPI (recommended)

No need to clone the repository. Just run:

```bash
pip install cutf
```

or with `uv`:

```bash
uv tool install cutf
```

Then use it directly:

```bash
cutf --path ./src --all --extensions .py .txt
```

### Option B – Clone and run locally

#### 1) Clone the repository

```bash
git clone https://github.com/<your-org>/cutf.git
cd cutf
```

#### 2) Create environment and install dependencies with uv

```bash
uv sync --all-groups
```

#### 3) Run cutf

```bash
uv run cutf --path ./src --all --extensions .py .txt
```

## Usage

```text
usage: cutf --path PATH [--checks] [--convert] [--copyOld]
            [--fix-wrong-with-ai] [--ai-ollama-url AI_OLLAMA_URL]
            [--printMissingCharString] [--printAllSkippedFile]
            [--all] [--verbose] [--only-relevant]
            [--extensions EXT [EXT ...]]
```

### Main options

- `--path`: file or directory to process.
- `--checks`: run missing-character checks.
- `--convert`: convert non-UTF files to UTF-8 with BOM.
- `--fix-wrong-with-ai`: interactively replace `�` through Ollama while preserving the file encoding.
- `--ai-ollama-url`: override the Ollama base URL used by AI fix mode.
- `--all`: enable both `--checks` and `--convert`.
- `--extensions`: list of extensions to scan (required), for example `.cpp .h .cs .ini`.
- `--copyOld`: copy original file before conversion into temp folder.
- `--printMissingCharString`: print the line content for each missing-character finding.
- `--printAllSkippedFile`: print every skipped file instead of only the count.
- `--only-relevant`: hide less relevant missing-character entries.
- `--verbose`: print extra execution logs.

### AI Fix Mode

`--fix-wrong-with-ai` is a dedicated mode. It cannot be combined with `--checks`, `--convert`, or `--all`.

When enabled, cutf:

- scans every matching file for `�`
- asks Ollama for a single-character replacement proposal
- shows the wrong line and the proposed corrected line
- lets you choose whether to apply, retry, or skip
- writes the accepted fix back without changing the original encoding or BOM

Ollama URL resolution order:

- `--ai-ollama-url`
- `.env` file next to the executable, using `OLLAMA_URL=...`
- `OLLAMA_URL` from the process environment
- current-user environment on Windows when available

Default model: `qwen2.5:1.5b-instruct`

## Typical Commands

Run checks only:

```bash
uv run cutf --path ./project --checks --extensions .py .js .ts
```

Run conversion + checks:

```bash
uv run cutf --path ./project --all --extensions .cpp .h --copyOld
```

Process one file:

```bash
uv run cutf --path ./src/main.cpp --all --extensions .cpp
```

Run interactive AI fixing:

```bash
OLLAMA_URL=http://localhost:11434 uv run cutf --path ./src --fix-wrong-with-ai --extensions .cpp .py
```

Override the Ollama URL explicitly:

```bash
uv run cutf --path ./src --fix-wrong-with-ai --ai-ollama-url http://localhost:11434 --extensions .cpp
```

## Development

Run tests:

```bash
uv run pytest
```

Run linter:

```bash
uv run ruff check .
```

Format code:

```bash
uv run ruff format .
```

## FAQ

### Why does CUTF require `--extensions`?
It prevents accidental processing of unrelated files and keeps scans predictable.

### Why UTF-8 **with BOM**?
Some tools and Windows-oriented workflows require BOM for UTF-8 detection.

### What happens if `iconv` is missing?
CUTF stops before processing and prints an error only for conversion mode. AI fix mode does not require `iconv`.

### Where are original files copied when `--copyOld` is enabled?
They are copied to `<system-temp>/SrcChE`.

### Does CUTF modify UTF-8 files?
Only when conversion is requested and the file is detected as non-UTF. Otherwise files are skipped.

### Does AI fix mode change the file encoding?
No. Accepted changes are written back using the original encoding and BOM.

## License

This project is distributed under the license in `LICENSE`.

