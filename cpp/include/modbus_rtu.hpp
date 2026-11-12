
#ifndef MODBUS_RTU_HPP
#define MODBUS_RTU_HPP

#include <cstdint>
#include <vector>
#include <optional>
#include <stdexcept>

namespace modbus {

constexpr uint8_t READ_HOLDING_REGISTERS = 0x03;
constexpr uint8_t READ_INPUT_REGISTERS = 0x04;
constexpr uint8_t WRITE_SINGLE_REGISTER = 0x06;
constexpr uint8_t WRITE_MULTIPLE_REGISTERS = 0x10;

constexpr uint8_t MAX_READ_REGISTERS = 125;
constexpr uint8_t MAX_WRITE_REGISTERS = 123;

struct Frame {
    uint8_t slave_id;
    uint8_t function_code;
    std::vector<uint8_t> data;

    bool is_exception() const {
        return (function_code & 0x80) != 0;
    }

    uint8_t exception_code() const {
        if (!is_exception() || data.size() != 1) {
            throw std::logic_error("Frame is not a valid exception response");
        }

        return data[0];
    }
};

uint16_t calculate_crc16(const std::vector<uint8_t>& data);

std::vector<uint8_t> build_frame(
    uint8_t slave_id,
    uint8_t function_code,
    const std::vector<uint8_t>& data
);

bool validate_frame(const std::vector<uint8_t>& frame);

std::optional<Frame> parse_frame(
    const std::vector<uint8_t>& frame
);

} // namespace modbus

#endif
