from pathlib import Path
from typing import Iterable


COMMENT_CONTEXT_CODE = "code"
COMMENT_CONTEXT_COMMENT = "comment"
COMMENT_CONTEXT_UNSUPPORTED = "unsupported"

C_LIKE_COMMENT_EXTENSIONS = {".c", ".cs", ".cpp", ".h", ".hpp"}
PYTHON_COMMENT_EXTENSIONS = {".py"}
SUPPORTED_COMMENT_EXTENSIONS = C_LIKE_COMMENT_EXTENSIONS | PYTHON_COMMENT_EXTENSIONS


def _normalize_positions(text: str, absolute_positions: Iterable[int]) -> list[int]:
    """Return sorted unique positions that fall inside ``text`` bounds."""
    return sorted({position for position in absolute_positions if 0 <= position < len(text)})


def _classify_c_like_contexts(text: str, absolute_positions: list[int]) -> dict[int, str]:
    """Classify positions for languages that use ``//`` and ``/* */`` comments."""
    contexts: dict[int, str] = {}
    if not absolute_positions:
        return contexts

    in_line_comment = False
    in_block_comment = False
    string_quote: str | None = None
    escape_active = False
    target_index = 0
    index = 0
    text_length = len(text)

    while index < text_length and target_index < len(absolute_positions):
        while target_index < len(absolute_positions) and absolute_positions[target_index] == index:
            contexts[index] = (
                COMMENT_CONTEXT_COMMENT if in_line_comment or in_block_comment else COMMENT_CONTEXT_CODE
            )
            target_index += 1

        current_char = text[index]
        next_char = text[index + 1] if index + 1 < text_length else ""

        if in_line_comment:
            if current_char == "\n":
                in_line_comment = False
            index += 1
            continue

        if in_block_comment:
            if current_char == "*" and next_char == "/":
                in_block_comment = False
                index += 2
                continue
            index += 1
            continue

        if string_quote is not None:
            if escape_active:
                escape_active = False
            elif current_char == "\\":
                escape_active = True
            elif current_char == string_quote:
                string_quote = None
            index += 1
            continue

        if current_char == "/" and next_char == "/":
            in_line_comment = True
            index += 2
            continue

        if current_char == "/" and next_char == "*":
            in_block_comment = True
            index += 2
            continue

        if current_char in {'"', "'"}:
            string_quote = current_char
            escape_active = False
            index += 1
            continue

        index += 1

    return contexts


def _classify_python_contexts(text: str, absolute_positions: list[int]) -> dict[int, str]:
    """Classify positions for Python files using ``#`` comments."""
    contexts: dict[int, str] = {}
    if not absolute_positions:
        return contexts

    in_comment = False
    string_quote: str | None = None
    triple_quoted = False
    escape_active = False
    target_index = 0
    index = 0
    text_length = len(text)

    while index < text_length and target_index < len(absolute_positions):
        while target_index < len(absolute_positions) and absolute_positions[target_index] == index:
            contexts[index] = COMMENT_CONTEXT_COMMENT if in_comment else COMMENT_CONTEXT_CODE
            target_index += 1

        current_char = text[index]

        if in_comment:
            if current_char == "\n":
                in_comment = False
            index += 1
            continue

        if string_quote is not None:
            if triple_quoted and text.startswith(string_quote * 3, index):
                string_quote = None
                triple_quoted = False
                escape_active = False
                index += 3
                continue

            if not triple_quoted:
                if escape_active:
                    escape_active = False
                elif current_char == "\\":
                    escape_active = True
                elif current_char == string_quote:
                    string_quote = None
                index += 1
                continue

            index += 1
            continue

        if current_char == "#":
            in_comment = True
            index += 1
            continue

        if current_char in {'"', "'"}:
            if text.startswith(current_char * 3, index):
                string_quote = current_char
                triple_quoted = True
                escape_active = False
                index += 3
                continue

            string_quote = current_char
            triple_quoted = False
            escape_active = False
            index += 1
            continue

        index += 1

    return contexts


def classify_comment_contexts(file_path: str, text: str, absolute_positions: Iterable[int]) -> dict[int, str]:
    """Classify selected positions as ``comment``, ``code``, or ``unsupported``.

    Args:
        file_path: Source file path used only to derive the extension.
        text: Decoded file content.
        absolute_positions: Character offsets to classify within ``text``.

    Returns:
        dict[int, str]: Mapping from absolute position to one of the
        ``COMMENT_CONTEXT_*`` constants.
    """
    positions = _normalize_positions(text, absolute_positions)
    if not positions:
        return {}

    extension = Path(file_path).suffix.lower()
    if extension in C_LIKE_COMMENT_EXTENSIONS:
        return _classify_c_like_contexts(text, positions)
    if extension in PYTHON_COMMENT_EXTENSIONS:
        return _classify_python_contexts(text, positions)
    return {position: COMMENT_CONTEXT_UNSUPPORTED for position in positions}


def is_line_commented(file_path: str, line_number: int) -> bool:
    """Return ``True`` when the first non-whitespace char of a line is inside a comment."""
    with open(file_path, "r", encoding="utf-8", errors="replace") as file:
        text = file.read()

    if line_number < 1:
        return False

    line_start = 0
    current_line = 1
    text_length = len(text)

    while current_line < line_number and line_start < text_length:
        next_newline = text.find("\n", line_start)
        if next_newline == -1:
            return False
        line_start = next_newline + 1
        current_line += 1

    line_end = text.find("\n", line_start)
    if line_end == -1:
        line_end = text_length

    stripped_line = text[line_start:line_end].lstrip().lstrip("\ufeff")
    extension = Path(file_path).suffix.lower()
    if stripped_line.startswith("//"):
        return True
    if stripped_line.startswith("/*"):
        return True
    if extension in PYTHON_COMMENT_EXTENSIONS and stripped_line.startswith("#"):
        return True

    for absolute_index in range(line_start, line_end):
        if not text[absolute_index].isspace():
            context = classify_comment_contexts(file_path, text, [absolute_index]).get(absolute_index)
            return context == COMMENT_CONTEXT_COMMENT

    return False
