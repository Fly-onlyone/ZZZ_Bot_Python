import threading
from copy import deepcopy
from typing import Callable


def schedule_mission_email_delivery(
    todays_data: dict,
    *,
    exit_after_run: bool,
    send_func: Callable[[dict], None],
    thread_factory: Callable[..., threading.Thread] = threading.Thread,
) -> threading.Thread | None:
    """Send synchronously for exit-after-run, otherwise dispatch a daemon worker."""

    payload = deepcopy(todays_data)
    if exit_after_run:
        send_func(payload)
        return None

    worker = thread_factory(
        target=send_func,
        args=(payload,),
        name="mission-email-sender",
        daemon=True,
    )
    worker.start()
    return worker
