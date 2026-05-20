import os

import rich

from cutf.model.MissingCharResult import MissingCharResult
from cutf.util.textfile import compute_byte_offset, read_text_file_state


def _is_line_commented(line_text: str, in_block_comment: bool) -> tuple[bool, bool]:
    """Evaluate whether the current line should be considered a comment."""
    stripped_line = line_text.strip().lstrip("\ufeff")

    if in_block_comment:
        return True, "*/" not in stripped_line

    if stripped_line.startswith("//"):
        return True, False

    if "/*" in stripped_line:
        start_index = stripped_line.find("/*")
        end_index = stripped_line.find("*/", start_index + 2)
        return False, end_index == -1

    return False, False


def _strip_line_ending(line_text: str) -> str:
    """Remove only the newline suffix from a line preserving other whitespace."""
    if line_text.endswith("\r\n"):
        return line_text[:-2]
    if line_text.endswith("\n") or line_text.endswith("\r"):
        return line_text[:-1]
    return line_text


def check_illegal_chars(file_path: str, source_encoding: str) -> list[MissingCharResult]:
    """Find replacement-character byte sequences in a text file.

    This function searches for the UTF-8 byte sequence ``EF BF BD`` (U+FFFD,
    replacement character) and reports each match with line metadata.

    Args:
        file_path: Absolute or relative path of the file to inspect.
        source_encoding: Encoding used to decode the file content for line extraction.

    Returns:
        list[MissingCharResult]: One item for each detected replacement character.

    Raises:
        RuntimeError: If the file cannot be decoded using ``source_encoding``.
    """
    results = []
    try:
        file_state = read_text_file_state(file_path, source_encoding)
        text_data = file_state.text
    except UnicodeDecodeError:
        rich.print(
            f"\t[bold red]Error decoding file {os.path.basename(file_path)} "
            f"with encoding {source_encoding}.[/bold red]"
        )
        raise RuntimeError(f"Error decoding file {os.path.basename(file_path)} during check_illegal_chars().")

    in_block_comment = False
    absolute_char_index = 0
    for line_number, line_with_end in enumerate(text_data.splitlines(keepends=True), start=1):
        line = _strip_line_ending(line_with_end)
        line_is_commented, in_block_comment = _is_line_commented(line, in_block_comment)

        search_start = 0
        while True:
            char_pos_in_line = line.find("�", search_start)
            if char_pos_in_line == -1:
                break

            char_index = absolute_char_index + char_pos_in_line
            byte_offset = compute_byte_offset(text_data, file_state, char_index)

            rich.print(
                f"\t[bold yellow]Found illegal character at position {byte_offset}, "
                f"line {line_number} in file {os.path.basename(file_path)}[/bold yellow]"
            )

            results.append(
                MissingCharResult(
                    is_commented=line_is_commented,
                    string=line.lstrip(" \t"),
                    line=line_number,
                    file_name=os.path.basename(file_path),
                    char_position=char_pos_in_line,
                    char_found=True,
                    byte_sequence_file_pos=byte_offset,
                    absolute_char_index=char_index,
                )
            )
            search_start = char_pos_in_line + 1

        absolute_char_index += len(line_with_end)

    return results