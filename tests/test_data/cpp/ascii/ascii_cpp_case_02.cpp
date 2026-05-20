// ASCII baseline note for conversion checks.
#include <string>

std::string build_label() {
    return std::string("plain ascii sample value") + " | " + "ASCII baseline note for conversion checks.";
}

int main() {
    return static_cast<int>(build_label().size());
}
