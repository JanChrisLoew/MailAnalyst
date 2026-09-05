"""Deliver background results on the Tk main thread via a queue."""

import queue
import threading


class BackgroundJobs:
    def __init__(self, root):
        self.root = root
        self.events = queue.Queue()
        self.root.after(50, self._poll)

    def submit(self, work, on_success, on_error, on_progress):
        def progress(*args):
            self.events.put((on_progress, args))

        def run():
            try:
                result = work(progress)
            except Exception as exc:
                self.events.put((on_error, (str(exc),)))
            else:
                self.events.put((on_success, (result,)))

        threading.Thread(target=run, daemon=True).start()

    def _poll(self):
        try:
            for _ in range(100):
                callback, args = self.events.get_nowait()
                callback(*args)
        except queue.Empty:
            pass
        finally:
            self.root.after(50, self._poll)
