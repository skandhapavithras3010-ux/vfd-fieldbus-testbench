
import pytest

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

