"""Sender DDP (Distributed Display Protocol) via UDP para WLED."""
import socket

DDP_PORT = 4048
HEADER_LEN = 10
MAX_PAYLOAD = 1440


def build_packet(data, seq, offset=0, push=True):
    flags = 0x40 | (0x01 if push else 0)  # versão 1 + push
    return (
        bytes([flags, seq & 0x0F or 1, 0x01, 0x01])  # tipo RGB, id 1
        + offset.to_bytes(4, "big")
        + len(data).to_bytes(2, "big")
        + data
    )


class DDPSender:
    def __init__(self, host, port=DDP_PORT):
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.seq = 0

    def send(self, data):
        """Envia `data` (RGB contíguo), fragmentando se passar de 1440 bytes."""
        self.seq = self.seq % 15 + 1
        for off in range(0, len(data), MAX_PAYLOAD):
            chunk = data[off:off + MAX_PAYLOAD]
            last = off + MAX_PAYLOAD >= len(data)
            self.sock.sendto(build_packet(chunk, self.seq, off, push=last), self.addr)

    def close(self):
        self.sock.close()
