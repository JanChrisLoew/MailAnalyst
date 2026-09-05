"""Processing step: its widgets and user interactions."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
import pandas as pd
from mailanalyst.checks.preflight import write_preflight_report
from mailanalyst.services import ProcessingOptions, process_sources


class ProcessingStep:
    def __init__(self, app):
        self.app = app

    def _build_processing_tab(self) -> None:
        tab = self.app.processing_tab
        tab.columnconfigure(0, weight=1)
        ttk.Label(tab, text="E-Mails werden verarbeitet", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(tab, text="Die Verarbeitung laeuft vollstaendig lokal. Dieses Fenster kann geoeffnet bleiben.",
                  style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(5, 28))
        self.processing_status = tk.StringVar(value="Wartet")
        ttk.Label(tab, textvariable=self.processing_status, style="Surface.TLabel",
                  font=(self.app.font_family, 11, "bold")).grid(row=2, column=0, sticky="w", pady=(22, 8))
        self.processing_progress = ttk.Progressbar(tab, mode="determinate")
        self.processing_progress.grid(row=3, column=0, sticky="ew")
        self.processing_detail = tk.StringVar(value="")
        ttk.Label(tab, textvariable=self.processing_detail, style="Subtitle.TLabel", wraplength=900).grid(row=4, column=0, sticky="w", pady=10)

    def _start_processing(self) -> None:
        selected = [Path(result.path) for result in self.app.preflight_results if result.include]
        if not selected:
            return
        write_preflight_report(self.app.preflight_results, Path(self.app.output_dir.get()))
        self.app._unlock_step(3, select=True)
        self.processing_progress["maximum"] = len(selected)
        self.processing_progress["value"] = 0
        self.processing_status.set(f"0 von {len(selected)} Quellen verarbeitet")
        options = ProcessingOptions(
            source=Path(self.app.input_path.get()), target=Path(self.app.output_dir.get()),
            paths=tuple(selected), profile=self.app.profile.get(), backend=self.app.pst_backend.get(),
            links=self.app.link_mode.get(), refresh=self.app.refresh_cache.get(), hash_check=self.app.hash_check.get(),
        )
        self.app.jobs.submit(
            lambda progress: process_sources(options, progress),
            lambda frame: self._finish_processing(frame, None, options),
            lambda error: self._finish_processing(pd.DataFrame(), error, options), self._processing_update,
        )

    def _processing_update(self, done: int, total: int, path: Path, mode: str) -> None:
        self.processing_progress["value"] = done
        self.processing_status.set(f"{done} von {total} Quellen verarbeitet")
        self.processing_detail.set(f"{path.name} ({'Cache' if mode == 'cache' else 'neu geparst'})")

    def _finish_processing(self, frame: pd.DataFrame, error: str | None, options: ProcessingOptions) -> None:
        if error:
            messagebox.showerror("Verarbeitung", error)
            self.processing_status.set("Verarbeitung fehlgeschlagen")
            return
        self.app.result_step.show_results(frame, len(options.paths), options.target)
        self.app._unlock_step(4, select=True)
