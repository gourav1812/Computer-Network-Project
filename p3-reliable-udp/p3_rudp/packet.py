
import json
import base64
from dataclasses import dataclass

DATA = "DATA"
ACK = "ACK"
FIN = "FIN"
FIN_ACK = "FIN_ACK"


class CorruptPacket(Exception):
    """Raised when a packet cannot be decoded."""


@dataclass
class Packet:
    type: str
    seq: int = 0
    ack: int = -1
    payload: bytes = b""


def encode(packet: Packet) -> bytes:
    data = {
        "type": packet.type,
        "seq": packet.seq,
        "ack": packet.ack,
        "payload": base64.b64encode(packet.payload).decode("ascii"),
    }
    return json.dumps(data).encode("utf-8")


def decode(data: bytes) -> Packet:
    try:
        obj = json.loads(data.decode("utf-8"))
        return Packet(
            type=obj["type"],
            seq=int(obj.get("seq", 0)),
            ack=int(obj.get("ack", -1)),
            payload=base64.b64decode(obj.get("payload", ""), validate=True),
        )
    except (ValueError, TypeError, KeyError, UnicodeDecodeError) as exc:
        raise CorruptPacket("Invalid packet") from exc
