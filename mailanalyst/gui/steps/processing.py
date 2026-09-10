"""Processing step: its widgets and user interactions."""

from __future__ import annotations
from dataclasses import replace

import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path
import pandas as pd
from mailanalyst.checks.preflight import write_preflight_report
from mailanalyst.services import ProcessingOptions, process_sources
from mailanalyst.progress import PhaseProgress
from mailanalyst.gui.processing_display import ProcessingDisplay


class ProcessingStep:
    def __init__(self, app):
        self.app = app

    def _build_processing_tab(self) -> None:
        tab = self.app.processing_tab
        tab.columnconfigure(0, weight=1)
        ttk.Label(tab, text="E-Mails werden verarbeitet", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(tab, text="Die Verarbeitung läuft vollständig lokal. Das Fenster kann geöffnet bleiben.",
                  style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(5, 28))
        self.processing_status = tk.StringVar(value="Wartet")
        ttk.Label(tab, textvariable=self.processing_status, style="Surface.TLabel",
                  font=(self.app.font_family, 11, "bold")).grid(row=2, column=0, sticky="w", pady=(22, 8))
        self.processing_progress = ttk.Progressbar(tab, mode="determinate")
        self.processing_progress.grid(row=3, column=0, sticky="ew")
        self.processing_detail = tk.StringVar(value="")
        ttk.Label(tab, textvariable=self.processing_detail, style="Subtitle.TLabel", wraplength=620).grid(row=4, column=0, sticky="w", pady=10)

        self.display = ProcessingDisplay(self, tab)

    def _start_processing(self) -> None:
        if self.app.jobs.busy or self.app.jobs.closing:
            return
        selected = [Path(result.path) for result in self.app.preflight_results if result.include]
        if not selected:
            return
        # Reports are written by the worker to keep large selections off the Tk thread.
        self.app.unlocked_steps.discard(4)
        self.app.result_output_path.set("")
        self.app._unlock_step(3, select=True)
        self.display.start(len(selected))
        options = ProcessingOptions(
            source=Path(self.app.input_path.get()), target=Path(self.app.output_dir.get()),
            paths=tuple(selected), profile=self.app.profile.get(), backend=self.app.pst_backend.get(),
            links=self.app.link_mode.get(), refresh=self.app.refresh_cache.get(), hash_check=self.app.hash_check.get(),
            preflight=tuple(replace(row) for row in self.app.preflight_results),
        )
        selection = list(self.app.preflight_results)

        def work(progress):
            progress.cancel_token.check()
            write_preflight_report(selection, options.target)
            return process_sources(options, progress, cancel=progress.cancel_token, phase_progress=progress)

        self.app.jobs.submit(
            work,
            lambda frame: self._finish_processing(frame, None, options),
            lambda error: self._finish_processing(pd.DataFrame(), error, options), self._processing_update,
            on_cancel=self._cancelled,
        )

    def _cancelled(self, details):
        self.display.stop()
        self.processing_status.set("Verarbeitung abgebrochen")
        self.app.activity_status.set("Verarbeitung abgebrochen")
        self.processing_detail.set(details)
        self.app._select_step(2)

    def _processing_update(self, *args) -> None:
        if len(args) == 1 and isinstance(args[0], PhaseProgress):
            self.display.update(args[0])
        else:
            done, total, path, mode = args
            self.display.sources.set(f"{done} von {total} Quellen verarbeitet")

    def _finish_processing(self, frame: pd.DataFrame, error: str | None, options: ProcessingOptions) -> None:
        self.display.stop()
        if error:
            messagebox.showerror("Verarbeitung", error, parent=self.app)
            self.processing_status.set("Verarbeitung fehlgeschlagen")
            return
        self.processing_status.set("Verarbeitung abgeschlossen")
        self.processing_progress.configure(mode="determinate", maximum=100, value=100)
        self.app.result_step.show_results(frame, len(options.paths), Path(frame.attrs["run_directory"]))
        self.app._unlock_step(4, select=True)
