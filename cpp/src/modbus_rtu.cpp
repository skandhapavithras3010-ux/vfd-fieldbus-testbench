
#include "modbus_rtu.hpp"

#include <stdexcept>

namespace modbus {

uint16_t calculate_crc16(const std::vector<uint8_t>& data) {
    uint16_t crc = 0xFFFF;

    for (uint8_t byte : data) {
        crc ^= byte;

        for (int bit = 0; bit < 8; ++bit) {
            if (crc & 1) {
                crc = (crc >> 1) ^ 0xA001;
            } else {
                crc >>= 1;
            }
        }
    }

    return crc;
}

std::vector<uint8_t> build_frame(
    uint8_t slave_id,
    uint8_t function_code,
    const std::vector<uint8_t>& data
) {
    if (slave_id == 0 || slave_id > 247) {
        throw std::invalid_argument("Invalid slave ID");
    }

    std::vector<uint8_t> frame = {
        slave_id,
        function_code
    };

    frame.insert(frame.end(), data.begin(), data.end());

    uint16_t crc = calculate_crc16(frame);

    frame.push_back(static_cast<uint8_t>(crc & 0xFF));
    frame.push_back(static_cast<uint8_t>((crc >> 8) & 0xFF));

    return frame;
}

bool validate_frame(const std::vector<uint8_t>& frame) {
    if (frame.size() < 4) {
        return false;
    }

    if (frame[0] == 0 || frame[0] > 247) {
        return false;
    }

    uint16_t calculated_crc = calculate_crc16(
        std::vector<uint8_t>(frame.begin(), frame.end() - 2)
    );

    uint16_t received_crc =
        static_cast<uint16_t>(frame[frame.size() - 2]) |
        (static_cast<uint16_t>(frame.back()) << 8);

    return calculated_crc == received_crc;
}

std::optional<Frame> parse_frame(
    const std::vector<uint8_t>& frame
) {
    if (!validate_frame(frame)) {
        return std::nullopt;
    }

    Frame result;

    result.slave_id = frame[0];
    result.function_code = frame[1];

    result.data.assign(
        frame.begin() + 2,
        frame.end() - 2
    );

    return result;
}

} // namespace modbus
