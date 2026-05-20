// Windows-1252 note: citta, perche, gia, euro € e “virgolette”.
#include <string>

std::string build_label() {
    return std::string("label cp1252 citta € “quote”") + " | " + "Windows-1252 note: citta, perche, gia, euro € e “virgolette”.";
}

int main() {
    return static_cast<int>(build_label().size());
}
