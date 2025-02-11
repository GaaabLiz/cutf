from dataclasses import dataclass


@dataclass
class AppSetting:
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