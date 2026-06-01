import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.network import find_free_port


def _is_bindable(port: int, host: str = "127.0.0.1") -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, port))
            return True
        except OSError:
            return False


def test_returns_preferred_port_when_free():
    # Grab a free port, release it, then ask for it — it should be handed back.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as scratch:
        scratch.bind(("127.0.0.1", 0))
        preferred = scratch.getsockname()[1]

    assert find_free_port(preferred) == preferred


def test_falls_back_when_preferred_port_in_use():
    # Hold a socket on the preferred port so the probe bind fails.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen()
        preferred = occupied.getsockname()[1]

        resolved = find_free_port(preferred)

    assert resolved != preferred
    assert resolved > 0
    assert _is_bindable(resolved)
