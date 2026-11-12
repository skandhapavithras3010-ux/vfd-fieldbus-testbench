
import threading
import time
import pytest

from sim.vfd_sim import DEVICE, Server, Handler
from client.modbus_client import ModbusClient


@pytest.fixture
def client():
    # Reset simulator state before each test.
    DEVICE.reg = {
        0: 0,
        1: 0,
        2: 10,
        3: 10,
        100: 0,
        101: 0,
        102: 25,
        103: 0
    }
    DEVICE.fault = False
    DEVICE._output_freq = 0.0
    DEVICE._last_update = time.monotonic()

    server = Server(("127.0.0.1", 0), Handler)
    thread = threading.Thread(
        target=server.serve_forever,
        daemon=True
    )
    thread.start()

    host, port = server.server_address

    test_client = ModbusClient(host=host, port=port)
    test_client.connect()

    yield test_client

    test_client.close()
    server.shutdown()
    server.server_close()
    thread.join(timeout=2)
