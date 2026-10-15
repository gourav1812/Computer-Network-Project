
import socket


def send_stop_and_wait(
    sock,
    packets,
    receiver_addr,
    get_ack_seq,
    timeout=1.0,
    max_retries=5
):
    """
    Send packets using Stop-and-Wait ARQ.

    packets: list of (sequence_number, packet_bytes)
    get_ack_seq: function that extracts the ACK sequence number
    """

    sock.settimeout(timeout)

    for seq, packet in packets:
        acknowledged = False

        for attempt in range(max_retries + 1):
            # Send the current packet
            sock.sendto(packet, receiver_addr)

            try:
                # Wait for an acknowledgement
                data, address = sock.recvfrom(4096)

                ack_seq = get_ack_seq(data)

                if ack_seq == seq:
                    acknowledged = True
                    break

            except socket.timeout:
                # No ACK arrived before the timeout
                pass

        if not acknowledged:
            raise TimeoutError(
                f"Packet {seq} failed after "
                f"{max_retries} retries"
            )

    return True
