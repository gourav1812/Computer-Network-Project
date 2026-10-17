
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
            sock.sendto(packet, receiver_addr)

            try:
                while True:
                    data, address = sock.recvfrom(4096)

                    # Ignore ACKs from unexpected senders
                    if address != receiver_addr:
                        continue

                    # Ignore ACKs for other packets
                    ack_seq = get_ack_seq(data)

                    if ack_seq == seq:
                        acknowledged = True
                        break

                if acknowledged:
                    break

            except socket.timeout:
                # Retry if no valid ACK arrives before timeout
                pass

        if not acknowledged:
            raise TimeoutError(
                f"Packet {seq} failed after "
                f"{max_retries} retries"
            )

    return True
