import socket
import time
from ..packet import ACK, DATA, FIN, FIN_ACK, CorruptPacket, Packet, decode, encode
from .base import BaseReceiver, BaseSender

class SelectiveRepeatSender(BaseSender):
    def send_chunks(self, chunks: list[bytes]) -> None:
        base = 0
        next_seq = 0
        n = len(chunks)
        window = self.window

        acked = set()
        deadlines = {}   # seq -> deadline timestamp
        send_times = {}  # seq -> first transmission time
        send_counts = {} # seq -> attempts count

        while base < n:
            now = time.monotonic()
            current_rto = self.rto.rto if self.rto else 1.0

            # 1. Send new packets that fit in the window
            while next_seq < base + window and next_seq < n:
                pkt = Packet(seq=next_seq, ack=0, ptype=DATA, payload=chunks[next_seq])
                self.sock.sendto(encode(pkt), self.peer)
                self.stats.packets_sent += 1
                deadlines[next_seq] = now + current_rto
                send_times[next_seq] = now
                send_counts[next_seq] = 1
                next_seq += 1