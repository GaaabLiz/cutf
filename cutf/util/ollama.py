import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def build_ollama_prompt(
    file_path: str,
    line_text: str,
    char_position: int,
    previous_suggestions: list[str] | None = None,
) -> str:
    """Build a compact prompt that asks Ollama for one replacement character."""
    extension = os.path.splitext(file_path)[1].lower() or "unknown"
    left_context = line_text[:char_position]
    right_context = line_text[char_position + 1:]
    rejected = ", ".join(previous_suggestions or []) or "none"

    return (
        "You repair exactly one replacement character in source code or comments.\n"
        "Return JSON only, with this exact shape: {\"character\":\"x\"}.\n"
        "Rules:\n"
        "- Return exactly one Unicode character in character, not a string of multiple characters.\n"
        "- Do not return explanations, code fences, or extra keys.\n"
        "- If uncertain, infer the most likely single character from the context.\n"
        f"File extension: {extension}\n"
        f"Full line: {line_text}\n"
        f"Replacement char index: {char_position}\n"
        f"Left context: {left_context}\n"
        f"Right context: {right_context}\n"
        f"Rejected suggestions: {rejected}\n"
    )


def sanitize_replacement_character(raw_response: str) -> str | None:
    """Extract a single replacement character from an Ollama response."""
    candidate = raw_response.strip()
    if not candidate:
        return None

    parsed: object = candidate
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        parsed = candidate

    if isinstance(parsed, dict):
        for key in ("character", "replacement", "char"):
            value = parsed.get(key)
            if isinstance(value, str):
                candidate = value
                break
        else:
            return None
    elif isinstance(parsed, str):
        candidate = parsed
    else:
        return None

    if len(candidate) != 1:
        return None
    if candidate == "�":
        return None
    return candidate


def request_replacement_character(
    ollama_url: str,
    model: str,
    file_path: str,
    line_text: str,
    char_position: int,
    previous_suggestions: list[str] | None = None,
) -> str | None:
    """Ask Ollama for the most likely original character replacing ``�``."""
    prompt = build_ollama_prompt(file_path, line_text, char_position, previous_suggestions)
    body = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": min(0.2 + (0.1 * len(previous_suggestions or [])), 0.7),
        },
    }
    url = f"{ollama_url.rstrip('/')}/api/generate"
    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(request, timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Cannot contact Ollama at {ollama_url}: {exc}") from exc

    response_text = payload.get("response")
    if not isinstance(response_text, str):
        raise RuntimeError("Ollama returned an unexpected response payload.")
    return sanitize_replacement_character(response_text)