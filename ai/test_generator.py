
import json
from pathlib import Path


SPEC_PATH = (
    Path(__file__).resolve().parent.parent
    / "spec"
    / "register_map.json"
)


def load_spec():
    """Load the VFD register specification."""
    with open(SPEC_PATH, "r", encoding="utf-8") as file:
        return json.load(file)["registers"]


def oracle(spec, addr, value):
    """
    Determine the expected Modbus result.

    Returns:
        ok    : Valid register write
        exc2  : Undefined or read-only register
        exc3  : Invalid or out-of-range value
    """
    register = spec.get(str(addr))

    if register is None:
        return "exc2"

    if register["access"] != "rw":
        return "exc2"

    if not isinstance(value, int) or isinstance(value, bool):
        return "exc3"

    if not 0 <= value <= 65535:
        return "exc3"

    # Control word allows only bits 0, 1 and 2.
    if addr == 0 and (value & ~0x07):
        return "exc3"

    if value < register["min"] or value > register["max"]:
        return "exc3"

    return "ok"


def generate_boundary_cases(spec):
    """Generate boundary-value tests for writable registers."""
    cases = []

    for addr, register in spec.items():
        if register["access"] != "rw":
            continue

        minimum = register["min"]
        maximum = register["max"]

        values = {
            minimum - 1,
            minimum,
            minimum + 1,
            maximum - 1,
            maximum,
            maximum + 1,
            65535,
        }

        # Additional control-word bit-pattern tests.
        if int(addr) == 0:
            values.update([1, 2, 4, 5, 8, 0x80, 0x8000])

        for value in sorted(values):
            if 0 <= value <= 65535:
                cases.append({
                    "addr": int(addr),
                    "value": value,
                    "expected": oracle(spec, int(addr), value),
                })

    return cases

def validate_ai_cases(raw_output, spec):
    """
    Validate untrusted AI-generated JSON test cases.

    Accept only:
    - A JSON list of objects
    - Integer address and value fields (booleans rejected)
    - Known register addresses
    - Values within the Modbus 16-bit range

    Expected results are always calculated by our oracle.
    """
    try:
        proposals = json.loads(raw_output)
    except (json.JSONDecodeError, TypeError):
        return []

    if not isinstance(proposals, list):
        return []

    validated = []

    for item in proposals:
        if not isinstance(item, dict):
            continue

        addr = item.get("addr")
        value = item.get("value")

        if type(addr) is not int or type(value) is not int:
            continue

        if str(addr) not in spec:
            continue

        if not 0 <= value <= 65535:
            continue

        validated.append({
            "addr": addr,
            "value": value,
            "expected": oracle(spec, addr, value),
        })

    return validated
def demo_ai_validation(spec):
    """Test the validator using simulated AI-generated JSON."""

    sample_ai_output = json.dumps([
        {"addr": 1, "value": 500},
        {"addr": 0, "value": 8},
        {"addr": 100, "value": 5},
        {"addr": 999, "value": 10},
        {"addr": 1, "value": 70000},
        {"addr": True, "value": 100},
        {"addr": 2, "value": "invalid"}
    ])

    results = validate_ai_cases(sample_ai_output, spec)

    print("\nAI validation results:")

    for result in results:
        print(result)

    print(f"Accepted proposals: {len(results)}")
    print(f"Rejected proposals: {7 - len(results)}")

if __name__ == "__main__":
    registers = load_spec()
    cases = generate_boundary_cases(registers)
    
    print(f"Generated {len(cases)} boundary test cases")

    for case in cases:
        print(case)
    demo_ai_validation(registers)
