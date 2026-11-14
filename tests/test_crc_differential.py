import os
import random
import subprocess
from pathlib import Path

EXE_NAME = "crc_cli.exe" if os.name == "nt" else "crc_cli"

EXE_PATH = (
    Path(__file__).resolve().parents[1]
    / "cpp"
    / "tests"
    / EXE_NAME
)

def python_crc16(data):
    crc = 0xFFFF

    for byte in data:
        crc ^= byte

        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1

    return crc


def cpp_crc16(data):
    result = subprocess.run(
        [str(EXE_PATH), *[f"{byte:02X}" for byte in data]],
        capture_output=True,
        text=True,
        check=True
    )

    return int(result.stdout.strip(), 16)


def test_cpp_matches_python_crc():
    assert EXE_PATH.exists(), f"C++ executable not found: {EXE_PATH}"

    test_vectors = [
        bytes.fromhex("01030000000A"),
        bytes.fromhex("010600010003"),
        bytes.fromhex("1103006B0003"),
        bytes.fromhex("000000000000"),
        bytes.fromhex("FFFFFFFF"),
    ]

    rng = random.Random(42)

    for _ in range(20):
        length = rng.randint(1, 100)
        test_vectors.append(
            bytes(rng.randint(0, 255) for _ in range(length))
        )

    for data in test_vectors:
        expected = python_crc16(data)
        actual = cpp_crc16(data)

        assert actual == expected, (
            f"CRC mismatch for {data.hex().upper()}: "
            f"Python={expected:04X}, C++={actual:04X}"
        )
