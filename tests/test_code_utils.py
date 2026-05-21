from pathlib import Path

from cutf.util.code import (
    COMMENT_CONTEXT_CODE,
    COMMENT_CONTEXT_COMMENT,
    COMMENT_CONTEXT_UNSUPPORTED,
    classify_comment_contexts,
    is_line_commented,
)


def test_classify_comment_contexts_detects_inline_c_like_comment():
    text = "if (isAtomSectionId) { // Se param � un section id atom\n"
    missing_index = text.index("�")

    contexts = classify_comment_contexts("sample.cpp", text, [missing_index])

    assert contexts[missing_index] == COMMENT_CONTEXT_COMMENT


def test_classify_comment_contexts_keeps_comment_markers_inside_c_like_strings_as_code():
    text = 'printf("// not a comment �");\nprintf("/* still not a comment � */");\n'
    first_missing_index = text.index("�")
    second_missing_index = text.rindex("�")

    contexts = classify_comment_contexts("sample.cpp", text, [first_missing_index, second_missing_index])

    assert contexts[first_missing_index] == COMMENT_CONTEXT_CODE
    assert contexts[second_missing_index] == COMMENT_CONTEXT_CODE


def test_classify_comment_contexts_detects_python_comments_but_not_hash_inside_strings():
    text = 'value = 1  # comment �\nprint("# not a comment �")\n'
    comment_missing_index = text.index("�")
    string_missing_index = text.rindex("�")

    contexts = classify_comment_contexts("sample.py", text, [comment_missing_index, string_missing_index])

    assert contexts[comment_missing_index] == COMMENT_CONTEXT_COMMENT
    assert contexts[string_missing_index] == COMMENT_CONTEXT_CODE


def test_classify_comment_contexts_marks_unsupported_extensions_explicitly():
    text = "plain text �\n"
    missing_index = text.index("�")

    contexts = classify_comment_contexts("sample.txt", text, [missing_index])

    assert contexts[missing_index] == COMMENT_CONTEXT_UNSUPPORTED


def test_is_line_commented_single_line_comment(tmp_path: Path):
    file_path = tmp_path / "file.c"
    file_path.write_text("int a = 1;\n// comment\nint b = 2;\n", encoding="utf-8")

    assert is_line_commented(str(file_path), 2) is True
    assert is_line_commented(str(file_path), 1) is False


def test_is_line_commented_inside_block_comment(tmp_path: Path):
    file_path = tmp_path / "file.c"
    file_path.write_text("/*\ninside\n*/\nint x = 0;\n", encoding="utf-8")

    assert is_line_commented(str(file_path), 2) is True
    assert is_line_commented(str(file_path), 4) is False

