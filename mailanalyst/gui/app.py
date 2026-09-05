"""Application shell and navigation; pages own their widgets."""

from __future__ import annotations

import sys
from pathlib import Path
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from mailanalyst.checks.preflight import PreflightResult
from mailanalyst.checks.system import SystemCheckResult
from mailanalyst.gui.resources import _load_private_fonts
from mailanalyst.gui.theme import COLORS, configure_style
from mailanalyst.gui.jobs import BackgroundJobs
from mailanalyst.gui.steps.system import SystemStep
from mailanalyst.gui.steps.config import ConfigStep
from mailanalyst.gui.steps.preflight import PreflightStep
from mailanalyst.gui.steps.processing import ProcessingStep
from mailanalyst.gui.steps.result import ResultStep


class MailAnalystApp(tk.Tk):
    COLORS = COLORS

    def __init__(self) -> None:
        _load_private_fonts()
        super().__init__()
        self.title("MailAnalyst")
        self.geometry("1240x790")
        self.minsize(980, 640)
        self.configure(background=self.COLORS["background"])
        start_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[2]
        self.input_path = tk.StringVar(value="" if getattr(sys, "frozen", False) else str(start_dir / "input_emails"))
        self.output_dir = tk.StringVar(value=str(start_dir / "out"))
        self.profile = tk.StringVar(value="Analysepaket")
        self.pst_backend = tk.StringVar(value="Automatisch")
        self.link_mode = tk.StringVar(value="Kompakte URLs")
        self.refresh_cache = tk.BooleanVar(value=False)
        self.hash_check = tk.BooleanVar(value=False)
        self.result_output_path = tk.StringVar(value="")
        self.system_check_results: list[SystemCheckResult] = []
        self.preflight_results: list[PreflightResult] = []
        self.current_step = 0
        self.unlocked_steps = {0}
        self.font_family = "Mulish" if "Mulish" in tkfont.families(self) else "Segoe UI"
        configure_style(self)
        self.jobs = BackgroundJobs(self)
        self.system_step = SystemStep(self)
        self.config_step = ConfigStep(self)
        self.preflight_step = PreflightStep(self)
        self.processing_step = ProcessingStep(self)
        self.result_step = ResultStep(self)
        self._build_ui()
        self.after(250, self.system_step._start_system_check)

    def _build_ui(self) -> None:
        header = ttk.Frame(self, style="Header.TFrame", padding=(26, 16))
        header.pack(fill="x")
        tk.Frame(header, width=5, height=30, background=self.COLORS["primary"]).pack(side="left", padx=(0, 12))
        ttk.Label(header, text="MailAnalyst", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="Lokale Aufbereitung von Projektpostfaechern", style="Subtitle.TLabel").pack(side="left", padx=(16, 0), pady=(6, 0))
        ttk.Label(header, text="●  LOKAL · OFFLINE", style="Offline.TLabel").pack(side="right")
        brand_line = tk.Frame(self, height=4, background=self.COLORS["surface"])
        brand_line.pack(fill="x")
        brand_line.grid_columnconfigure((0, 1, 2), weight=1)
        tk.Frame(brand_line, background=self.COLORS["primary"], height=4).grid(row=0, column=0, sticky="ew")
        tk.Frame(brand_line, background=self.COLORS["accent_secondary"], height=4).grid(row=0, column=1, sticky="ew")
        tk.Frame(brand_line, background=self.COLORS["accent_tertiary"], height=4).grid(row=0, column=2, sticky="ew")

        shell = ttk.Frame(self, padding=(18, 18, 18, 18))
        shell.pack(fill="both", expand=True)
        sidebar = ttk.Frame(shell, style="Sidebar.TFrame", width=230, padding=(12, 22))
        sidebar.pack(side="left", fill="y", padx=(0, 16))
        sidebar.pack_propagate(False)
        ttk.Label(sidebar, text="WORKFLOW", style="SidebarTitle.TLabel").pack(fill="x", padx=10, pady=(0, 10))
        nav_items = ("1   Systemcheck", "2   Daten festlegen", "3   Vorpruefung", "4   Verarbeitung", "5   Ergebnis")
        self.nav_buttons: list[ttk.Button] = []
        for index, label in enumerate(nav_items):
            button = ttk.Button(sidebar, text=label, style="Nav.TButton", command=lambda step=index: self._select_step(step))
            button.pack(fill="x", pady=2)
            self.nav_buttons.append(button)
        ttk.Label(sidebar, text="Ihre Daten verlassen diese\nUmgebung nicht.", style="SidebarTitle.TLabel", justify="left").pack(side="bottom", fill="x", padx=10)

        self.notebook = ttk.Notebook(shell, style="Content.TNotebook")
        self.notebook.pack(side="left", fill="both", expand=True)
        self.system_tab = ttk.Frame(self.notebook, style="Surface.TFrame", padding=28)
        self.config_tab = ttk.Frame(self.notebook, style="Surface.TFrame", padding=28)
        self.preflight_tab = ttk.Frame(self.notebook, style="Surface.TFrame", padding=28)
        self.processing_tab = ttk.Frame(self.notebook, style="Surface.TFrame", padding=28)
        self.result_tab = ttk.Frame(self.notebook, style="Surface.TFrame", padding=28)
        for title, tab in (("1  Systemcheck", self.system_tab), ("2  Konfiguration", self.config_tab),
                           ("3  Vorpruefung", self.preflight_tab), ("4  Verarbeitung", self.processing_tab),
                           ("5  Ergebnis", self.result_tab)):
            self.notebook.add(tab, text=title)
        self.system_step._build_system_tab()
        self.config_step._build_config_tab()
        self.preflight_step._build_preflight_tab()
        self.processing_step._build_processing_tab()
        self.result_step._build_result_tab()
        self._refresh_navigation()

    def _refresh_navigation(self) -> None:
        for index, button in enumerate(self.nav_buttons):
            if index == self.current_step:
                button.configure(style="ActiveNav.TButton", state="normal")
            else:
                button.configure(style="Nav.TButton", state="normal" if index in self.unlocked_steps else "disabled")

    def _select_step(self, step: int) -> None:
        if step not in self.unlocked_steps:
            return
        self.current_step = step
        self.notebook.select(step)
        self._refresh_navigation()

    def _unlock_step(self, step: int, select: bool = False) -> None:
        self.unlocked_steps.add(step)
        if select:
            self._select_step(step)
        else:
            self._refresh_navigation()
