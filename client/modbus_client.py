
import socket
import struct
import time


class ModbusException(Exception):
    pass


class ModbusClient:
    def __init__(self, host="127.0.0.1", port=5020, unit_id=1):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.transaction_id = 0
        self.sock = None

    def connect(self):
        self.sock = socket.create_connection(
            (self.host, self.port), timeout=3
        )
        self.sock.settimeout(3)

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def _recv_exact(self, size):
        data = bytearray()

        while len(data) < size:
            chunk = self.sock.recv(size - len(data))

            if not chunk:
                raise ConnectionError("Server disconnected")

            data.extend(chunk)

        return bytes(data)

    def _request(self, pdu):
        if self.sock is None:
            raise ConnectionError("Client is not connected")

        self.transaction_id = (self.transaction_id + 1) % 65536
        tid = self.transaction_id

        mbap = struct.pack(
            ">HHHB",
            tid,
            0,
            len(pdu) + 1,
            self.unit_id
        )

        start = time.perf_counter()
        self.sock.sendall(mbap + pdu)

        header = self._recv_exact(7)
        response_tid, protocol, length, unit = struct.unpack(
            ">HHHB", header
        )

        if response_tid != tid:
            raise ValueError("Transaction ID mismatch")

        if protocol != 0 or unit != self.unit_id:
            raise ValueError("Invalid MBAP header")

        if not 2 <= length <= 254:
            raise ValueError("Invalid response length")

        response = self._recv_exact(length - 1)
        latency = (time.perf_counter() - start) * 1000

        if response[0] & 0x80:
            raise ModbusException(
                f"Modbus exception code: {response[1]}"
            )

        if response[0] != pdu[0]:
            raise ValueError("Function code mismatch")

        print(
            f"FC={pdu[0]}, TID={tid}, "
            f"Latency={latency:.2f} ms, "
            f"Reply={len(response)} bytes"
        )

        return response

    def read_holding_registers(self, address, quantity):
        pdu = struct.pack(">BHH", 3, address, quantity)
        response = self._request(pdu)

        if len(response) < 2:
            raise ValueError("Incomplete read response")

        byte_count = response[1]

        if byte_count != quantity * 2:
            raise ValueError("Unexpected byte count")

        if len(response) != 2 + byte_count:
            raise ValueError("Invalid read response length")

        return list(
            struct.unpack(f">{quantity}H", response[2:])
        )

    def write_single_register(self, address, value):
        pdu = struct.pack(">BHH", 6, address, value)
        response = self._request(pdu)

        if response != pdu:
            raise ValueError("Invalid write response")

        return True

    def write_multiple_registers(self, address, values):
        quantity = len(values)

        data = struct.pack(f">{quantity}H", *values)

        pdu = (
            struct.pack(">BHHB", 16, address, quantity, len(data))
            + data
        )

        response = self._request(pdu)

        expected = struct.pack(">BHH", 16, address, quantity)

        if response != expected:
            raise ValueError("Invalid multiple-write response")

        return True


if __name__ == "__main__":
    client = ModbusClient()

    try:
        client.connect()
        print("Connected to VFD simulator")

        print("Initial registers:", client.read_holding_registers(0, 4))

        client.write_single_register(1, 250)

        print("Updated registers:", client.read_holding_registers(0, 4))

        client.write_multiple_registers(1, [300, 20, 20])

        print("After multiple write:", client.read_holding_registers(0, 4))

    except Exception as error:
        print("Error:", error)

    finally:
        client.close()
