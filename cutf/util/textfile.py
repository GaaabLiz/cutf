from dataclasses import dataclass

UTF8_BOM = b"\xef\xbb\xbf"
UTF16_LE_BOM = b"\xff\xfe"
UTF16_BE_BOM = b"\xfe\xff"


@dataclass(frozen=True)
class TextFileState:
    """Decoded text plus the information required to write it back unchanged."""

    raw_data: bytes
    text: str
    normalized_encoding: str
    write_encoding: str
    bom_bytes: bytes


def normalize_encoding_name(encoding: str) -> str:
    """Normalize common encoding labels for comparisons and writes."""
    return encoding.strip().lower().replace("_", "-")


def detect_bom(raw_data: bytes) -> bytes:
    """Return the BOM prefix used by the raw file content, if any."""
    if raw_data.startswith(UTF8_BOM):
        return UTF8_BOM
    if raw_data.startswith(UTF16_LE_BOM):
        return UTF16_LE_BOM
    if raw_data.startswith(UTF16_BE_BOM):
        return UTF16_BE_BOM
    return b""


def read_text_file_state(file_path: str, source_encoding: str) -> TextFileState:
    """Read a text file and preserve the metadata needed for round-trip writes."""
    with open(file_path, "rb") as f:
        raw_data = f.read()

    normalized_encoding = normalize_encoding_name(source_encoding)
    bom_bytes = detect_bom(raw_data)
    decode_encoding = normalized_encoding
    write_encoding = normalized_encoding

    if bom_bytes == UTF8_BOM:
        decode_encoding = "utf-8-sig"
        write_encoding = "utf-8"
    elif bom_bytes == UTF16_LE_BOM:
        decode_encoding = "utf-16"
        write_encoding = "utf-16-le"
    elif bom_bytes == UTF16_BE_BOM:
        decode_encoding = "utf-16"
        write_encoding = "utf-16-be"
    elif normalized_encoding == "utf-8-sig":
        decode_encoding = "utf-8-sig"
        write_encoding = "utf-8"
        bom_bytes = UTF8_BOM
    elif normalized_encoding == "utf-16":
        decode_encoding = "utf-16"
        write_encoding = "utf-16-le"

    text = raw_data.decode(decode_encoding, errors="replace")
    return TextFileState(
        raw_data=raw_data,
        text=text,
        normalized_encoding=normalized_encoding,
        write_encoding=write_encoding,
        bom_bytes=bom_bytes,
    )


def encode_text_with_original_encoding(text: str, state: TextFileState) -> bytes:
    """Encode text using the original file encoding and BOM strategy."""
    encoded = text.encode(state.write_encoding)
    if state.bom_bytes and not encoded.startswith(state.bom_bytes):
        return state.bom_bytes + encoded
    return encoded


def compute_byte_offset(text: str, state: TextFileState, char_index: int) -> int:
    """Return the byte offset of a character index in the original file encoding."""
    prefix = text[:char_index].encode(state.write_encoding)
    return len(state.bom_bytes) + len(prefix)