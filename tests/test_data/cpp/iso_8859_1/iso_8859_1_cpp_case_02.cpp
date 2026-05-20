// ISO-8859-1 note: citta, perche, gia, deja, AEOU.
#include <string>

std::string build_label() {
    return std::string("label iso citta perche gia deja") + " | " + "ISO-8859-1 note: citta, perche, gia, deja, AEOU.";
}

int main() {
    return static_cast<int>(build_label().size());
}
