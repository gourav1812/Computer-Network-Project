
import socket
import time

from ..packet import (
    ACK, DATA, FIN, FIN_ACK,
    CorruptPacket, Packet, decode, encode
)
from .base import BaseReceiver, BaseSender


class GoBackNSender(BaseSender):
    def send_chunks(self, chunks: list[bytes]) -> None:
        base = 0
        next_seq = 0
        total = len(chunks)
        window = self.window

        send_times = {}
        retransmitted = set()

        while base < total:
            # Send packets while the window has space
            while next_seq < total and next_seq < base + window:
                packet = Packet(
                    type=DATA,
                    seq=next_seq,
                    payload=chunks[next_seq]
                )

                self.sock.sendto(encode(packet), self.peer)
                send_times[next_seq] = time.monotonic()
                next_seq += 1

            try:
                data, address = self.sock.recvfrom(65535)

                if address != self.peer:
                    continue

                pkt = decode(data)

                if pkt.type != ACK:
                    continue

                # Cumulative ACK: all packets up to pkt.ack are received
                if pkt.ack >= base:
                    old_base = base
                    base = min(pkt.ack + 1, total)

                    # Take RTT samples only for packets never retransmitted
                    for seq in range(old_base, base):
                        if seq in send_times and seq not in retransmitted:
                            self.rto.sample(
                                time.monotonic() - send_times[seq]
                            )

                    # Remove acknowledged packet timing records
                    for seq in range(old_base, base):
                        send_times.pop(seq, None)
                        retransmitted.discard(seq)

            except socket.timeout:
                # Go-Back-N retransmits every outstanding packet
                if base < next_seq:
                    self.rto.backoff()

                    for seq in range(base, next_seq):
                        packet = Packet(
                            type=DATA,
                            seq=seq,
                            payload=chunks[seq]
                        )

                        self.sock.sendto(encode(packet), self.peer)
                        send_times[seq] = time.monotonic()
                        retransmitted.add(seq)

                self.sock.settimeout(self.rto.rto)

        # Send FIN after all data packets are acknowledged
        fin_packet = Packet(type=FIN, seq=total, payload=b"")

        for _ in range(self.max_retries):
            self.sock.sendto(encode(fin_packet), self.peer)

            try:
                data, address = self.sock.recvfrom(65535)

                if address != self.peer:
                    continue

                pkt = decode(data)

                if pkt.type == FIN_ACK:
                    return

            except socket.timeout:
                self.rto.backoff()
                self.sock.settimeout(self.rto.rto)

        raise TimeoutError("FIN was not acknowledged")


class GoBackNReceiver(BaseReceiver):
    def receive_chunks(self) -> list[bytes]:
        expected_seq = 0
        chunks = []

        while True:
            data, address = self.sock.recvfrom(65535)

            if address != self.peer:
                continue

            try:
                pkt = decode(data)
            except CorruptPacket:
                continue

            if pkt.type == DATA:
                if pkt.seq == expected_seq:
                    chunks.append(pkt.payload)
                    expected_seq += 1

                # Always ACK the last in-order packet
                ack_packet = Packet(
                    type=ACK,
                    ack=expected_seq - 1,
                    payload=b""
                )
                self.sock.sendto(encode(ack_packet), self.peer)

            elif pkt.type == FIN:
                fin_ack = Packet(
                    type=FIN_ACK,
                    ack=expected_seq - 1,
                    payload=b""
                )
                self.sock.sendto(encode(fin_ack), self.peer)
                return chunks
