from dataclasses import dataclass
from pathlib import Path


TESTS_DIR = Path(__file__).parent
TEST_DATA_DIR = TESTS_DIR / "test_data"
TEST_OUTPUT_DIR = TESTS_DIR / "output"
UTF8_BOM = b"\xef\xbb\xbf"


@dataclass(frozen=True)
class FixtureCase:
    relative_path: str
    encoding: str
    should_convert: bool
    expected_text: str

    @property
    def extension(self) -> str:
        return Path(self.relative_path).suffix

    @property
    def source_path(self) -> Path:
        return TEST_DATA_DIR / self.relative_path

    @property
    def output_path(self) -> Path:
        return TEST_OUTPUT_DIR / self.relative_path


ENCODING_CASES = (
    {
        "key": "ascii",
        "encoding": "ascii",
        "should_convert": True,
        "note": "ASCII baseline note for conversion checks.",
        "message": "plain ascii sample value",
    },
    {
        "key": "windows_1252",
        "encoding": "cp1252",
        "should_convert": True,
        "note": "Windows-1252 note: citta, perche, gia, euro € e “virgolette”.",
        "message": "label cp1252 citta € “quote”",
    },
    {
        "key": "iso_8859_1",
        "encoding": "iso-8859-1",
        "should_convert": True,
        "note": "ISO-8859-1 note: citta, perche, gia, deja, AEOU.",
        "message": "label iso citta perche gia deja",
    },
    {
        "key": "utf8",
        "encoding": "utf-8",
        "should_convert": False,
        "note": "UTF-8 note: cafe, manana, Привет, 你好.",
        "message": "label utf8 cafe manana Привет 你好",
    },
    {
        "key": "utf8_sig",
        "encoding": "utf-8-sig",
        "should_convert": False,
        "note": "UTF-8-SIG note: facade, Gruss Gott, 東京.",
        "message": "label utf8 sig facade Gruss Gott 東京",
    },
    {
        "key": "utf16",
        "encoding": "utf-16",
        "should_convert": False,
        "note": "UTF-16 note: manana, Καλημερα, こんにちは.",
        "message": "label utf16 manana Καλημερα こんにちは",
    },
)


LANGUAGE_CASES = (
    (
        "python",
        ".py",
        (
            """# __NOTE__
# __MESSAGE__
def compute_total(value_a, value_b):
    label = \"__MESSAGE__\"
    detail = \"__NOTE__\"
    return \"{} :: {}\".format(label, value_a + value_b)

print(compute_total(2, 3))
""",
            """# __NOTE__
# __MESSAGE__
class SampleRunner:
    def build(self):
        return \"__MESSAGE__\" + \" / \" + \"__NOTE__\"

print(SampleRunner().build())
""",
        ),
    ),
    (
        "cpp",
        ".cpp",
        (
            """// __NOTE__
// __MESSAGE__
#include <iostream>

int main() {
    const char* label = \"__MESSAGE__\";
    std::cout << label << std::endl;
    std::cout << \"__NOTE__\" << std::endl;
    return 0;
}
""",
            """// __NOTE__
#include <string>

std::string build_label() {
    return std::string(\"__MESSAGE__\") + \" | \" + \"__NOTE__\";
}

int main() {
    return static_cast<int>(build_label().size());
}
""",
        ),
    ),
    (
        "csharp",
        ".cs",
        (
            """// __NOTE__
using System;

public class Program {
    public static void Main() {
        const string label = \"__MESSAGE__\";
        Console.WriteLine(label);
        Console.WriteLine(\"__NOTE__\");
    }
}
""",
            """// __NOTE__
using System;

public sealed class SampleRunner {
    public string Build() {
        return \"__MESSAGE__\" + \" | \" + \"__NOTE__\";
    }
}
""",
        ),
    ),
)


def _build_fixture_cases() -> tuple[FixtureCase, ...]:
    cases: list[FixtureCase] = []
    for language_dir, extension, templates in LANGUAGE_CASES:
        for encoding_case in ENCODING_CASES:
            for index, template in enumerate(templates, start=1):
                expected_text = template.replace("__NOTE__", encoding_case["note"]).replace(
                    "__MESSAGE__", encoding_case["message"]
                )
                relative_path = (
                    f"{language_dir}/{encoding_case['key']}/"
                    f"{encoding_case['key']}_{language_dir}_case_{index:02d}{extension}"
                )
                cases.append(
                    FixtureCase(
                        relative_path=relative_path,
                        encoding=encoding_case["encoding"],
                        should_convert=encoding_case["should_convert"],
                        expected_text=expected_text,
                    )
                )
    return tuple(cases)


FIXTURE_CASES = _build_fixture_cases()


def write_fixture_tree() -> int:
    written_files = 0
    for case in FIXTURE_CASES:
        case.source_path.parent.mkdir(parents=True, exist_ok=True)
        case.source_path.write_bytes(case.expected_text.encode(case.encoding))
        written_files += 1
    return written_files