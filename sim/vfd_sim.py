
import json
import socketserver
import struct
from pathlib import Path

SPEC_PATH = Path(__file__).resolve().parents[1] / "spec" / "register_map.json"

with open(SPEC_PATH, "r", encoding="utf-8") as f:
    SPEC = json.load(f)["registers"]


class VFD:
    def __init__(self):
        self.reg = {int(a): 0 for a in SPEC}
        self.reg.update({2: 10, 3: 10, 102: 25})
        self.fault = False

    def update(self):
        running = bool(self.reg[0] & 1)

        if running and self.reg[1] >= 480:
            self.fault = True

        if self.fault:
            self.reg.update({100: 4, 101: 0, 103: 15})
        else:
            self.reg[100] = 1 | (2 if running else 0)
            self.reg[101] = self.reg[1] if running else 0
            self.reg[103] = 0

            if running:
                self.reg[100] |= 8

    def read(self, address, quantity):
        addresses = list(range(address, address + quantity))

        if any(a not in self.reg for a in addresses):
            raise ValueError(2)

        self.update()
        return [self.reg[a] for a in addresses]

    def write(self, address, values):
        if not values:
            raise ValueError(3)

        addresses = list(range(address, address + len(values)))

        # Validate the entire write before changing any register.
        for a, value in zip(addresses, values):
            if a not in self.reg:
                raise ValueError(2)

            rule = SPEC[str(a)]

            if rule["access"] != "rw":
                raise ValueError(2)

            if not rule["min"] <= value <= rule["max"]:
                raise ValueError(3)

            if a == 0 and value & ~7:
                raise ValueError(3)

        # Apply only after every value passes validation.
        for a, value in zip(addresses, values):
            if a == 0 and value & 4:
                self.fault = False
                value &= ~4

            self.reg[a] = value

        self.update()


DEVICE = VFD()


def process_pdu(pdu):
    if not pdu:
        return None

    fc = pdu[0]

    try:
        # Read Holding Registers / Read Input Registers
        if fc in (3, 4):
            if len(pdu) != 5:
                return bytes([fc | 128, 3])

            address, quantity = struct.unpack(">HH", pdu[1:])

            if not 1 <= quantity <= 125:
                return bytes([fc | 128, 3])

            values = DEVICE.read(address, quantity)
            data = b"".join(struct.pack(">H", v) for v in values)

            return bytes([fc, len(data)]) + data

        # Write Single Register
        if fc == 6:
            if len(pdu) != 5:
                return bytes([fc | 128, 3])

            address, value = struct.unpack(">HH", pdu[1:])
            DEVICE.write(address, [value])

            return pdu

        # Write Multiple Registers
        if fc == 16:
            if len(pdu) < 6:
                return bytes([fc | 128, 3])

            address, quantity, count = struct.unpack(">HHB", pdu[1:6])

            if not 1 <= quantity <= 123 or count != quantity * 2:
                return bytes([fc | 128, 3])

            if len(pdu) != 6 + count:
                return bytes([fc | 128, 3])

            values = struct.unpack(f">{quantity}H", pdu[6:])
            DEVICE.write(address, list(values))

            return struct.pack(">BHH", fc, address, quantity)

        return bytes([fc | 128, 1])

    except ValueError as error:
        return bytes([fc | 128, error.args[0]])


def recv_exact(sock, size):
    data = bytearray()

    while len(data) < size:
        chunk = sock.recv(size - len(data))

        if not chunk:
            raise ConnectionError("Disconnected")

        data.extend(chunk)

    return bytes(data)


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        while True:
            try:
                header = recv_exact(self.request, 7)
                tid, pid, length, unit = struct.unpack(">HHHB", header)

                if pid != 0 or not 2 <= length <= 254:
                    return

                pdu = recv_exact(self.request, length - 1)
                response = process_pdu(pdu)

                if response is None:
                    return

                mbap = struct.pack(
                    ">HHHB", tid, 0, len(response) + 1, unit
                )

                self.request.sendall(mbap + response)

            except (ConnectionError, OSError):
                return


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with Server(("127.0.0.1", 5020), Handler) as server:
        print("VFD Simulator running on 127.0.0.1:5020")
        print("Press Ctrl+C to stop.")

        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()
