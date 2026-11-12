
#include "modbus_rtu.hpp"

#include <cassert>
#include <iostream>
#include <vector>

using namespace modbus;

void test_crc_known_vector() {
    std::vector<uint8_t> request = {
        0x01, 0x03, 0x00, 0x00, 0x00, 0x0A
    };

    uint16_t crc = calculate_crc16(request);

    assert(crc == 0xCDC5);

    std::cout << "[PASS] CRC known vector\n";
}

void test_frame_construction() {
    std::vector<uint8_t> data = {
        0x00, 0x00, 0x00, 0x0A
    };

    auto frame = build_frame(1, READ_HOLDING_REGISTERS, data);

    assert(frame.size() == 8);
    assert(frame[0] == 0x01);
    assert(frame[1] == 0x03);
    assert(validate_frame(frame));

    std::cout << "[PASS] Frame construction\n";
}

void test_frame_validation() {
    std::vector<uint8_t> frame = {
        0x01, 0x03, 0x00, 0x00, 0x00, 0x0A,
        0xC5, 0xCD
    };

    assert(validate_frame(frame));

    std::cout << "[PASS] Valid frame validation\n";
}

void test_corrupted_frame() {
    std::vector<uint8_t> frame = {
        0x01, 0x03, 0x00, 0x00, 0x00, 0x0A,
        0xC5, 0xCD
    };

    frame[3] = 0x01;

    assert(!validate_frame(frame));

    std::cout << "[PASS] Corrupted frame rejection\n";
}

void test_short_frame() {
    std::vector<uint8_t> frame = {
        0x01, 0x03, 0x00
    };

    assert(!validate_frame(frame));

    std::cout << "[PASS] Short frame rejection\n";
}

void test_invalid_slave_id() {
    bool rejected = false;

    try {
        build_frame(248, READ_HOLDING_REGISTERS, {});
    }
    catch (const std::invalid_argument&) {
        rejected = true;
    }

    assert(rejected);

    std::cout << "[PASS] Invalid slave ID rejection\n";
}

void test_frame_parsing() {
    std::vector<uint8_t> frame = {
        0x01, 0x03, 0x00, 0x00, 0x00, 0x0A,
        0xC5, 0xCD
    };

    auto parsed = parse_frame(frame);

    assert(parsed.has_value());
    assert(parsed->slave_id == 1);
    assert(parsed->function_code == READ_HOLDING_REGISTERS);
    assert(parsed->data.size() == 4);

    std::cout << "[PASS] Frame parsing\n";
}

void test_invalid_frame_parsing() {
    std::vector<uint8_t> frame = {
        0x01, 0x03, 0x00, 0x00, 0x00, 0x0A,
        0x00, 0x00
    };

    auto parsed = parse_frame(frame);

    assert(!parsed.has_value());

    std::cout << "[PASS] Invalid frame parsing\n";
}

void test_exception_response() {
    // Exception response: slave 1, function 0x83, exception code 2
    auto frame = build_frame(
        1,
        0x83,
        {0x02}
    );

    auto parsed = parse_frame(frame);

    assert(parsed.has_value());
    assert(parsed->slave_id == 1);
    assert(parsed->function_code == 0x83);
    assert(parsed->is_exception());
    assert(parsed->exception_code() == 2);

    std::cout << "[PASS] Exception response handling\n";
}

int main() {
    test_crc_known_vector();
    test_frame_construction();
    test_frame_validation();
    test_corrupted_frame();
    test_short_frame();
    test_invalid_slave_id();
    test_frame_parsing();
    test_invalid_frame_parsing();
    test_exception_response();
    std::cout << "\nAll C++ RTU tests passed.\n";

    return 0;
}
