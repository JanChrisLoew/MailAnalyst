"""Result step: its widgets and user interactions."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
import os
import pandas as pd
from mailanalyst.gui.paging import Pager, scrollable_table
from mailanalyst.review_store import read_review, FIELDS


class ResultStep:
    def __init__(self, app):
        self.app = app

    def show_results(self, frame: pd.DataFrame, planned: int, target: Path) -> None:
        self.preview = frame.head(500)
        self.review_path = target / "exports" / "review.sqlite3"
        self.pager.refresh(reset=True)
        errors = int((frame.get("parse_status", pd.Series(dtype=str)) == "error").sum())
        errors = frame.attrs.get("total_errors", errors)
        total = frame.attrs.get("total_messages", len(frame))
        self.result_status.set(f"{planned} Quellen · {total} Nachrichten · {errors} Parserfehler · "
                               "bis zu 500 Nachrichten pro Seite")
        self.app.result_output_path.set(str(target.resolve()))

    def _build_result_tab(self) -> None:
        tab = self.app.result_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(4, weight=1)
        ttk.Label(tab, text="Verarbeitung abgeschlossen", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(tab, text="Der geprüfte Lauf enthält Ausgabedaten, Index und Protokoll. Details per Doppelklick oder Eingabetaste.",
                  style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(5, 14))
        self.result_status = tk.StringVar(value="")
        ttk.Label(tab, textvariable=self.result_status, style="Surface.TLabel", wraplength=620,
                  font=(self.app.font_family, 11, "bold")).grid(row=2, column=0, sticky="w", pady=(0, 12))
        path_frame = ttk.Frame(tab, style="Surface.TFrame")
        path_frame.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        path_frame.columnconfigure(1, weight=1)
        ttk.Label(path_frame, text="Laufordner", style="Surface.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Entry(path_frame, textvariable=self.app.result_output_path, state="readonly").grid(row=0, column=1, sticky="ew")
        ttk.Button(path_frame, text="Pfad kopieren", command=self._copy_output_path).grid(row=0, column=2, padx=(8, 0))
        columns = FIELDS
        self.result_table = scrollable_table(tab, columns)
        for column, title, width in zip(columns, ("Datum", "Absender", "Betreff", "Format", "Status", "Fehler", "Quelle"),
                                        (140, 190, 340, 70, 80, 280, 330)):
            self.result_table.heading(column, text=title)
            self.result_table.column(column, width=width, minwidth=width, stretch=column in {"subject", "parse_error"})
        self.result_table.bind("<Double-1>", self._show_details)
        self.result_table.bind("<Return>", self._show_details)
        self.pager = Pager(tab, 5, {"Alle Nachrichten": "", "Nur Fehler": "error"}, self._load_page, self._render_page)
        self.page_rows = {}
        self.result_table.tag_configure("error", background=self.app.COLORS["error_soft"], foreground=self.app.COLORS["error"])
        actions = ttk.Frame(tab, style="Surface.TFrame")
        actions.grid(row=6, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(actions, text="Neuer Lauf", command=lambda: self.app._select_step(1)).pack(side="left")
        ttk.Button(actions, text="Log öffnen", command=self._open_log).pack(side="right")
        ttk.Button(actions, text="Laufordner öffnen", style="Primary.TButton", command=self._open_output).pack(side="right", padx=6)

    def _copy_output_path(self) -> None:
        path = self.app.result_output_path.get()
        if not path:
            return
        self.app.clipboard_clear()
        self.app.clipboard_append(path)
        self.app.update_idletasks()

    def _open_output(self) -> None:
        path = Path(self.app.result_output_path.get())
        if path.exists():
            os.startfile(path)

    def _open_log(self) -> None:
        path = Path(self.app.result_output_path.get()) / "parse_log.txt"
        if path.exists():
            os.startfile(path)

    def _load_page(self, offset, status):
        if self.review_path.exists():
            try:
                return read_review(self.review_path, offset, status)
            except Exception as exc:
                messagebox.showerror("Ergebnisindex", f"Ergebnisse konnten nicht geladen werden: {exc}",
                                     parent=self.app)
                return [], 0
        rows = [(index, row.to_dict()) for index, row in self.preview.iterrows()
                if not status or row.get("parse_status") == status]
        return rows[offset:offset + 500], len(rows)

    def _render_page(self, rows):
        self.result_table.delete(*self.result_table.get_children())
        self.page_rows = {str(index): row for index, row in rows}
        for index, row in rows:
            status = row.get("parse_status", "")
            self.result_table.insert("", "end", iid=str(index), values=tuple(row.get(key, "") for key in FIELDS),
                                     tags=("error",) if status == "error" else ())

    def _show_details(self, _event=None):
        selected = self.result_table.selection()
        if selected:
            row = self.page_rows[selected[0]]
            messagebox.showinfo("Nachricht", f"{row.get('subject', '')}\n\nQuelle: {row.get('source_path', '')}"
                                f"\n\nStatus: {row.get('parse_status', '')}\n{row.get('parse_error', '')}",
                                parent=self.app)
