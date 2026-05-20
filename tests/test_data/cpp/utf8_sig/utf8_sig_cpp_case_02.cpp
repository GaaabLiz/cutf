// UTF-8-SIG note: facade, Gruss Gott, 東京.
#include <string>

std::string build_label() {
    return std::string("label utf8 sig facade Gruss Gott 東京") + " | " + "UTF-8-SIG note: facade, Gruss Gott, 東京.";
}

int main() {
    return static_cast<int>(build_label().size());
}
