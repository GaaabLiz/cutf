from dataclasses import dataclass


@dataclass
class MissingCharResult:
    """Details about one replacement-character occurrence in a file.

    Attributes:
        is_commented: ``True`` if the detected character is inside a comment.
        comment_context: Comment classification for the detected character.
            Supported values are ``comment``, ``code``, and ``unsupported``.
        string: Original line content where the issue was found.
        line: 1-based line number in the file.
        file_name: Name of the file that contains the issue.
        char_position: Character index of ``�`` inside the line, or ``-1`` when not visible.
        char_found: ``True`` when the replacement character is visible in decoded text.
        byte_sequence_file_pos: Byte index in the raw file where ``EF BF BD`` starts.
        absolute_char_index: Absolute character offset in the decoded text.
    """
    is_commented: bool
    string: str
    line: int
    file_name: str
    char_position: int
    char_found: bool
    byte_sequence_file_pos: int
    comment_context: str = "code"
    absolute_char_index: int | None = None