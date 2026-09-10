"""Preflight step: its widgets and user interactions."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
from mailanalyst.checks.preflight import PreflightResult
from mailanalyst.checks.system import write_system_check_report
from mailanalyst.services import check_sources
from mailanalyst.checks.targets import validate_source_target
from mailanalyst.gui.paging import Pager, PAGE_SIZE, scrollable_table


class PreflightStep:
    def __init__(self, app):
        self.app = app

    def _build_preflight_tab(self) -> None:
        tab = self.app.preflight_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(4, weight=1)
        ttk.Label(tab, text="Quelldateien vorprüfen", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(tab, text="Prüfergebnisse werden vor der Verarbeitung sichtbar. Auswahl per Doppelklick oder Eingabetaste.",
                  style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(5, 18))
        self.preflight_status = tk.StringVar(value="Noch nicht gestartet")
        ttk.Label(tab, textvariable=self.preflight_status, style="Surface.TLabel", wraplength=620).grid(row=2, column=0, sticky="w", pady=(0, 7))
        self.preflight_progress = ttk.Progressbar(tab, mode="determinate")
        self.preflight_progress.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        columns = ("include", "status", "format", "size", "path", "reason")
        self.preflight_table = scrollable_table(tab, columns)
        for column, title, width in (("include", "Verarbeiten", 100), ("status", "Status", 75),
                                     ("format", "Format", 60), ("size", "MB", 55),
                                     ("path", "Datei", 340), ("reason", "Ergebnis", 300)):
            self.preflight_table.heading(column, text=title)
            self.preflight_table.column(column, width=width, minwidth=width, stretch=column in {"path", "reason"})
        self.preflight_table.tag_configure("ok", background=self.app.COLORS["success_soft"], foreground=self.app.COLORS["success"])
        self.preflight_table.tag_configure("warning", background=self.app.COLORS["warning_soft"], foreground=self.app.COLORS["warning"])
        self.preflight_table.tag_configure("error", background=self.app.COLORS["error_soft"], foreground=self.app.COLORS["error"])
        self.preflight_table.tag_configure("ignored", foreground=self.app.COLORS["muted"])
        self.preflight_table.bind("<Double-1>", self._toggle_preflight_item)
        self.preflight_table.bind("<Return>", self._toggle_preflight_item)
        self.pager = Pager(tab, 5, {"Alle Quellen": "", "Warnungen": "warning", "Fehler": "error", "Ignoriert": "ignored"},
                           self._load_page, self._render_page)
        actions = ttk.Frame(tab, style="Surface.TFrame")
        actions.grid(row=6, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(actions, text="Zurück", command=lambda: self.app._select_step(1)).pack(side="left")
        ttk.Button(actions, text="Warnungen einschließen", command=lambda: self._set_status_included("warning", True)).pack(side="left", padx=6)
        ttk.Button(actions, text="Warnungen ausschließen", command=lambda: self._set_status_included("warning", False)).pack(side="left")
        self.process_button = ttk.Button(actions, text="Verarbeitung starten", style="Primary.TButton",
                                         command=self.app.processing_step._start_processing, state="disabled")
        self.process_button.pack(side="right")

    def _start_preflight(self) -> None:
        if self.app.jobs.busy or self.app.jobs.closing:
            return
        if not self.app.input_path.get().strip().strip('"').strip("'"):
            messagebox.showerror("MailAnalyst", "Bitte zuerst eine Eingabedatei oder einen Eingabeordner auswählen.",
                                 parent=self.app)
            return
        source = self.app.config_step._normalized_path(self.app.input_path.get())
        target = self.app.config_step._normalized_path(self.app.output_dir.get())
        self.app.input_path.set(str(source))
        self.app.output_dir.set(str(target))
        if not source.exists():
            messagebox.showerror("MailAnalyst", f"Der Eingabepfad existiert nicht oder ist nicht erreichbar:\n\n{source}",
                                 parent=self.app)
            return
        try:
            validate_source_target(source, target)
            target.mkdir(parents=True, exist_ok=True)
            write_system_check_report(self.app.system_check_results, target)
        except Exception as exc:
            messagebox.showerror("MailAnalyst", f"Zielordner nicht verwendbar: {exc}", parent=self.app)
            return
        self.app.unlocked_steps = {0, 1, 2}
        self.app.result_output_path.set("")
        self.app._unlock_step(2, select=True)
        self.process_button.configure(state="disabled")
        self.app.preflight_results = []
        self.pager.refresh(reset=True)
        self.preflight_progress["value"] = 0
        for item in self.preflight_table.get_children():
            self.preflight_table.delete(item)
        self.app.jobs.submit(
            lambda progress: check_sources(source, target, progress, cancel=progress.cancel_token),
            self._finish_preflight, lambda error: messagebox.showerror("Vorprüfung", error, parent=self.app),
            self._preflight_progress,
            on_cancel=lambda _: self.preflight_status.set("Vorprüfung abgebrochen"),
        )

    def _preflight_progress(self, done: int, total: int, path: Path) -> None:
        self.preflight_progress["maximum"] = max(total, 1)
        self.preflight_progress["value"] = done
        self.preflight_status.set(f"Prüfe {done} von {total}: {path.name}")

    def _finish_preflight(self, results: list[PreflightResult]) -> None:
        self.app.preflight_results = results
        self.pager.refresh(reset=True)
        counts = {status: sum(result.status == status for result in results) for status in ("ok", "warning", "error", "ignored")}
        self.preflight_status.set(f"{len(results)} Quellen · {counts['ok']} OK · {counts['warning']} Warnungen · "
                                  f"{counts['error']} Fehler · {counts['ignored']} ignoriert")
        self.process_button.configure(state="normal" if any(result.include for result in results) else "disabled")

    def _toggle_preflight_item(self, _event=None) -> None:
        if self.app.jobs.busy or self.app.jobs.closing:
            return
        selected = self.preflight_table.selection()
        if not selected:
            return
        index = int(selected[0])
        result = self.app.preflight_results[index]
        if result.status == "ignored":
            return
        if result.status == "error" and not result.include:
            if not messagebox.askyesno("Problematische Quelle", "Diese Quelle trotzdem einplanen?", parent=self.app):
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
        self.pager.refresh()
        self.process_button.configure(state="normal" if any(item.include for item in self.app.preflight_results) else "disabled")

    def _load_page(self, offset, status):
        rows, total = [], 0
        for index, result in enumerate(self.app.preflight_results):
            if status and result.status != status:
                continue
            if offset <= total < offset + PAGE_SIZE:
                rows.append((index, result))
            total += 1
        return rows, total

    def _render_page(self, rows):
        self.preflight_table.delete(*self.preflight_table.get_children())
        for index, result in rows:
            self.preflight_table.insert("", "end", iid=str(index), values=("Ja" if result.include else "Nein",
                result.status.upper(), result.extension, f"{result.size / 1048576:.2f}", result.path, result.reason),
                tags=(result.status,))
