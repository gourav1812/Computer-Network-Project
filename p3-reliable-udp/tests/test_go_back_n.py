
import socket
import unittest
from unittest.mock import Mock

from p3_rudp.packet import (
    ACK, DATA, FIN_ACK, Packet, encode
)
from p3_rudp.protocols.go_back_n import (
    GoBackNSender, GoBackNReceiver
)


class TestGoBackN(unittest.TestCase):

    def test_sender_sends_data_and_fin(self):
        sock = Mock()
        peer = ("127.0.0.1", 9000)

        # First response acknowledges packet 0.
        # Second response acknowledges the FIN.
        sock.recvfrom.side_effect = [
            (encode(Packet(type=ACK, ack=0)), peer),
            (encode(Packet(type=FIN_ACK, ack=0)), peer),
        ]

        sender = GoBackNSender(
            sock=sock,
            peer=peer,
            window=1,
            max_retries=2,
        )
        sender.send_chunks([b"hello"])

        sent_packets = [
            encode_call.args[0]
            for encode_call in sock.sendto.call_args_list
        ]

        from p3_rudp.packet import decode
        decoded = [decode(data) for data in sent_packets]

        self.assertEqual(decoded[0].type, DATA)
        self.assertEqual(decoded[0].seq, 0)
        self.assertEqual(decoded[-1].type, "FIN")

    def test_receiver_accepts_in_order_data(self):
        sock = Mock()
        peer = ("127.0.0.1", 9001)

        sock.recvfrom.side_effect = [
            (encode(Packet(type=DATA, seq=0, payload=b"hello")), peer),
            (encode(Packet(type=DATA, seq=1, payload=b"world")), peer),
            (encode(Packet(type="FIN", seq=2)), peer),
        ]

        receiver = GoBackNReceiver(sock=sock, peer=peer)
        chunks = receiver.receive_chunks()

        self.assertEqual(chunks, [b"hello", b"world"])
        self.assertEqual(sock.sendto.call_count, 3)


if __name__ == "__main__":
    unittest.main()
