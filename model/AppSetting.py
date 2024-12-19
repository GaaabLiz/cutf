from dataclasses import dataclass


@dataclass
class AppSetting:
    path: str
    extensions: list[str]
    checks: bool = False
    convert: bool = False
    copy_old_encoded: bool = False
    print_missing_char_str: bool = False
    verbose: bool = False