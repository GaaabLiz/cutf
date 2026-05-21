from dataclasses import dataclass

import rich

from cutf.controller.fileChecker import check_illegal_chars
from cutf.model.AppSetting import AppSetting
from cutf.model.MissingCharResult import MissingCharResult
from cutf.util.log import format_log_error, format_log_path
from cutf.util.ollama import request_replacement_character
from cutf.util.textfile import encode_text_with_original_encoding, read_text_file_state


@dataclass
class AiFixSummary:
    """Counters and remaining findings collected during AI-assisted fixing."""

    total_missing_chars: int
    applied_fixes: int = 0
    skipped_fixes: int = 0
    retry_count: int = 0
    failed_fixes: int = 0
    remaining_occurrences: list[MissingCharResult] | None = None


def _line_details_from_absolute_index(text: str, absolute_char_index: int) -> tuple[str, int, int]:
    """Return the current line text, line number, and in-line position for a character index."""
    line_start = text.rfind("\n", 0, absolute_char_index) + 1
    line_end = text.find("\n", absolute_char_index)
    if line_end == -1:
        line_end = len(text)

    line_text = text[line_start:line_end]
    if line_text.endswith("\r"):
        line_text = line_text[:-1]

    line_number = text.count("\n", 0, absolute_char_index) + 1
    char_position = absolute_char_index - line_start
    return line_text, line_number, char_position


def _prompt_user_choice(input_fn=input) -> str:
    """Prompt the operator for the next action on the suggested fix."""
    rich.print("1. Si, applica la modifica")
    rich.print("2. No, ritenta")
    rich.print("3. No, passa al prossimo carattere")

    while True:
        choice = input_fn("Seleziona [1/2/3]: ").strip()
        if choice in {"1", "2", "3"}:
            return choice
        rich.print(format_log_error("Scelta non valida. Inserisci 1, 2 oppure 3."))


def fix_wrong_chars_with_ai(
    file_path: str,
    source_encoding: str,
    setting: AppSetting,
    input_fn=input,
    propose_fn=request_replacement_character,
) -> AiFixSummary:
    """Interactively repair replacement characters while preserving the original encoding."""
    current_state = read_text_file_state(file_path, source_encoding)
    initial_occurrences = check_illegal_chars(file_path, source_encoding)
    summary = AiFixSummary(
        total_missing_chars=len(initial_occurrences),
        remaining_occurrences=initial_occurrences,
    )

    if not initial_occurrences:
        return summary

    visible_occurrences = [
        occurrence
        for occurrence in initial_occurrences
        if occurrence.char_found and occurrence.absolute_char_index is not None
    ]

    if not visible_occurrences:
        rich.print(
            f"Found {len(initial_occurrences)} replacement-byte sequence(s) in {format_log_path(file_path)}, "
            f"but none are visible under {source_encoding}. AI fix only handles visible replacement characters."
        )
        return summary

    rich.print(
        f"Found {len(initial_occurrences)} replacement character(s) in {format_log_path(file_path)}."
    )

    hidden_occurrences = len(initial_occurrences) - len(visible_occurrences)
    if hidden_occurrences:
        rich.print(
            f"Skipping {hidden_occurrences} occurrence(s) that are not visible under {source_encoding}."
        )

    for occurrence in visible_occurrences:
        absolute_char_index = occurrence.absolute_char_index
        if absolute_char_index is None:
            summary.failed_fixes += 1
            continue

        if absolute_char_index >= len(current_state.text):
            summary.failed_fixes += 1
            continue

        if current_state.text[absolute_char_index] != "�":
            continue

        previous_suggestions: list[str] = []

        while True:
            line_text, line_number, char_position = _line_details_from_absolute_index(
                current_state.text,
                absolute_char_index,
            )

            try:
                suggested_character = propose_fn(
                    ollama_url=setting.ai_ollama_url or "",
                    model=setting.ai_model,
                    file_path=file_path,
                    line_text=line_text,
                    char_position=char_position,
                    previous_suggestions=previous_suggestions,
                )
            except RuntimeError as exc:
                rich.print(
                    format_log_error(
                        f"AI fix failed for {format_log_path(file_path)}:{line_number}: {exc}"
                    )
                )
                summary.failed_fixes += 1
                break

            if not suggested_character:
                rich.print(
                    format_log_error(
                        f"Ollama did not return a valid single-character fix for {format_log_path(file_path)}:{line_number}."
                    )
                )
                summary.failed_fixes += 1
                break

            corrected_line = (
                line_text[:char_position] + suggested_character + line_text[char_position + 1:]
            )
            rich.print(f"\nFile: {format_log_path(file_path)} | Line: {line_number}")
            rich.print(f"Riga errata   : {line_text}")
            rich.print(f"Riga proposta : {corrected_line}")

            choice = _prompt_user_choice(input_fn)
            if choice == "2":
                summary.retry_count += 1
                if suggested_character not in previous_suggestions:
                    previous_suggestions.append(suggested_character)
                continue

            if choice == "3":
                summary.skipped_fixes += 1
                break

            updated_text = (
                current_state.text[:absolute_char_index]
                + suggested_character
                + current_state.text[absolute_char_index + 1:]
            )

            try:
                updated_bytes = encode_text_with_original_encoding(updated_text, current_state)
            except UnicodeEncodeError as exc:
                rich.print(
                    format_log_error(
                        f"Cannot write {suggested_character!r} back using {source_encoding}: {exc}"
                    )
                )
                summary.failed_fixes += 1
                break

            with open(file_path, "wb") as f:
                f.write(updated_bytes)

            current_state = read_text_file_state(file_path, source_encoding)
            if (
                absolute_char_index < len(current_state.text)
                and current_state.text[absolute_char_index] == suggested_character
            ):
                summary.applied_fixes += 1
            else:
                rich.print(
                    format_log_error(
                        "The applied fix could not be verified on disk. Moving to the next replacement character."
                    )
                )
                summary.failed_fixes += 1
            break

    summary.remaining_occurrences = check_illegal_chars(file_path, source_encoding)
    return summary