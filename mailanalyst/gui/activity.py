"""Disable editing during work and wait for workers before closing Tk."""

from tkinter import ttk

from mailanalyst.config import LOGGER


class Activity:
    def __init__(self, app):
        self.app = app
        self.saved_states = []

    def set_active(self, active):
        app = self.app
        if app.jobs.closing:
            return
        if active:
            self.saved_states = []
            self._disable(app)
            app.cancel_button.state(["!disabled"])
            app.activity_status.set("Auftrag laeuft")
        else:
            for widget, state in self.saved_states:
                widget.state(["!disabled", *state])
            self.saved_states = []
            app.cancel_button.state(["disabled"])
            app.activity_status.set("")
        app._refresh_navigation()

    def _disable(self, parent):
        for widget in parent.winfo_children():
            if isinstance(widget, (ttk.Button, ttk.Entry, ttk.Combobox, ttk.Checkbutton, ttk.Treeview)):
                self.saved_states.append((widget, widget.state()))
                widget.state(["disabled"])
            self._disable(widget)

    def cancel(self):
        if self.app.jobs.cancel():
            self.app.activity_status.set("Abbruch angefordert.\nAktuelle Operation wird beendet.")
        elif self.app.jobs.busy:
            self.app.activity_status.set("Abschluss laeuft.\nBitte warten.")
        self.app.cancel_button.state(["disabled"])

    def close(self):
        self.cancel()
        self.app.activity_status.set("Wird geschlossen, sobald\nder Auftrag beendet ist.")
        self.app.jobs.close(self._destroy)

    def _destroy(self):
        for handler in LOGGER.handlers[:]:
            handler.close()
            LOGGER.removeHandler(handler)
        for event in self.app.tk.call("after", "info"):
            self.app.after_cancel(event)
        self.app.destroy()
