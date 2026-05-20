// UTF-8 note: cafe, manana, Привет, 你好.
// label utf8 cafe manana Привет 你好
#include <iostream>

int main() {
    const char* label = "label utf8 cafe manana Привет 你好";
    std::cout << label << std::endl;
    std::cout << "UTF-8 note: cafe, manana, Привет, 你好." << std::endl;
    return 0;
}
