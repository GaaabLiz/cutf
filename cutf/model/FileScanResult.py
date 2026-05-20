from dataclasses import dataclass

from cutf.model.MissingCharResult import MissingCharResult


@dataclass
class FileScanResult:
    """Result payload produced when processing a single file.

    Attributes:
        file_path: Absolute or relative file path that was scanned.
        file_name: File name extracted from ``file_path``.
        encoding_before: Detected source encoding before any operation.
        encoding_after: Target encoding after conversion, if conversion happened.
        converted: ``True`` when conversion was executed successfully.
        check_missing_char: List of missing-character findings, if checks were run.
        error_skipped: ``True`` when the file was skipped because of an error.
        error_name: Optional short error name (reserved for future use).
        error_description: Human-readable error details.
        skipped: ``True`` when no operation was needed for the file.
        ai_fix_enabled: ``True`` when interactive AI fixing ran for the file.
        ai_total_missing_chars: Number of replacement characters found before AI fixing.
        ai_applied_fixes: Number of user-approved AI fixes written to disk.
        ai_skipped_fixes: Number of replacement characters skipped by the user.
        ai_retry_count: Number of times the user asked Ollama for another proposal.
        ai_failed_fixes: Number of failed AI suggestions or write verifications.
    """
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
    ai_fix_enabled: bool = False
    ai_total_missing_chars: int = 0
    ai_applied_fixes: int = 0
    ai_skipped_fixes: int = 0
    ai_retry_count: int = 0
    ai_failed_fixes: int = 0