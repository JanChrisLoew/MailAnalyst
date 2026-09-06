"""Cooperative cancellation with an explicit publication boundary."""

from threading import Lock


class Cancelled(Exception):
    """Requested cancellation reached a safe checkpoint."""


class Cancellation:
    def __init__(self):
        self._lock = Lock()
        self._requested = False
        self._committing = False

    def request(self):
        with self._lock:
            if self._committing:
                return False
            self._requested = True
            return True

    def check(self):
        with self._lock:
            if self._requested:
                raise Cancelled("Verarbeitung abgebrochen")

    def begin_commit(self):
        with self._lock:
            if self._requested:
                raise Cancelled("Verarbeitung abgebrochen")
            self._committing = True


def check_cancel(cancel):
    if cancel is not None:
        cancel.check()
