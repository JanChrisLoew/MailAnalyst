"""System step: its widgets and user interactions."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
from mailanalyst.checks.system import SystemCheckResult, run_system_check


class SystemStep:
    def __init__(self, app):
        self.app = app

    def _build_system_tab(self) -> None:
        tab = self.app.system_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(4, weight=1)
        ttk.Label(tab, text="Lokale Umgebung pruefen", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(tab, text="MailAnalyst prueft die Laufzeit, Importer, Ausgabeformate und grundlegende Systemressourcen.",
                  style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(5, 18))
        self.system_status = tk.StringVar(value="Systemcheck wird vorbereitet")
        ttk.Label(tab, textvariable=self.system_status, style="Surface.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 7))
        self.system_progress = ttk.Progressbar(tab, mode="determinate")
        self.system_progress.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        columns = ("status", "category", "check", "detail")
        self.system_table = ttk.Treeview(tab, columns=columns, show="headings")
        for column, title, width in (("status", "Status", 95), ("category", "Bereich", 135),
                                     ("check", "Pruefung", 230), ("detail", "Ergebnis", 520)):
            self.system_table.heading(column, text=title)
            self.system_table.column(column, width=width, stretch=column == "detail")
        self.system_table.grid(row=4, column=0, sticky="nsew")
        self.system_table.tag_configure("ok", background=self.app.COLORS["success_soft"], foreground=self.app.COLORS["success"])
        self.system_table.tag_configure("warning", background=self.app.COLORS["warning_soft"], foreground=self.app.COLORS["warning"])
        self.system_table.tag_configure("error", background=self.app.COLORS["error_soft"], foreground=self.app.COLORS["error"])
        actions = ttk.Frame(tab, style="Surface.TFrame")
        actions.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        self.system_retry_button = ttk.Button(actions, text="Erneut pruefen", command=self._start_system_check)
        self.system_retry_button.pack(side="left")
        self.system_continue_button = ttk.Button(actions, text="Weiter zu den Daten  →", style="Primary.TButton",
                                                 command=lambda: self.app._select_step(1), state="disabled")
        self.system_continue_button.pack(side="right")

    def _start_system_check(self) -> None:
        if self.app.jobs.busy or self.app.jobs.closing:
            return
        self.app.unlocked_steps = {0}
        self.app.current_step = 0
        self.app.notebook.select(self.app.system_tab)
        self.app._refresh_navigation()
        self.app.system_check_results = []
        self.system_progress["value"] = 0
        self.system_status.set("Systemcheck laeuft ...")
        self.system_retry_button.configure(state="disabled")
        self.system_continue_button.configure(state="disabled")
        for item in self.system_table.get_children():
            self.system_table.delete(item)
        font = self.app.font_family
        self.app.jobs.submit(
            lambda progress: run_system_check(progress, detected_font_family=font),
            self._finish_system_check, self._finish_system_check_error, self._system_check_progress,
            on_cancel=self._cancelled,
        )

    def _system_check_progress(self, done: int, total: int, label: str) -> None:
        self.system_progress["maximum"] = max(total, 1)
        self.system_progress["value"] = done
        self.system_status.set(f"Pruefe {label} ({done} von {total})")

    def _finish_system_check(self, results: list[SystemCheckResult]) -> None:
        self.app.system_check_results = results
        for index, result in enumerate(results):
            self.system_table.insert("", "end", iid=str(index), values=(
                result.status.upper(), result.category, result.name, result.detail
            ), tags=(result.status,))
        counts = {status: sum(result.status == status for result in results) for status in ("ok", "warning", "error")}
        self.system_status.set(
            f"Systemcheck abgeschlossen: OK {counts['ok']} | Warnungen {counts['warning']} | Fehler {counts['error']}"
        )
        self.system_retry_button.configure(state="normal")
        if counts["error"]:
            self.system_continue_button.configure(state="disabled")
        else:
            self.app._unlock_step(1)
            self.system_continue_button.configure(state="normal")

    def _finish_system_check_error(self, error: str) -> None:
        self.system_status.set(f"Systemcheck fehlgeschlagen: {error}")
        self.system_retry_button.configure(state="normal")
        self.system_continue_button.configure(state="disabled")

    def _cancelled(self, _details):
        self.system_status.set("Systemcheck abgebrochen")
        self.system_retry_button.configure(state="normal")
        self.system_continue_button.configure(state="disabled")
