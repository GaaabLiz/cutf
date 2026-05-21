from collections import Counter

import rich
from rich.table import Table

from cutf.model import AppSetting
from cutf.model.FileScanResult import FileScanResult
from cutf.util.code import COMMENT_CONTEXT_CODE, COMMENT_CONTEXT_COMMENT, COMMENT_CONTEXT_UNSUPPORTED


def _iter_missing_char_findings(results: list[FileScanResult]):
    """Yield every missing-char finding collected in ``results``."""
    for result in results:
        for finding in result.check_missing_char or []:
            yield finding


def _build_missing_char_table(
    title: str,
    findings: list,
    print_mis_char_string: bool,
    empty_message: str,
) -> Table:
    """Build a Rich table for a slice of missing-character findings."""
    table = Table(title=title)
    table.add_column("File", style="cyan")
    table.add_column("Visible", justify="center", style="magenta")
    table.add_column("Line", justify="right", style="green")
    table.add_column("Line Pos", justify="right")
    table.add_column("File Pos", justify="right")
    if print_mis_char_string:
        table.add_column("String")

    if findings:
        for finding in findings:
            row = [
                finding.file_name,
                str(finding.char_found),
                str(finding.line),
                str(finding.char_position),
                str(finding.byte_sequence_file_pos),
            ]
            if print_mis_char_string:
                row.append(finding.string)
            table.add_row(*row)
    else:
        row = [empty_message, "", "", "", ""]
        if print_mis_char_string:
            row.append("")
        table.add_row(*row)

    return table


def __print_encoding_before(results: list[FileScanResult]):
    """Print a count of detected original encodings.

    Args:
        results: Collection of per-file scan outcomes.
    """
    encoding_counter = Counter()
    total_files = len(results)
    files_with_detected_encoding = 0

    # Scorri ogni FileScanResult
    for result in results:
        # Aggiungi l'encoding_before se non e None
        if result.encoding_before:
            encoding_counter[result.encoding_before] += 1
            files_with_detected_encoding += 1

    table = Table(
        title=(
            "Encodings found during scanning "
            f"({files_with_detected_encoding}/{total_files} files with detected encoding)"
        )
    )
    table.add_column("Encoding", style="cyan")
    table.add_column("Files", justify="right", style="magenta")
    table.add_column("Notes")

    if encoding_counter:
        for encoding, count in sorted(encoding_counter.items(), key=lambda item: (-item[1], item[0])):
            table.add_row(encoding, str(count), "")
    else:
        table.add_row("No detected encoding", "0", "")

    missing_encoding_count = total_files - files_with_detected_encoding
    if missing_encoding_count:
        table.add_row(
            "Undetected or skipped early",
            str(missing_encoding_count),
            "Unsupported extension or early processing error",
        )

    rich.print(table)


def __print_converted_files(results: list[FileScanResult]):
    """Print all files that were converted during processing.

    Args:
        results: Collection of per-file scan outcomes.
    """
    table = Table(title="Converted files")
    table.add_column("File", style="cyan")
    table.add_column("From", style="magenta")
    table.add_column("To", style="green")
    count = 0
    for result in results:
        if result.converted:
            count += 1
            table.add_row(
                result.file_name,
                result.encoding_before or "Unknown",
                result.encoding_after or "Unknown",
            )
    if count == 0:
        table.add_row("No converted files", "", "")
    rich.print(table)


def __print_skipped_files(results: list[FileScanResult], print_all: bool):
    """Print files skipped because no action was required.

    Args:
        results: Collection of per-file scan outcomes.
        print_all: If ``True``, prints one row per skipped file.
    """
    if print_all:
        table = Table(title="Skipped files")
        table.add_column("File", style="cyan")
        table.add_column("Reason")
        count = 0
        for result in results:
            if result.skipped:
                count += 1
                table.add_row(result.file_name, "No action was required")
        if count == 0:
            table.add_row("No skipped files", "")
    else:
        table = Table(title="Skipped files")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", justify="right", style="magenta")
        count = 0
        for result in results:
            if result.skipped:
                count += 1
        table.add_row("Files skipped because no action was required", str(count))
    rich.print(table)


def __print_skipped_error_files(results: list[FileScanResult]):
    """Print files skipped because of processing errors.

    Args:
        results: Collection of per-file scan outcomes.
    """
    table = Table(title="Skipped files from errors")
    table.add_column("File", style="cyan")
    table.add_column("Error")
    count = 0
    for result in results:
        if result.error_skipped:
            count += 1
            table.add_row(result.file_path, result.error_description or "Unknown error")
    if count == 0:
        table.add_row("No processing errors", "")
    rich.print(table)


