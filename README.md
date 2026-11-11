\# VFD Fieldbus Test Bench



\*\*A software-based testing environment for Variable Frequency Drive (VFD) communication protocols.\*\*



> \*\*Project Status:\*\* In Progress



\## Overview



The VFD Fieldbus Test Bench is a software-based project designed to simulate and test industrial communication between a controller and a Variable Frequency Drive (VFD).



The project currently includes a Python-based Modbus TCP simulator, a custom socket-based Modbus TCP client, automated protocol tests using pytest, and a foundational C++17 library for Modbus RTU frame handling.



The objective is to build a test environment that validates protocol behaviour, handles invalid requests, and eventually incorporates AI-assisted test generation and traffic anomaly detection.



\*\*Note:\*\* This is currently a software simulation environment. It does not require or communicate with a physical VFD.



\## Project Architecture



```text

vfd-fieldbus-testbench/

│

├── ai/                     # AI-assisted testing (planned)

│

├── client/

│   └── modbus\_client.py    # Custom Modbus TCP client

│

├── cpp/

│   ├── include/

│   │   └── modbus\_rtu.hpp

│   ├── src/

│   │   └── modbus\_rtu.cpp

│   └── tests/

│       └── test\_modbus\_rtu.cpp

│

├── sim/

│   └── vfd\_sim.py          # Python VFD simulator

│

├── spec/

│   └── register\_map.json   # Register definitions

│

├── tests/

│   ├── conftest.py

│   └── test\_modbus.py      # Automated protocol tests

│

└── .gitignore

```



\## Implemented Features



\### 1. Python VFD Simulator



A Modbus TCP simulator implemented using Python's standard library.



Current functionality includes:



\- Modbus TCP server operating on localhost (`127.0.0.1:5020`).

\- Function codes FC03 and FC04 for register reads.

\- Function code FC06 for single-register writes.

\- Function code FC16 for multiple-register writes.

\- Register access and value-range validation.

\- Modbus exception handling.

\- Atomicity checks for multiple-register writes.



\### 2. Custom Modbus TCP Client



A custom client implemented using Python socket programming and the `struct` module.



Current functionality includes:



\- MBAP header construction and parsing.

\- Transaction ID validation.

\- Register read and write operations.

\- Multiple-register write support.

\- Response and exception handling.

\- Communication latency logging.



\### 3. Automated Testing with pytest



Automated tests currently cover:



\- Initial register values.

\- Register read operations.

\- Single-register writes.

\- Multiple-register writes.

\- Read-only register restrictions.

\- Invalid register addresses.

\- Out-of-range values.

\- Invalid register quantities.

\- Unsupported function codes.

\- Atomicity of multiple-register writes.



\*\*Current result: 10 pytest tests passing.\*\*



\### 4. C++17 Modbus RTU Frame Library



A foundational C++17 implementation for Modbus RTU frame handling.



Implemented components:



\- CRC16/MODBUS calculation.

\- RTU frame construction.

\- Frame validation.

\- Frame parsing.



The C++ source has been compiled successfully using GCC. Execution of the C++ unit tests is still pending verification in the current Windows environment.



\## Technology Stack



| Area | Technologies |

|---|---|

| Programming | Python, C++17 |

| Communication | Modbus TCP, Modbus RTU |



