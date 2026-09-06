"""One non-daemon worker; callbacks and shutdown run on the Tk thread."""

import queue
import threading

from mailanalyst.cancellation import Cancellation, Cancelled


class BackgroundJobs:
    def __init__(self, root):
        self.root = root
        self.events = queue.Queue()
        self.thread = None
        self.cancel_token = None
        self.closing = False
        self.stopped = False
        self._completion = None
        self._after = self.root.after(50, self._poll)

    @property
    def busy(self):
        return self.thread is not None

    def submit(self, work, on_success, on_error, on_progress, on_cancel=None):
        if self.busy or self.closing:
            return False
        token = self.cancel_token = Cancellation()

        def progress(*args):
            token.check()
            self.events.put(("progress", on_progress, args))

        progress.cancel_token = token

        def run():
            try:
                token.check()
                result = work(progress)
                token.begin_commit()
            except Cancelled as exc:
                event = (on_cancel or on_error, (str(exc),))
            except Exception as exc:
                event = (on_error, (str(exc),))
            else:
                event = (on_success, (result,))
            self.events.put(("done", *event))

        self.thread = threading.Thread(target=run, daemon=False)
        self.root._set_job_active(True)
        try:
            self.thread.start()
        except Exception:
            self.thread = None
            self.root._set_job_active(False)
            raise
        return True

    def cancel(self):
        return self.cancel_token.request() if self.busy else False

    def close(self, on_closed):
        self.closing = True
        self.on_closed = on_closed
        if self.busy:
            self.cancel()
        else:
            self._finish_close()

    def _finish_close(self):
        self.stopped = True
        self.root.after_cancel(self._after)
        self.on_closed()

    def _drain_events(self):
        for _ in range(100):
            try:
                kind, callback, args = self.events.get_nowait()
            except queue.Empty:
                return
            if kind == "done":
                self._completion = (callback, args)
            elif not self.closing:
                callback(*args)

    def _poll(self):
        try:
            self._drain_events()
            if self._completion is not None and not self.thread.is_alive():
                self.thread.join()
                self.thread = None
                callback, args = self._completion
                self._completion = None
                self.root._set_job_active(False)
                if self.closing:
                    self._finish_close()
                else:
                    callback(*args)
        finally:
            if not self.stopped:
                self._after = self.root.after(50, self._poll)
