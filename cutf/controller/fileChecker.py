import codecs
import os

import rich

from cutf.model.MissingCharResult import MissingCharResult
from cutf.util.code import COMMENT_CONTEXT_COMMENT, classify_comment_contexts
from cutf.util.textfile import read_text_file_state


UTF8_REPLACEMENT_BYTES = b"\xef\xbf\xbd"


def _strip_line_ending(line_text: str) -> str:
    """Remove only the newline suffix from a line preserving other whitespace."""
    if line_text.endswith("\r\n"):
        return line_text[:-2]
    if line_text.endswith("\n") or line_text.endswith("\r"):
        return line_text[:-1]
    return line_text


def _find_raw_replacement_offsets(raw_data: bytes, replacement_bytes: bytes) -> list[int]:
    """Return every raw byte offset that starts with ``replacement_bytes``."""
    offsets = []
    search_start = 0
    while True:
        offset = raw_data.find(replacement_bytes, search_start)
        if offset == -1:
            return offsets
        offsets.append(offset)
        search_start = offset + 1


def _replacement_bytes_for_scan(source_encoding: str) -> bytes:
    """Return the byte pattern that should represent one replacement char for the scan."""
    try:
        return "�".encode(source_encoding)
    except UnicodeEncodeError:
        return UTF8_REPLACEMENT_BYTES


def _line_details_from_absolute_index(text: str, absolute_char_index: int) -> tuple[str, int, int]:
    """Return line text, line number, and in-line position for a text index."""
    bounded_index = min(max(absolute_char_index, 0), len(text))
    line_start = text.rfind("\n", 0, bounded_index) + 1
    line_end = text.find("\n", bounded_index)
    if line_end == -1:
        line_end = len(text)

    line_text = _strip_line_ending(text[line_start:line_end]).lstrip(" \t")
    line_number = text.count("\n", 0, bounded_index) + 1
    char_position = bounded_index - line_start
    return line_text, line_number, char_position


def _classification_anchor_index(text: str, absolute_char_index: int) -> int | None:
    """Return an in-range index suitable for comment-context classification."""
    if not text:
        return None
    return min(max(absolute_char_index, 0), len(text) - 1)


def check_illegal_chars(file_path: str, source_encoding: str) -> list[MissingCharResult]:
    """Find replacement-character byte sequences in a text file.

    This function searches for the raw byte sequence that represents one
    replacement character in the current file encoding. When the encoding cannot
    encode ``�`` directly, it falls back to the UTF-8 byte sequence
    ``EF BF BD``. When the decoded text shows a visible ``�`` at the same
    position, ``char_found`` is ``True``; otherwise the raw sequence is still
    reported with ``char_found=False`` and ``char_position=-1``.

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

    replacement_bytes = _replacement_bytes_for_scan(file_state.write_encoding)
    raw_offsets = _find_raw_replacement_offsets(file_state.raw_data, replacement_bytes)
    if not raw_offsets:
        return results

    decoder = codecs.getincrementaldecoder(file_state.decode_encoding)(errors="replace")
    decoded_char_index = 0
    last_raw_offset = 0
    occurrences: list[dict[str, int | str | bool | None]] = []

    for raw_offset in raw_offsets:
        decoded_char_index += len(decoder.decode(file_state.raw_data[last_raw_offset:raw_offset], final=False))
        insertion_index = decoded_char_index
        sequence_text = decoder.decode(file_state.raw_data[raw_offset:raw_offset + len(replacement_bytes)], final=False)
        absolute_char_index = insertion_index if sequence_text.startswith("�") else None
        line_text, line_number, char_position = _line_details_from_absolute_index(text_data, insertion_index)

        rich.print(
            f"\t[bold yellow]Found replacement-byte sequence at position {raw_offset}, "
            f"line {line_number} in file {os.path.basename(file_path)}[/bold yellow]"
        )

        occurrences.append(
            {
                "string": line_text,
                "line": line_number,
                "char_position": char_position if absolute_char_index is not None else -1,
                "char_found": absolute_char_index is not None,
                "byte_sequence_file_pos": raw_offset,
                "absolute_char_index": absolute_char_index,
                "classification_index": _classification_anchor_index(text_data, insertion_index),
            }
        )

        decoded_char_index += len(sequence_text)
        last_raw_offset = raw_offset + len(replacement_bytes)

    contexts = classify_comment_contexts(
        file_path,
        text_data,
        [
            int(occurrence["classification_index"])
            for occurrence in occurrences
            if occurrence["classification_index"] is not None
        ],
    )

    for occurrence in occurrences:
        classification_index = occurrence["classification_index"]
        comment_context = contexts.get(int(classification_index), "code") if classification_index is not None else "code"
        results.append(
            MissingCharResult(
                is_commented=comment_context == COMMENT_CONTEXT_COMMENT,
                comment_context=comment_context,
                string=str(occurrence["string"]),
                line=int(occurrence["line"]),
                file_name=os.path.basename(file_path),
                char_position=int(occurrence["char_position"]),
                char_found=bool(occurrence["char_found"]),
                byte_sequence_file_pos=int(occurrence["byte_sequence_file_pos"]),
                absolute_char_index=(
                    int(occurrence["absolute_char_index"])
                    if occurrence["absolute_char_index"] is not None
                    else None
                ),
            )
        )

    return results