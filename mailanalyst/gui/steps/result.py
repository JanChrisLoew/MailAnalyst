"""Result step: its widgets and user interactions."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
import os
import pandas as pd


class ResultStep:
    def __init__(self, app):
        self.app = app

    def show_results(self, frame: pd.DataFrame, planned: int, target: Path) -> None:
        for item in self.result_table.get_children():
            self.result_table.delete(item)
        for _, row in frame.iterrows():
            status = str(row.get("parse_status", ""))
            self.result_table.insert("", "end", values=(row.get("sent_datetime_de", ""), row.get("from_email", ""),
                row.get("subject", ""), row.get("file_ext", ""), status), tags=(("error",) if status == "error" else ()))
        errors = int((frame.get("parse_status", pd.Series(dtype=str)) == "error").sum())
        self.result_status.set(f"{planned} Quellen verarbeitet | {len(frame)} Nachrichten | {errors} Parserfehler")
        self.app.result_output_path.set(str(target.resolve()))

    def _build_result_tab(self) -> None:
        tab = self.app.result_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(4, weight=1)
        ttk.Label(tab, text="Verarbeitung abgeschlossen", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(tab, text="Die Ausgabedaten und das Protokoll liegen jetzt im gewaehlten Zielordner.",
                  style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(5, 14))
        self.result_status = tk.StringVar(value="")
        ttk.Label(tab, textvariable=self.result_status, style="Surface.TLabel",
                  font=(self.app.font_family, 11, "bold")).grid(row=2, column=0, sticky="w", pady=(0, 12))
        path_frame = ttk.Frame(tab, style="Surface.TFrame")
        path_frame.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        path_frame.columnconfigure(1, weight=1)
        ttk.Label(path_frame, text="Zielordner", style="Surface.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Entry(path_frame, textvariable=self.app.result_output_path, state="readonly").grid(row=0, column=1, sticky="ew")
        ttk.Button(path_frame, text="Pfad kopieren", command=self._copy_output_path).grid(row=0, column=2, padx=(8, 0))
        columns = ("date", "from", "subject", "format", "status")
        self.result_table = ttk.Treeview(tab, columns=columns, show="headings")
        for column, title, width in (("date", "Datum", 145), ("from", "Absender", 220), ("subject", "Betreff", 480),
                                     ("format", "Format", 70), ("status", "Status", 80)):
            self.result_table.heading(column, text=title)
            self.result_table.column(column, width=width, stretch=column in {"from", "subject"})
        self.result_table.grid(row=4, column=0, sticky="nsew")
        self.result_table.tag_configure("error", background=self.app.COLORS["error_soft"], foreground=self.app.COLORS["error"])
        actions = ttk.Frame(tab, style="Surface.TFrame")
        actions.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(actions, text="↻  Neuer Lauf", command=lambda: self.app._select_step(1)).pack(side="left")
        ttk.Button(actions, text="Log oeffnen", command=self._open_log).pack(side="right")
        ttk.Button(actions, text="Ausgabeordner oeffnen", style="Primary.TButton", command=self._open_output).pack(side="right", padx=6)

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
