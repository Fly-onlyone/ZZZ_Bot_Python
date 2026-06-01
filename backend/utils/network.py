"""Network helpers for backend startup."""

import socket


def find_free_port(preferred: int, host: str = "127.0.0.1") -> int:
    """Return ``preferred`` if it can be bound, otherwise an OS-allocated free port.

    Probes by binding a fresh socket. ``SO_REUSEADDR`` is intentionally NOT set:
    on Windows it lets two sockets share a port, which would give a false
    "available" reading for a port already in use by another process.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, preferred))
            return preferred
        except OSError:
            pass

    # Preferred port is taken — let the OS hand us a free one.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as fallback:
        fallback.bind((host, 0))
        return fallback.getsockname()[1]
