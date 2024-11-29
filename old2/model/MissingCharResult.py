from dataclasses import dataclass


@dataclass
class MissingCharResult:
    is_commented: bool
    string: str
    line: int
    file_name: str