def __print_ai_fix_summary(results: list[FileScanResult]):
    """Print an aggregate summary for interactive AI-fix runs."""
    ai_results = [result for result in results if result.ai_fix_enabled]
    table = Table(title="AI fix summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", justify="right", style="magenta")
    table.add_row("Files processed with AI fix", str(len(ai_results)))
    table.add_row("Replacement chars found", str(sum(result.ai_total_missing_chars for result in ai_results)))
    table.add_row("Fixes applied", str(sum(result.ai_applied_fixes for result in ai_results)))
    table.add_row("Skipped by user", str(sum(result.ai_skipped_fixes for result in ai_results)))
    table.add_row("Retries requested", str(sum(result.ai_retry_count for result in ai_results)))
    table.add_row("Failed fixes", str(sum(result.ai_failed_fixes for result in ai_results)))
    table.add_row(
        "Remaining replacement chars",
        str(sum(len(result.check_missing_char or []) for result in ai_results)),
    )
    rich.print(table)


def __print_missing_chars_on_comments(results: list[FileScanResult], print_mis_char_string: bool):
    """Print missing character occurrences detected in comments.

    Args:
        results: Collection of per-file scan outcomes.
        print_mis_char_string: If ``True``, include the original line string.
    """
    findings = [
        finding
        for finding in _iter_missing_char_findings(results)
        if finding.comment_context == COMMENT_CONTEXT_COMMENT
    ]
    rich.print(
        _build_missing_char_table(
            "Missing chars found in comments",
            findings,
            print_mis_char_string,
            "No missing chars found in comments",
        )
    )


def __print_missing_chars_on_code(results: list[FileScanResult], print_mis_char_string: bool, only_relevant: bool):
    """Print missing character occurrences detected in code lines.

    Args:
        results: Collection of per-file scan outcomes.
        print_mis_char_string: If ``True``, include the original line string.
        only_relevant: If ``True``, hide missing-char entries where the symbol is not visible.
    """
    findings = [
        finding
        for finding in _iter_missing_char_findings(results)
        if finding.comment_context == COMMENT_CONTEXT_CODE and (finding.char_found or not only_relevant)
    ]
    rich.print(
        _build_missing_char_table(
            "Missing chars found in code",
            findings,
            print_mis_char_string,
            "No missing chars found in code",
        )
    )


def __print_missing_chars_on_unsupported(results: list[FileScanResult], print_mis_char_string: bool):
    """Print missing characters found in files without supported comment analysis."""
    findings = [
        finding
        for finding in _iter_missing_char_findings(results)
        if finding.comment_context == COMMENT_CONTEXT_UNSUPPORTED
    ]
    rich.print(
        _build_missing_char_table(
            "Missing chars in unsupported comment-analysis files",
            findings,
            print_mis_char_string,
            "No missing chars found in unsupported comment-analysis files",
        )
    )


def print_results(results: list[FileScanResult], setting: AppSetting):
    """Print the complete scan summary to the console.

    Args:
        results: Collection of per-file scan outcomes.
        setting: Runtime settings controlling verbosity and filtering.
    """

    rich.print("\n\n")

    rich.print("########################################################") if setting.verbose else None
    rich.print("### START OF RESULTS ###################################")
    rich.print("########################################################") if setting.verbose else None

    # Print list of encoding before all
    __print_encoding_before(results)
    rich.print("\n")

    __print_ai_fix_summary(results)
    rich.print("\n")

    # Print file converted
    __print_converted_files(results)
    rich.print("\n")

    # File skipped
    __print_skipped_files(results, setting.print_skipped_file_no_action)
    rich.print("\n")

    # File skipped (Error)
    __print_skipped_error_files(results)
    rich.print("\n")

    # Missing chars (comments)
    if not setting.print_result_only_relevant:
        __print_missing_chars_on_comments(results, setting.print_missing_char_str)
        rich.print("\n")

    __print_missing_chars_on_unsupported(results, setting.print_missing_char_str)
    rich.print("\n")

    # Missing chars (code)
    __print_missing_chars_on_code(results, setting.print_missing_char_str, setting.print_result_only_relevant)

    rich.print("\n\n")
    rich.print("########################################################") if setting.verbose else None
    rich.print("### END OF RESULTS #####################################")
    rich.print("########################################################") if setting.verbose else None
