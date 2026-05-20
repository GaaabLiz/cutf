// Windows-1252 note: citta, perche, gia, euro € e “virgolette”.
// label cp1252 citta € “quote”
#include <iostream>

int main() {
    const char* label = "label cp1252 citta € “quote”";
    std::cout << label << std::endl;
    std::cout << "Windows-1252 note: citta, perche, gia, euro € e “virgolette”." << std::endl;
    return 0;
}
