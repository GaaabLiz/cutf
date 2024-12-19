from dataclasses import dataclass

from model.MissingCharResult import MissingCharResult


@dataclass
class FileScanResult:
    file_path: str
    file_name: str
    encoding_before: str | None = None
    encoding_after: str | None = None
    converted: bool = False
    check_missing_char: list[MissingCharResult] | None = None
    error_skipped: bool = False
    error_name: str | None = None
    error_description: str | None = None
    skipped: bool = False