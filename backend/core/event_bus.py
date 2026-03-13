"""Thread-safe SSE event broadcaster.

Uses stdlib queue.Queue so emit() is safe to call from threading.Thread
contexts (scheduler, hunt mode, playwright tasks).
"""

import json
import logging
import threading
from queue import Full, Queue

logger = logging.getLogger(__name__)

_subscribers: list[Queue] = []
_lock = threading.Lock()


def subscribe(maxsize: int = 100) -> Queue:
    """Register a new SSE client and return its event queue."""
    q: Queue = Queue(maxsize=maxsize)
    with _lock:
        _subscribers.append(q)
    logger.debug("SSE client subscribed (total=%d)", len(_subscribers))
    return q


def unsubscribe(q: Queue) -> None:
    """Remove an SSE client queue."""
    with _lock:
        try:
            _subscribers.remove(q)
        except ValueError:
            pass
    logger.debug("SSE client unsubscribed (total=%d)", len(_subscribers))


def emit(event_type: str, data: dict | None = None) -> None:
    """Broadcast an event to all connected SSE clients.

    Safe to call from any thread. Drops the event for a client
    whose queue is full rather than blocking the automation flow.
    """
    payload = json.dumps(data or {})
    with _lock:
        targets = list(_subscribers)

    delivered = 0
    for q in targets:
        try:
            q.put_nowait((event_type, payload))
            delivered += 1
        except Full:
            logger.warning("SSE client queue full, dropping event: %s", event_type)

    if delivered:
        logger.debug("SSE event '%s' delivered to %d client(s)", event_type, delivered)
