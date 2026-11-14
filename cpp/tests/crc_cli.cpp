
#include "modbus_rtu.hpp"

#include <iostream>
#include <vector>
#include <string>
#include <cstdlib>

int main(int argc, char* argv[]) {
    std::vector<uint8_t> data;

    for (int i = 1; i < argc; ++i) {
        unsigned long value = std::stoul(argv[i], nullptr, 16);

        if (value > 255) {
            std::cerr << "Invalid byte value\n";
            return 1;
        }

        data.push_back(static_cast<uint8_t>(value));
    }

    uint16_t crc = modbus::calculate_crc16(data);

    std::cout << std::hex << std::uppercase
              << crc << '\n';

    return 0;
}
