from dataclasses import dataclass


@dataclass
class MissingCharResult:
    is_commented: bool
    string: str
    line: int
    file_name: str
    char_position: int
    char_found: bool
    byte_sequence_file_pos: int