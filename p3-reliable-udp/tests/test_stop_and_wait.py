
import unittest
import socket
from unittest.mock import Mock

from p3_rudp.stop_and_wait import send_stop_and_wait


class TestStopAndWait(unittest.TestCase):

    def test_packet_acknowledged(self):
        sock = Mock()
        sock.recvfrom.return_value = (
            b"ACK1", ("127.0.0.1", 9000)
        )

        result = send_stop_and_wait(
            sock=sock,
            packets=[(1, b"DATA1")],
            receiver_addr=("127.0.0.1", 9000),
            get_ack_seq=lambda data: int(data[3:]),
            timeout=1.0,
            max_retries=2
        )

        self.assertTrue(result)
        sock.sendto.assert_called_once_with(
            b"DATA1", ("127.0.0.1", 9000)
        )

    def test_retransmission_after_timeout(self):
        sock = Mock()
        sock.recvfrom.side_effect = [
            socket.timeout,
            (b"ACK1", ("127.0.0.1", 9000))
        ]

        result = send_stop_and_wait(
            sock=sock,
            packets=[(1, b"DATA1")],
            receiver_addr=("127.0.0.1", 9000),
            get_ack_seq=lambda data: int(data[3:]),
            timeout=1.0,
            max_retries=2
        )

        self.assertTrue(result)
        self.assertEqual(sock.sendto.call_count, 2)

    def test_failure_after_retries(self):
        sock = Mock()
        sock.recvfrom.side_effect = socket.timeout

        with self.assertRaises(TimeoutError):
            send_stop_and_wait(
                sock=sock,
                packets=[(1, b"DATA1")],
                receiver_addr=("127.0.0.1", 9000),
                get_ack_seq=lambda data: int(data[3:]),
                timeout=1.0,
                max_retries=2
            )

        self.assertEqual(sock.sendto.call_count, 3)
        
    def test_ignores_ack_from_wrong_address(self):
        sock = Mock()
        sock.recvfrom.side_effect = [
            (b"ACK1", ("127.0.0.2", 9000)),
            (b"ACK1", ("127.0.0.1", 9000))
        ]

        result = send_stop_and_wait(
            sock=sock,
            packets=[(1, b"DATA1")],
            receiver_addr=("127.0.0.1", 9000),
            get_ack_seq=lambda data: int(data[3:]),
            timeout=1.0,
            max_retries=2
        )

        self.assertTrue(result)
        sock.sendto.assert_called_once_with(
            b"DATA1", ("127.0.0.1", 9000)
        )

    def test_ignores_wrong_sequence_ack(self):
        sock = Mock()
        sock.recvfrom.side_effect = [
            (b"ACK2", ("127.0.0.1", 9000)),
            (b"ACK1", ("127.0.0.1", 9000))
        ]

        result = send_stop_and_wait(
            sock=sock,
            packets=[(1, b"DATA1")],
            receiver_addr=("127.0.0.1", 9000),
            get_ack_seq=lambda data: int(data[3:]),
            timeout=1.0,
            max_retries=2
        )

        self.assertTrue(result)
        sock.sendto.assert_called_once_with(
            b"DATA1", ("127.0.0.1", 9000)
        )



if __name__ == "__main__":
    unittest.main()
