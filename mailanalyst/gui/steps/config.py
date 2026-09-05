"""Config step: its widgets and user interactions."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
import os
from tkinter import filedialog


class ConfigStep:
    def __init__(self, app):
        self.app = app

    def _build_config_tab(self) -> None:
        tab = self.app.config_tab
        tab.columnconfigure(1, weight=1)
        ttk.Label(tab, text="Daten und Ausgabe festlegen", style="PageTitle.TLabel").grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(tab, text="Waehlen Sie die Mailquelle, den getrennten Zielordner und die gewuenschte Aufbereitung.",
                  style="Subtitle.TLabel").grid(row=1, column=0, columnspan=3, sticky="w", pady=(5, 24))
        self._path_row(tab, 2, "Eingabe", self.app.input_path, self._choose_input_file, self._choose_input_folder)
        self._path_row(tab, 3, "Zielordner", self.app.output_dir, self._choose_output)
        ttk.Separator(tab).grid(row=4, column=0, columnspan=3, sticky="ew", pady=18)
        ttk.Label(tab, text="Verarbeitungsoptionen", style="Surface.TLabel", font=(self.app.font_family, 11, "bold")).grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(0, 8))
        ttk.Label(tab, text="Ausgabeprofil", style="Surface.TLabel").grid(row=6, column=0, sticky="w", pady=8)
        ttk.Combobox(tab, textvariable=self.app.profile, state="readonly",
                     values=("Analysepaket", "Parquet", "CSV", "JSON", "Markdown", "Markdown-Monatsordner"), width=32).grid(row=6, column=1, sticky="w", pady=8)
        ttk.Label(tab, text="PST-Importer", style="Surface.TLabel").grid(row=7, column=0, sticky="w", pady=8)
        ttk.Combobox(tab, textvariable=self.app.pst_backend, state="readonly",
                     values=("Automatisch", "Ohne Outlook (libpff)", "Klassisches Outlook"), width=32).grid(row=7, column=1, sticky="w", pady=8)
        ttk.Label(tab, text="Markdown-Links", style="Surface.TLabel").grid(row=8, column=0, sticky="w", pady=8)
        ttk.Combobox(tab, textvariable=self.app.link_mode, state="readonly",
                     values=("Vollstaendige URLs", "Kompakte URLs", "Nur Linktext"), width=32).grid(row=8, column=1, sticky="w", pady=8)
        options = ttk.Frame(tab, style="Surface.TFrame")
        options.grid(row=9, column=1, sticky="w", pady=8)
        ttk.Checkbutton(options, text="Cache neu aufbauen", variable=self.app.refresh_cache).pack(side="left")
        ttk.Checkbutton(options, text="Strenge Hash-Pruefung", variable=self.app.hash_check).pack(side="left", padx=20)
        ttk.Label(tab, text="Systemcheck abgeschlossen · optionale Warnungen koennen je nach Datenquelle irrelevant sein.",
                  style="Subtitle.TLabel").grid(row=10, column=0, columnspan=3, sticky="w", pady=(22, 8))
        ttk.Button(tab, text="Vorpruefung starten  →", style="Primary.TButton", command=self.app.preflight_step._start_preflight).grid(
            row=11, column=2, sticky="e", pady=(24, 0))

    def _path_row(self, parent, row: int, label: str, variable: tk.StringVar, command, second_command=None) -> None:
        ttk.Label(parent, text=label, style="Surface.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 10), pady=8)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=8)
        buttons = ttk.Frame(parent, style="Surface.TFrame")
        buttons.grid(row=row, column=2, padx=(8, 0), pady=8)
        ttk.Button(buttons, text="Datei..." if second_command else "Ordner...", command=command).pack(side="left")
        if second_command:
            ttk.Button(buttons, text="Ordner...", command=second_command).pack(side="left", padx=(4, 0))

    def _choose_input_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Mailquellen", "*.eml *.msg *.pst"), ("Alle Dateien", "*.*")])
        if path:
            self.app.input_path.set(path)

    def _choose_input_folder(self) -> None:
        path = filedialog.askdirectory(title="Eingabeordner waehlen")
        if path:
            self.app.input_path.set(path)

    def _choose_output(self) -> None:
        path = filedialog.askdirectory(title="Separaten Zielordner waehlen")
        if path:
            self.app.output_dir.set(path)

    @staticmethod
    def _normalized_path(value: str) -> Path:
        cleaned = value.strip().strip('"').strip("'")
        cleaned = os.path.expandvars(os.path.expanduser(cleaned))
        return Path(cleaned).resolve(strict=False)
