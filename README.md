
# VFD Fieldbus Test Bench

**A software-based testing environment for Variable Frequency Drive (VFD) communication protocols.**

![Status](https://img.shields.io/badge/Status-In%20Progress-orange)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![C++](https://img.shields.io/badge/C%2B%2B-17-blue)
![Protocol](https://img.shields.io/badge/Protocol-Modbus%20TCP%2FRTU-green)

## Overview

The **VFD Fieldbus Test Bench** is a software-based project designed to simulate and test industrial communication between a controller and a Variable Frequency Drive (VFD).

The current implementation consists of a Python-based Modbus TCP simulator, a custom socket-based Modbus TCP client, automated protocol tests using pytest, and a foundational C++17 library for Modbus RTU frame handling.

The project aims to develop a test environment for validating protocol behaviour, handling invalid requests, and exploring AI-assisted test generation and traffic anomaly detection.

> **Note:** This project currently operates as a software simulation environment. It does not communicate with a physical VFD or industrial hardware.

## Project Architecture

```text
vfd-fieldbus-testbench/
│
├── ai/                         # Planned AI-assisted testing
├── client/
│   └── modbus_client.py        # Custom Modbus TCP client
├── cpp/
│   ├── include/
│   │   └── modbus_rtu.hpp      # RTU library declarations
│   ├── src/
│   │   └── modbus_rtu.cpp      # RTU implementation
│   └── tests/
│       └── test_modbus_rtu.cpp # C++ unit tests
├── sim/
│   └── vfd_sim.py              # Python VFD simulator
├── spec/
│   └── register_map.json       # Register definitions
├── tests/
│   ├── conftest.py             # Test fixtures
│   └── test_modbus.py          # Modbus TCP tests
├── .gitignore
└── README.md
```

## Implemented Features

### 1. Python VFD Simulator

A Modbus TCP simulator developed using Python's standard library.

- TCP server operating on `127.0.0.1:5020`.
- FC03 and FC04 register read operations.
- FC06 single-register write operations.
- FC16 multiple-register write operations.
- Register access and value-range validation.
- Modbus exception responses.
- Atomicity checks for multiple-register writes.

### 2. Custom Modbus TCP Client

A custom client developed using Python socket programming and the `struct` module.

- MBAP header construction and parsing.
- Transaction ID validation.
- Register read and write operations.
- Multiple-register write support.
- Response and exception handling.
- Communication latency logging.

### 3. Automated Testing with pytest

The Python test suite currently contains **10 passing tests** covering:

- Initial register values.
- Register read operations.
- Single-register writes.
- Multiple-register writes.
- Read-only register restrictions.
- Invalid register addresses.
- Out-of-range values.
- Invalid register quantities.
- Unsupported function codes.
- Atomicity of multiple-register writes.

### 4. C++17 Modbus RTU Frame Library

A foundational C++17 implementation for Modbus RTU frame handling.

- CRC16/MODBUS calculation.
- RTU frame construction.
- Frame validation.
- Frame parsing.

The C++ source compiles successfully with GCC. Execution of the C++ unit tests and differential verification against the Python CRC implementation remain pending.

## Technology Stack

| Category | Technologies |
|---|---|
| Programming Languages | Python, C++17 |
| Communication Protocols | Modbus TCP, Modbus RTU |
| Networking | TCP Socket Programming |
| Protocol Handling | MBAP Framing, CRC16/MODBUS |
| Testing | pytest |
| Compiler | GCC |
| Version Control | Git, GitHub |

## Getting Started

### Prerequisites

- Python 3.11 or later
- GCC with C++17 support
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/skandhapavithras3010-ux/vfd-fieldbus-testbench.git
cd vfd-fieldbus-testbench
```

### 2. Create a Virtual Environment

**Windows:**

```cmd
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies

```bash
python -m pip install pytest
```

### 4. Run the Test Suite

```bash
python -m pytest -v
```

### 5. Start the VFD Simulator

```bash
python -m sim.vfd_sim
```

The simulator listens on `127.0.0.1:5020`.

## Development Roadmap

- [ ] Expand functional and negative protocol test coverage.
- [ ] Implement seeded fuzz testing for Modbus PDUs.
- [ ] Extend VFD operating-state simulation and fault scenarios.
- [ ] Complete C++ RTU unit testing.
- [ ] Implement Python/C++ CRC differential verification.
- [ ] Develop AI-assisted boundary test generation using a specification-based validation oracle.
- [ ] Implement machine-learning-based traffic anomaly detection.
- [ ] Introduce bug-injection scenarios to evaluate test effectiveness.
- [ ] Integrate the components into a unified testing workflow.

## Project Objective

The long-term objective is to develop a reproducible software test bench combining protocol simulation, automated validation, cross-language protocol handling, and AI-assisted testing to explore the reliability of industrial communication systems.

---

**Development Status:** Active development. Implementation details, test coverage, and project capabilities will be updated as development progresses.
