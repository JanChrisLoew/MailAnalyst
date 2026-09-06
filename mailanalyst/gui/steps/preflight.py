"""Preflight step: its widgets and user interactions."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
from mailanalyst.checks.preflight import PreflightResult
from mailanalyst.checks.system import write_system_check_report
from mailanalyst.services import check_sources


class PreflightStep:
    def __init__(self, app):
        self.app = app

    def _build_preflight_tab(self) -> None:
        tab = self.app.preflight_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(4, weight=1)
        ttk.Label(tab, text="Quelldateien vorpruefen", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(tab, text="Fehlerhafte oder unvollstaendige Dateien werden vor der eigentlichen Verarbeitung sichtbar.",
                  style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(5, 18))
        self.preflight_status = tk.StringVar(value="Noch nicht gestartet")
        ttk.Label(tab, textvariable=self.preflight_status, style="Surface.TLabel").grid(row=2, column=0, sticky="w", pady=(0, 7))
        self.preflight_progress = ttk.Progressbar(tab, mode="determinate")
        self.preflight_progress.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        columns = ("include", "status", "format", "size", "path", "reason")
        self.preflight_table = ttk.Treeview(tab, columns=columns, show="headings")
        for column, title, width in (("include", "Verarbeiten", 85), ("status", "Status", 80), ("format", "Format", 65),
                                     ("size", "MB", 70), ("path", "Datei", 390), ("reason", "Ergebnis", 350)):
            self.preflight_table.heading(column, text=title)
            self.preflight_table.column(column, width=width, stretch=column in {"path", "reason"})
        self.preflight_table.grid(row=4, column=0, sticky="nsew")
        self.preflight_table.tag_configure("ok", background=self.app.COLORS["success_soft"], foreground=self.app.COLORS["success"])
        self.preflight_table.tag_configure("warning", background=self.app.COLORS["warning_soft"], foreground=self.app.COLORS["warning"])
        self.preflight_table.tag_configure("error", background=self.app.COLORS["error_soft"], foreground=self.app.COLORS["error"])
        self.preflight_table.tag_configure("ignored", foreground=self.app.COLORS["muted"])
        self.preflight_table.bind("<Double-1>", self._toggle_preflight_item)
        actions = ttk.Frame(tab, style="Surface.TFrame")
        actions.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(actions, text="←  Zurueck", command=lambda: self.app._select_step(1)).pack(side="left")
        ttk.Button(actions, text="Warnungen einschliessen", command=lambda: self._set_status_included("warning", True)).pack(side="left", padx=6)
        ttk.Button(actions, text="Warnungen ausschliessen", command=lambda: self._set_status_included("warning", False)).pack(side="left")
        self.process_button = ttk.Button(actions, text="Verarbeitung starten  →", style="Primary.TButton",
                                         command=self.app.processing_step._start_processing, state="disabled")
        self.process_button.pack(side="right")

    def _start_preflight(self) -> None:
        if self.app.jobs.busy or self.app.jobs.closing:
            return
        if not self.app.input_path.get().strip().strip('"').strip("'"):
            messagebox.showerror("MailAnalyst", "Bitte zuerst eine Eingabedatei oder einen Eingabeordner auswaehlen.")
            return
        source = self.app.config_step._normalized_path(self.app.input_path.get())
        target = self.app.config_step._normalized_path(self.app.output_dir.get())
        self.app.input_path.set(str(source))
        self.app.output_dir.set(str(target))
        if not source.exists():
            messagebox.showerror("MailAnalyst", f"Der Eingabepfad existiert nicht oder ist nicht erreichbar:\n\n{source}")
            return
        try:
            target.mkdir(parents=True, exist_ok=True)
            write_system_check_report(self.app.system_check_results, target)
        except Exception as exc:
            messagebox.showerror("MailAnalyst", f"Zielordner nicht verwendbar: {exc}")
            return
        self.app.unlocked_steps = {0, 1, 2}
        self.app.result_output_path.set("")
        self.app._unlock_step(2, select=True)
        self.process_button.configure(state="disabled")
        self.app.preflight_results = []
        self.preflight_progress["value"] = 0
        for item in self.preflight_table.get_children():
            self.preflight_table.delete(item)
        self.app.jobs.submit(
            lambda progress: check_sources(source, target, progress, cancel=progress.cancel_token),
            self._finish_preflight, lambda error: messagebox.showerror("Vorpruefung", error),
            self._preflight_progress,
            on_cancel=lambda _: self.preflight_status.set("Vorpruefung abgebrochen"),
        )

    def _preflight_progress(self, done: int, total: int, path: Path) -> None:
        self.preflight_progress["maximum"] = max(total, 1)
        self.preflight_progress["value"] = done
        self.preflight_status.set(f"Pruefe {done} von {total}: {path.name}")

    def _finish_preflight(self, results: list[PreflightResult]) -> None:
        self.app.preflight_results = results
        for index, result in enumerate(results):
            self.preflight_table.insert("", "end", iid=str(index), values=("Ja" if result.include else "Nein", result.status.upper(),
                result.extension, f"{result.size / 1048576:.2f}", result.path, result.reason), tags=(result.status,))
        counts = {status: sum(result.status == status for result in results) for status in ("ok", "warning", "error", "ignored")}
        self.preflight_status.set(f"Fertig: {len(results)} | OK {counts['ok']} | Warnungen {counts['warning']} | Fehler {counts['error']} | Ignoriert {counts['ignored']}")
        self.process_button.configure(state="normal" if any(result.include for result in results) else "disabled")

    def _toggle_preflight_item(self, _event=None) -> None:
        if self.app.jobs.busy or self.app.jobs.closing:
            return
        selected = self.preflight_table.selection()
        if not selected:
            return
        index = int(selected[0])
        result = self.app.preflight_results[index]
        if result.status in {"error", "ignored"} and not result.include:
            if not messagebox.askyesno("Problematische Quelle", "Diese Quelle trotzdem einplanen?"):
                return
        result.include = not result.include
        self.preflight_table.set(selected[0], "include", "Ja" if result.include else "Nein")
        self.process_button.configure(state="normal" if any(item.include for item in self.app.preflight_results) else "disabled")

    def _set_status_included(self, status: str, included: bool) -> None:
        if self.app.jobs.busy or self.app.jobs.closing:
            return
        for index, result in enumerate(self.app.preflight_results):
            if result.status == status:
                result.include = included
                self.preflight_table.set(str(index), "include", "Ja" if included else "Nein")
        self.process_button.configure(state="normal" if any(item.include for item in self.app.preflight_results) else "disabled")
