import time
import pytest
@pytest.mark.parametrize("function_code", [1, 5, 0x2B])
def test_unsupported_function_codes(client, function_code):
    from sim.vfd_sim import process_pdu

    response = process_pdu(bytes([function_code]))

    assert response == bytes([function_code | 0x80, 1])


@pytest.mark.parametrize("address", [4, 99, 104, 65535])
def test_undefined_read_addresses(client, address):
    from sim.vfd_sim import process_pdu

    pdu = bytes([
        3,
        (address >> 8) & 0xFF,
        address & 0xFF,
        0,
        1
    ])

    response = process_pdu(pdu)

    assert response == bytes([0x83, 2])


@pytest.mark.parametrize("quantity", [0, 126])
def test_invalid_read_quantities(client, quantity):
    from sim.vfd_sim import process_pdu

    pdu = bytes([
        3, 0, 0,
        (quantity >> 8) & 0xFF,
        quantity & 0xFF
    ])

    response = process_pdu(pdu)

    assert response == bytes([0x83, 3])


@pytest.mark.parametrize("address", [100, 101, 102, 103])
def test_reject_all_read_only_register_writes(client, address):
    from sim.vfd_sim import process_pdu

    pdu = bytes([
        6,
        (address >> 8) & 0xFF,
        address & 0xFF,
        0,
        1
    ])

    response = process_pdu(pdu)

    assert response == bytes([0x86, 2])
from client.modbus_client import ModbusException


def test_initial_register_values(client):
    values = client.read_holding_registers(0, 4)
    assert values == [0, 0, 10, 10]


def test_read_status_registers(client):
    values = client.read_holding_registers(100, 4)
    assert values == [1, 0, 25, 0]


def test_write_single_register(client):
    client.write_single_register(1, 250)
    assert client.read_holding_registers(1, 1) == [250]


def test_write_multiple_registers(client):
    client.write_multiple_registers(1, [300, 20, 20])
    assert client.read_holding_registers(1, 3) == [300, 20, 20]


def test_reject_read_only_register(client):
    with pytest.raises(ModbusException, match="code: 2"):
        client.write_single_register(100, 5)


def test_reject_invalid_address(client):
    with pytest.raises(ModbusException, match="code: 2"):
        client.read_holding_registers(99, 1)


def test_reject_out_of_range_value(client):
    with pytest.raises(ModbusException, match="code: 3"):
        client.write_single_register(1, 600)


def test_reject_invalid_quantity(client):
    with pytest.raises(ModbusException, match="code: 3"):
        client.read_holding_registers(0, 0)


def test_reject_unknown_function(client):
    with pytest.raises(ModbusException, match="code: 1"):
        client._request(bytes([99]))


def test_multiple_write_is_atomic(client):
    with pytest.raises(ModbusException, match="code: 3"):
        client.write_multiple_registers(1, [200, 9999])

    assert client.read_holding_registers(1, 2) == [0, 10]


def test_run_reaches_reference_frequency(client):
    client.write_single_register(2, 1)    # Acceleration: 0.1 seconds
    client.write_single_register(1, 250)  # Reference: 25.0 Hz
    client.write_single_register(0, 1)    # Start drive

    time.sleep(0.2)

    output = client.read_holding_registers(101, 1)[0]
    status = client.read_holding_registers(100, 1)[0]

    assert output == 250
    assert status & 2       # Running
    assert status & 8       # At reference


def test_stop_decelerates_to_zero(client):
    client.write_single_register(2, 1)
    client.write_single_register(3, 1)
    client.write_single_register(1, 250)
    client.write_single_register(0, 1)

    time.sleep(0.2)

    before_stop = client.read_holding_registers(101, 1)[0]
    assert before_stop == 250

    client.write_single_register(0, 0)
    time.sleep(0.2)

    after_stop = client.read_holding_registers(101, 1)[0]
    assert after_stop == 0


def test_overload_trip(client):
    client.write_single_register(1, 490)
    client.write_single_register(0, 1)

    status = client.read_holding_registers(100, 1)[0]
    output = client.read_holding_registers(101, 1)[0]
    fault_code = client.read_holding_registers(103, 1)[0]

    assert status & 4       # Fault bit
    assert output == 0
    assert fault_code == 15


def test_fault_reset_and_retrip(client):
    client.write_single_register(1, 490)
    client.write_single_register(0, 1)

    # Reset while overload condition persists.
    client.write_single_register(0, 5)

    status = client.read_holding_registers(100, 1)[0]
    assert status & 4

    # Remove the overload condition and stop the drive.
    client.write_single_register(0, 0)
    client.write_single_register(1, 0)

    # Reset the fault.
    client.write_single_register(0, 4)

    status = client.read_holding_registers(100, 1)[0]
    fault_code = client.read_holding_registers(103, 1)[0]

    assert not (status & 4)
    assert fault_code == 0


def test_fc03_and_fc04_return_same_status(client):
    from sim.vfd_sim import process_pdu

    # Read status using FC03 through the TCP client.
    holding = client.read_holding_registers(100, 1)

    # Read the same status register using FC04.
    response = process_pdu(bytes([4, 0, 100, 0, 1]))

    assert response[0] == 4
    assert response[1] == 2

    input_value = (response[2] << 8) | response[3]

    assert holding[0] == input_value


def test_fc16_byte_count_mismatch(client):
    from sim.vfd_sim import process_pdu

    # FC16: address 0, quantity 2, but byte count says 2
    # The correct byte count should be 4.
    malformed_pdu = bytes([16, 0, 0, 0, 2, 2, 0, 1])

    response = process_pdu(malformed_pdu)

    assert response == bytes([0x90, 3])


def test_seeded_fuzz_testing(client):
    import random
    from sim.vfd_sim import process_pdu

    rng = random.Random(1234)

    for _ in range(300):
        length = rng.randint(1, 11)
        pdu = bytes(
            rng.randint(0, 255)
            for _ in range(length)
        )

        response = process_pdu(pdu)

        assert len(response) >= 2

        if response[0] & 0x80:
            # Exception response
            assert len(response) == 2
            assert response[1] in (1, 2, 3)
        else:
            # Normal response must echo function code
            assert response[0] == pdu[0]

    # Confirm the simulator still responds after fuzzing.
    result = client.read_holding_registers(100, 1)
    assert len(result) == 1


def test_bad_protocol_id_closes_connection(client):
    import socket
    import struct

    with socket.create_connection(
        (client.host, client.port),
        timeout=2
    ) as sock:

        # MBAP header with an invalid protocol ID (1 instead of 0)
        header = struct.pack(
            ">HHHB",
            1,  # Transaction ID
            1,  # Invalid protocol ID
            2,  # Length
            1   # Unit ID
        )

        sock.sendall(header)

        response = sock.recv(1)

        assert response == b""

    # Verify the simulator remains available to other clients.
    result = client.read_holding_registers(100, 1)
    assert len(result) == 1
