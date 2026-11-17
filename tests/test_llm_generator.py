
import pytest

from ai.test_generator import (
    load_spec,
    oracle,
    validate_llm_cases,
    generate,
)

SPEC = load_spec()


def test_valid_llm_cases_are_accepted():
    raw = '[{"addr": 0, "value": 3}]'

    cases = validate_llm_cases(SPEC, raw)

    assert len(cases) == 1
    assert cases[0]["addr"] == 0
    assert cases[0]["value"] == 3
    assert cases[0]["expected"] == oracle(SPEC, 0, 3)


def test_unknown_register_is_rejected():
    raw = '[{"addr": 999, "value": 1}]'

    assert validate_llm_cases(SPEC, raw) == []


def test_out_of_range_value_is_rejected():
    raw = '[{"addr": 0, "value": 70000}]'

    assert validate_llm_cases(SPEC, raw) == []


def test_string_values_are_rejected():
    raw = '[{"addr": 0, "value": "3"}]'

    assert validate_llm_cases(SPEC, raw) == []


def test_boolean_values_are_rejected():
    raw = '[{"addr": 0, "value": true}]'

    assert validate_llm_cases(SPEC, raw) == []


def test_invalid_json_is_rejected():
    raw = "This is not JSON"

    assert validate_llm_cases(SPEC, raw) == []


def test_llm_failure_preserves_rule_based_cases():
    cases = generate(
        spec=SPEC,
        llm_function=lambda spec: (_ for _ in ()).throw(
            RuntimeError("Simulated API failure")
        ),
    )

    assert len(cases) > 0

    for case in cases:
        assert case["expected"] == oracle(
            SPEC,
            case["addr"],
            case["value"],
        )


def test_duplicate_cases_are_removed():
    def fake_llm(spec):
        return '[{"addr": 0, "value": 0}]'

    cases = generate(spec=SPEC, llm_function=fake_llm)

    keys = [(case["addr"], case["value"]) for case in cases]

    assert len(keys) == len(set(keys))
