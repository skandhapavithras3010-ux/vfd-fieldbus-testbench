
import pytest

from ai.test_generator import load_spec, generate_boundary_cases
from client.modbus_client import ModbusException


SPEC = load_spec()
CASES = generate_boundary_cases(SPEC)


@pytest.mark.parametrize(
    "case",
    CASES,
    ids=[
        f"addr{case['addr']}_value{case['value']}"
        for case in CASES
    ]
)
def test_generated_boundary_case_matches_simulator(client, case):
    """
    Compare the specification oracle against
    the actual VFD simulator response.
    """

    address = case["addr"]
    value = case["value"]
    expected = case["expected"]

    try:
        client.write_single_register(address, value)
        actual = "ok"

    except ModbusException as error:
        exception_code = int(str(error).rsplit(" ", 1)[-1])
        actual = f"exc{exception_code}"

    assert actual == expected, (
        f"Address={address}, Value={value}, "
        f"Expected={expected}, Actual={actual}"
    )
