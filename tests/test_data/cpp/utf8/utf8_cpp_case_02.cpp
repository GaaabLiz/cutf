// UTF-8 note: cafe, manana, Привет, 你好.
#include <string>

std::string build_label() {
    return std::string("label utf8 cafe manana Привет 你好") + " | " + "UTF-8 note: cafe, manana, Привет, 你好.";
}

int main() {
    return static_cast<int>(build_label().size());
}
