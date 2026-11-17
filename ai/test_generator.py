
import json
import os
import re
from pathlib import Path

from openai import OpenAI


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
        ok   : Valid register write
        exc2 : Undefined or read-only register
        exc3 : Illegal register value
    """
    register = spec.get(str(addr))

    if register is None or register["access"] != "rw":
        return "exc2"

    if type(value) is not int:
        return "exc3"

    if not 0 <= value <= 65535:
        return "exc3"

    if addr == 0 and (value & ~0x07):
        return "exc3"

    if value < register["min"] or value > register["max"]:
        return "exc3"

    return "ok"


def boundary_cases(spec):
    """Generate deterministic boundary-value test cases."""
    cases = []

    for addr, register in spec.items():
        if register["access"] != "rw":
            continue

        addr = int(addr)
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

        if addr == 0:
            values.update([1, 2, 4, 5, 8, 0x80, 0x8000])

        for value in sorted(values):
            if 0 <= value <= 65535:
                cases.append({
                    "addr": addr,
                    "value": value,
                    "expected": oracle(spec, addr, value),
                })

    return cases


def validate_llm_cases(spec, raw_text):
    """
    Extract and validate LLM-proposed JSON test cases.

    The LLM never determines expected results.
    The specification oracle does.
    """
    if not isinstance(raw_text, str):
        return []

    try:
        proposals = json.loads(raw_text)
    except json.JSONDecodeError:
        # Also support JSON surrounded by explanatory text.
        match = re.search(r"\[[\s\S]*\]", raw_text)

        if not match:
            return []

        try:
            proposals = json.loads(match.group(0))
        except json.JSONDecodeError:
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


def ask_llm(spec):
    """
    Ask an OpenAI-compatible model to propose test inputs.

    Returns raw model output, or None if unavailable.
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None

    try:
        client = OpenAI(api_key=api_key)

        prompt = f"""
You are helping generate test inputs for a simulated VFD
using Modbus TCP.

Register specification:
{json.dumps(spec, indent=2)}

Suggest up to 15 additional interesting register write
test inputs.

Explore unusual values, boundaries and control-word
bit combinations.

Return ONLY a JSON array.

Each item must have this structure:
{{"addr": 0, "value": 8}}

Do not provide expected results.
Do not invent register addresses.
"""

        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": "Return valid JSON test inputs only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.2,
            timeout=15,
        )

        return response.choices[0].message.content

    except Exception as error:
        print(f"LLM unavailable; using rule-based cases: {error}")
        return None


def generate(spec=None, llm_function=None):
    """
    Merge rule-based and optional LLM-generated test cases.

    Rule-based cases always remain available.
    """
    if spec is None:
        spec = load_spec()

    cases = boundary_cases(spec)

    if llm_function is None:
        llm_function = ask_llm

    try:
        raw_output = llm_function(spec)
        if raw_output:
            cases.extend(validate_llm_cases(spec, raw_output))
    except Exception as error:
        print(f"LLM proposal failed; continuing without it: {error}")

    unique_cases = {}

    for case in cases:
        key = (case["addr"], case["value"])
        unique_cases[key] = {
            "addr": case["addr"],
            "value": case["value"],
            "expected": oracle(spec, case["addr"], case["value"]),
        }

    return list(unique_cases.values())


if __name__ == "__main__":
    registers = load_spec()
    cases = generate(registers)

    print(f"Generated {len(cases)} unique test cases")

    for case in cases:
        print(case)
# Backward compatibility with existing project tests
generate_boundary_cases = boundary_cases

def validate_ai_cases(raw_output, spec):
    return validate_llm_cases(spec, raw_output)