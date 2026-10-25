from ..rto import AdaptiveRTO


class BaseSender:
    def __init__(
        self,
        sock,
        peer,
        window=4,
        max_retries=5,
        rto=None,
    ):
        self.sock = sock
        self.peer = peer
        self.window = window
        self.max_retries = max_retries
        self.rto = rto if rto is not None else AdaptiveRTO()

        self.sock.settimeout(self.rto.rto)


class BaseReceiver:
    def __init__(self, sock, peer):
        self.sock = sock
        self.peer = peer