from dataclasses import dataclass


@dataclass
class AppSetting:
    """Runtime configuration loaded from CLI flags.

    Attributes:
        input_path: Path of the input file or directory selected by the user.
        is_file: ``True`` when ``input_path`` points to a file, ``False`` for directories.
        extensions: Allowed file extensions to include in the scan.
        checks: Enables illegal-character checks.
        convert: Enables conversion to UTF-8 with BOM when needed.
        copy_old_encoded: Saves a copy of legacy-encoded files before conversion.
        print_missing_char_str: Prints the line text where missing characters are detected.
        print_skipped_file_no_action: Prints all skipped files instead of just a count.
        print_result_only_relevant: Hides less relevant missing-char entries.
        verbose: Enables detailed progress logs.
        fix_wrong_with_ai: Enables interactive AI-assisted replacement of ``�``.
        ai_ollama_url: Resolved Ollama base URL used for AI requests.
        ai_model: Ollama model name used for AI requests.
    """
    input_path: str
    is_file: bool
    extensions: list[str]
    checks: bool = False
    convert: bool = False
    copy_old_encoded: bool = False
    print_missing_char_str: bool = False
    print_skipped_file_no_action: bool = False
    print_result_only_relevant: bool = False
    verbose: bool = False
    fix_wrong_with_ai: bool = False
    ai_ollama_url: str | None = None
    ai_model: str = "qwen2.5:1.5b-instruct"