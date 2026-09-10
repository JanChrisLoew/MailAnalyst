"""Phase, message count and elapsed clock; all updates occur on Tk's thread."""

import tkinter as tk
from tkinter import ttk
from time import monotonic


class ProcessingDisplay:
    def __init__(self, step, parent):
        self.step = step
        self.app = step.app
        self.started = None
        self.timer = None
        self.messages = 0
        self.sources = tk.StringVar(value="")
        self.clock = tk.StringVar(value="")
        ttk.Label(parent, textvariable=self.sources, style="Subtitle.TLabel").grid(row=5, column=0, sticky="w")
        ttk.Label(parent, textvariable=self.clock, style="Subtitle.TLabel").grid(row=6, column=0, sticky="w", pady=10)

    def start(self, count):
        self.stop()
        self.started, self.messages = monotonic(), 0
        self.sources.set(f"0 von {count} Quellen verarbeitet")
        self.step.processing_status.set("Quellen prüfen")
        self.step.processing_detail.set("Verarbeitung wird vorbereitet")
        self.step.processing_progress.configure(mode="indeterminate", maximum=100, value=0)
        self.step.processing_progress.start(20)
        self._tick()

    def update(self, event):
        self.messages = event.messages
        self.step.processing_status.set(event.phase)
        self.step.processing_detail.set(event.detail)
        self._refresh_clock()

    def _refresh_clock(self):
        if self.started is None:
            return
        elapsed = int(monotonic() - self.started)
        self.clock.set(f"{self.messages} Nachrichten gelesen · Laufzeit {elapsed // 60:02d}:{elapsed % 60:02d}")

    def _tick(self):
        self._refresh_clock()
        self.timer = self.app.after(250, self._tick)

    def stop(self):
        self._refresh_clock()
        if self.timer is not None:
            self.app.after_cancel(self.timer)
            self.timer = None
        self.step.processing_progress.stop()
