"""GUI-independent phase events with bounded reporting frequency."""

from dataclasses import dataclass
from time import monotonic


@dataclass(frozen=True)
class PhaseProgress:
    phase: str
    detail: str = ""
    messages: int = 0


class PhaseReporter:
    def __init__(self, callback=None):
        self.callback = callback
        self.phase = None
        self.last = 0

    def __call__(self, phase, detail="", messages=0):
        now = monotonic()
        if self.callback and (phase != self.phase or now - self.last >= 0.15):
            self.callback(PhaseProgress(phase, detail, messages))
            self.last = now
        self.phase = phase


def report(store, phase, detail=""):
    callback = getattr(store, "phase_progress", None)
    if callback:
        callback(phase, detail, len(store))
