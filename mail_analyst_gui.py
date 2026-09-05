from __future__ import annotations

import json
import os
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import pandas as pd

from mail_analyst import DEFAULT_CACHE, build_dataframe, configure_logging, write_markdown_dataset, write_output
from preflight import PreflightResult, run_preflight, write_preflight_report
from system_check import SystemCheckResult, run_system_check, write_system_check_report


def _resource_path(relative_path: str) -> Path:
    base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base_path / relative_path


def _load_private_fonts() -> None:
    """Make bundled fonts available to this process without installing them."""
    if sys.platform != "win32":
        return
    try:
        import ctypes
        for filename in ("Mulish-VariableFont_wght.ttf", "Mulish-Italic-VariableFont_wght.ttf"):
            font_path = _resource_path(f"assets/fonts/{filename}")
            if font_path.exists():
                ctypes.windll.gdi32.AddFontResourceExW(str(font_path), 0x10, 0)
    except Exception:
        pass


class MailAnalystApp(tk.Tk):
    COLORS = {
        "background": "#F5F4F2",
        "surface": "#FFFFFF",
        "sidebar": "#414343",
        "sidebar_hover": "#555858",
        "primary": "#D63C24",
        "primary_hover": "#B8321F",
        "accent_secondary": "#EF7D00",
        "accent_tertiary": "#0090B6",
        "accent_tertiary_hover": "#007894",
        "accent_soft": "#FBE9E6",
        "text": "#414343",
        "muted": "#707474",
        "border": "#D9DADA",
        "success": "#007E9F",
        "success_soft": "#E3F4F8",
        "warning": "#A85A00",
        "warning_soft": "#FFF0DF",
        "error": "#D63C24",
        "error_soft": "#FBE9E6",
    }

    def __init__(self) -> None:
        _load_private_fonts()
        super().__init__()
        self.title("MailAnalyst")
        self.geometry("1240x790")
        self.minsize(980, 640)
        self.configure(background=self.COLORS["background"])
        start_dir = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
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
        self._configure_style()
        self._build_ui()
        self.after(250, self._start_system_check)

    def _configure_style(self) -> None:
        family = self.font_family
        self.option_add("*Font", (family, 10))
        self.option_add("*TCombobox*Listbox.font", (family, 10))
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(family=family, size=10)
        text_font = tkfont.nametofont("TkTextFont")
        text_font.configure(family=family, size=10)

        style = ttk.Style(self)
        style.theme_use("clam")
        c = self.COLORS
        style.configure("TFrame", background=c["background"])
        style.configure("Surface.TFrame", background=c["surface"])
        style.configure("Sidebar.TFrame", background=c["sidebar"])
        style.configure("Header.TFrame", background=c["surface"])
        style.configure("TLabel", background=c["background"], foreground=c["text"])
        style.configure("Surface.TLabel", background=c["surface"], foreground=c["text"])
        style.configure("Title.TLabel", background=c["surface"], foreground=c["text"], font=(family, 20, "bold"))
        style.configure("PageTitle.TLabel", background=c["surface"], foreground=c["text"], font=(family, 17, "bold"))
        style.configure("Subtitle.TLabel", background=c["surface"], foreground=c["muted"], font=(family, 10))
        style.configure("SidebarTitle.TLabel", background=c["sidebar"], foreground="#D5DADA", font=(family, 9, "bold"))
        style.configure("Offline.TLabel", background=c["success_soft"], foreground=c["success"], font=(family, 9, "bold"), padding=(10, 5))

        style.configure("TButton", font=(family, 10, "bold"), padding=(14, 8), borderwidth=1,
                        background=c["surface"], foreground=c["text"], bordercolor=c["border"])
        style.map("TButton", background=[("active", "#EAF0F3")], bordercolor=[("active", "#B9C8D0")])
        style.configure("Primary.TButton", background=c["primary"], foreground="#FFFFFF", bordercolor=c["primary"], padding=(18, 10))
        style.map("Primary.TButton", background=[("active", c["primary_hover"]), ("disabled", "#A9BCC5")],
                  foreground=[("disabled", "#EEF2F4")])
        style.configure("Nav.TButton", background=c["sidebar"], foreground="#C6D5DE", borderwidth=0,
                        anchor="w", padding=(18, 13), font=(family, 10, "bold"))
        style.map("Nav.TButton", background=[("active", c["sidebar_hover"]), ("disabled", c["sidebar"])],
                  foreground=[("disabled", "#688496")])
        style.configure("ActiveNav.TButton", background=c["accent_tertiary"], foreground="#FFFFFF", borderwidth=0,
                        anchor="w", padding=(18, 13), font=(family, 10, "bold"))
        style.map("ActiveNav.TButton", background=[("active", c["accent_tertiary_hover"])])

        style.configure("TLabelframe", background=c["surface"], bordercolor=c["border"], relief="solid", borderwidth=1)
        style.configure("TLabelframe.Label", background=c["surface"], foreground=c["text"], font=(family, 10, "bold"))
        style.configure("TEntry", fieldbackground="#FBFCFD", foreground=c["text"], bordercolor=c["border"], padding=7)
        style.configure("TCombobox", fieldbackground="#FBFCFD", foreground=c["text"], bordercolor=c["border"], padding=6)
        style.map("TCombobox", fieldbackground=[("readonly", "#FBFCFD")], selectbackground=[("readonly", "#FBFCFD")],
                  selectforeground=[("readonly", c["text"])])
        style.configure("TCheckbutton", background=c["surface"], foreground=c["text"])
        style.map("TCheckbutton", background=[("active", c["surface"])])
        style.configure("Horizontal.TProgressbar", background=c["accent_tertiary"], troughcolor="#E3E6E6", borderwidth=0, thickness=9)
        style.configure("Treeview", background=c["surface"], fieldbackground=c["surface"], foreground=c["text"],
                        rowheight=30, bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"])
        style.configure("Treeview.Heading", background="#ECEEEE", foreground=c["text"], font=(family, 9, "bold"),
                        padding=(8, 8), relief="flat")
        style.map("Treeview", background=[("selected", c["accent_tertiary"])], foreground=[("selected", "#FFFFFF")])
        style.layout("Content.TNotebook.Tab", [])
        style.configure("Content.TNotebook", background=c["background"], borderwidth=0)
        style.configure("Content.TNotebook.Client", background=c["surface"], borderwidth=0)

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
        self._build_system_tab()
        self._build_config_tab()
        self._build_preflight_tab()
        self._build_processing_tab()
        self._build_result_tab()
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

    def _path_row(self, parent, row: int, label: str, variable: tk.StringVar, command, second_command=None) -> None:
        ttk.Label(parent, text=label, style="Surface.TLabel").grid(row=row, column=0, sticky="w", padx=(0, 10), pady=8)
        ttk.Entry(parent, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=8)
        buttons = ttk.Frame(parent, style="Surface.TFrame")
        buttons.grid(row=row, column=2, padx=(8, 0), pady=8)
        ttk.Button(buttons, text="Datei..." if second_command else "Ordner...", command=command).pack(side="left")
        if second_command:
            ttk.Button(buttons, text="Ordner...", command=second_command).pack(side="left", padx=(4, 0))

    def _build_system_tab(self) -> None:
        tab = self.system_tab
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
        self.system_table.tag_configure("ok", background=self.COLORS["success_soft"], foreground=self.COLORS["success"])
        self.system_table.tag_configure("warning", background=self.COLORS["warning_soft"], foreground=self.COLORS["warning"])
        self.system_table.tag_configure("error", background=self.COLORS["error_soft"], foreground=self.COLORS["error"])
        actions = ttk.Frame(tab, style="Surface.TFrame")
        actions.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        self.system_retry_button = ttk.Button(actions, text="Erneut pruefen", command=self._start_system_check)
        self.system_retry_button.pack(side="left")
        self.system_continue_button = ttk.Button(actions, text="Weiter zu den Daten  →", style="Primary.TButton",
                                                 command=lambda: self._select_step(1), state="disabled")
        self.system_continue_button.pack(side="right")

    def _start_system_check(self) -> None:
        self.unlocked_steps = {0}
        self.current_step = 0
        self.notebook.select(self.system_tab)
        self._refresh_navigation()
        self.system_check_results = []
        self.system_progress["value"] = 0
        self.system_status.set("Systemcheck laeuft ...")
        self.system_retry_button.configure(state="disabled")
        self.system_continue_button.configure(state="disabled")
        for item in self.system_table.get_children():
            self.system_table.delete(item)
        threading.Thread(target=self._run_system_check, daemon=True).start()

    def _run_system_check(self) -> None:
        try:
            results = run_system_check(
                lambda done, total, label: self.after(0, self._system_check_progress, done, total, label),
                detected_font_family=self.font_family,
            )
            self.after(0, self._finish_system_check, results)
        except Exception as exc:
            self.after(0, self._finish_system_check_error, str(exc))

    def _system_check_progress(self, done: int, total: int, label: str) -> None:
        self.system_progress["maximum"] = max(total, 1)
        self.system_progress["value"] = done
        self.system_status.set(f"Pruefe {label} ({done} von {total})")

    def _finish_system_check(self, results: list[SystemCheckResult]) -> None:
        self.system_check_results = results
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
            self._unlock_step(1)
            self.system_continue_button.configure(state="normal")

    def _finish_system_check_error(self, error: str) -> None:
        self.system_status.set(f"Systemcheck fehlgeschlagen: {error}")
        self.system_retry_button.configure(state="normal")
        self.system_continue_button.configure(state="disabled")

    def _build_config_tab(self) -> None:
        tab = self.config_tab
        tab.columnconfigure(1, weight=1)
        ttk.Label(tab, text="Daten und Ausgabe festlegen", style="PageTitle.TLabel").grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(tab, text="Waehlen Sie die Mailquelle, den getrennten Zielordner und die gewuenschte Aufbereitung.",
                  style="Subtitle.TLabel").grid(row=1, column=0, columnspan=3, sticky="w", pady=(5, 24))
        self._path_row(tab, 2, "Eingabe", self.input_path, self._choose_input_file, self._choose_input_folder)
        self._path_row(tab, 3, "Zielordner", self.output_dir, self._choose_output)
        ttk.Separator(tab).grid(row=4, column=0, columnspan=3, sticky="ew", pady=18)
        ttk.Label(tab, text="Verarbeitungsoptionen", style="Surface.TLabel", font=(self.font_family, 11, "bold")).grid(
            row=5, column=0, columnspan=3, sticky="w", pady=(0, 8))
        ttk.Label(tab, text="Ausgabeprofil", style="Surface.TLabel").grid(row=6, column=0, sticky="w", pady=8)
        ttk.Combobox(tab, textvariable=self.profile, state="readonly",
                     values=("Analysepaket", "Parquet", "CSV", "JSON", "Markdown", "Markdown-Monatsordner"), width=32).grid(row=6, column=1, sticky="w", pady=8)
        ttk.Label(tab, text="PST-Importer", style="Surface.TLabel").grid(row=7, column=0, sticky="w", pady=8)
        ttk.Combobox(tab, textvariable=self.pst_backend, state="readonly",
                     values=("Automatisch", "Ohne Outlook (libpff)", "Klassisches Outlook"), width=32).grid(row=7, column=1, sticky="w", pady=8)
        ttk.Label(tab, text="Markdown-Links", style="Surface.TLabel").grid(row=8, column=0, sticky="w", pady=8)
        ttk.Combobox(tab, textvariable=self.link_mode, state="readonly",
                     values=("Vollstaendige URLs", "Kompakte URLs", "Nur Linktext"), width=32).grid(row=8, column=1, sticky="w", pady=8)
        options = ttk.Frame(tab, style="Surface.TFrame")
        options.grid(row=9, column=1, sticky="w", pady=8)
        ttk.Checkbutton(options, text="Cache neu aufbauen", variable=self.refresh_cache).pack(side="left")
        ttk.Checkbutton(options, text="Strenge Hash-Pruefung", variable=self.hash_check).pack(side="left", padx=20)
        ttk.Label(tab, text="Systemcheck abgeschlossen · optionale Warnungen koennen je nach Datenquelle irrelevant sein.",
                  style="Subtitle.TLabel").grid(row=10, column=0, columnspan=3, sticky="w", pady=(22, 8))
        ttk.Button(tab, text="Vorpruefung starten  →", style="Primary.TButton", command=self._start_preflight).grid(
            row=11, column=2, sticky="e", pady=(24, 0))

    def _build_preflight_tab(self) -> None:
        tab = self.preflight_tab
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
        self.preflight_table.tag_configure("ok", background=self.COLORS["success_soft"], foreground=self.COLORS["success"])
        self.preflight_table.tag_configure("warning", background=self.COLORS["warning_soft"], foreground=self.COLORS["warning"])
        self.preflight_table.tag_configure("error", background=self.COLORS["error_soft"], foreground=self.COLORS["error"])
        self.preflight_table.tag_configure("ignored", foreground=self.COLORS["muted"])
        self.preflight_table.bind("<Double-1>", self._toggle_preflight_item)
        actions = ttk.Frame(tab, style="Surface.TFrame")
        actions.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(actions, text="←  Zurueck", command=lambda: self._select_step(1)).pack(side="left")
        ttk.Button(actions, text="Warnungen einschliessen", command=lambda: self._set_status_included("warning", True)).pack(side="left", padx=6)
        ttk.Button(actions, text="Warnungen ausschliessen", command=lambda: self._set_status_included("warning", False)).pack(side="left")
        self.process_button = ttk.Button(actions, text="Verarbeitung starten  →", style="Primary.TButton",
                                         command=self._start_processing, state="disabled")
        self.process_button.pack(side="right")

    def _build_processing_tab(self) -> None:
        tab = self.processing_tab
        tab.columnconfigure(0, weight=1)
        ttk.Label(tab, text="E-Mails werden verarbeitet", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(tab, text="Die Verarbeitung laeuft vollstaendig lokal. Dieses Fenster kann geoeffnet bleiben.",
                  style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(5, 28))
        self.processing_status = tk.StringVar(value="Wartet")
        ttk.Label(tab, textvariable=self.processing_status, style="Surface.TLabel",
                  font=(self.font_family, 11, "bold")).grid(row=2, column=0, sticky="w", pady=(22, 8))
        self.processing_progress = ttk.Progressbar(tab, mode="determinate")
        self.processing_progress.grid(row=3, column=0, sticky="ew")
        self.processing_detail = tk.StringVar(value="")
        ttk.Label(tab, textvariable=self.processing_detail, style="Subtitle.TLabel", wraplength=900).grid(row=4, column=0, sticky="w", pady=10)

    def _build_result_tab(self) -> None:
        tab = self.result_tab
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(4, weight=1)
        ttk.Label(tab, text="Verarbeitung abgeschlossen", style="PageTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(tab, text="Die Ausgabedaten und das Protokoll liegen jetzt im gewaehlten Zielordner.",
                  style="Subtitle.TLabel").grid(row=1, column=0, sticky="w", pady=(5, 14))
        self.result_status = tk.StringVar(value="")
        ttk.Label(tab, textvariable=self.result_status, style="Surface.TLabel",
                  font=(self.font_family, 11, "bold")).grid(row=2, column=0, sticky="w", pady=(0, 12))
        path_frame = ttk.Frame(tab, style="Surface.TFrame")
        path_frame.grid(row=3, column=0, sticky="ew", pady=(0, 14))
        path_frame.columnconfigure(1, weight=1)
        ttk.Label(path_frame, text="Zielordner", style="Surface.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Entry(path_frame, textvariable=self.result_output_path, state="readonly").grid(row=0, column=1, sticky="ew")
        ttk.Button(path_frame, text="Pfad kopieren", command=self._copy_output_path).grid(row=0, column=2, padx=(8, 0))
        columns = ("date", "from", "subject", "format", "status")
        self.result_table = ttk.Treeview(tab, columns=columns, show="headings")
        for column, title, width in (("date", "Datum", 145), ("from", "Absender", 220), ("subject", "Betreff", 480),
                                     ("format", "Format", 70), ("status", "Status", 80)):
            self.result_table.heading(column, text=title)
            self.result_table.column(column, width=width, stretch=column in {"from", "subject"})
        self.result_table.grid(row=4, column=0, sticky="nsew")
        self.result_table.tag_configure("error", background=self.COLORS["error_soft"], foreground=self.COLORS["error"])
        actions = ttk.Frame(tab, style="Surface.TFrame")
        actions.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(actions, text="↻  Neuer Lauf", command=lambda: self._select_step(1)).pack(side="left")
        ttk.Button(actions, text="Log oeffnen", command=self._open_log).pack(side="right")
        ttk.Button(actions, text="Ausgabeordner oeffnen", style="Primary.TButton", command=self._open_output).pack(side="right", padx=6)

    def _choose_input_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Mailquellen", "*.eml *.msg *.pst"), ("Alle Dateien", "*.*")])
        if path:
            self.input_path.set(path)

    def _choose_input_folder(self) -> None:
        path = filedialog.askdirectory(title="Eingabeordner waehlen")
        if path:
            self.input_path.set(path)

    def _choose_output(self) -> None:
        path = filedialog.askdirectory(title="Separaten Zielordner waehlen")
        if path:
            self.output_dir.set(path)

    @staticmethod
    def _normalized_path(value: str) -> Path:
        cleaned = value.strip().strip('"').strip("'")
        cleaned = os.path.expandvars(os.path.expanduser(cleaned))
        return Path(cleaned).resolve(strict=False)

    def _start_preflight(self) -> None:
        if not self.input_path.get().strip().strip('"').strip("'"):
            messagebox.showerror("MailAnalyst", "Bitte zuerst eine Eingabedatei oder einen Eingabeordner auswaehlen.")
            return
        source = self._normalized_path(self.input_path.get())
        target = self._normalized_path(self.output_dir.get())
        self.input_path.set(str(source))
        self.output_dir.set(str(target))
        if not source.exists():
            messagebox.showerror("MailAnalyst", f"Der Eingabepfad existiert nicht oder ist nicht erreichbar:\n\n{source}")
            return
        try:
            target.mkdir(parents=True, exist_ok=True)
            write_system_check_report(self.system_check_results, target)
        except Exception as exc:
            messagebox.showerror("MailAnalyst", f"Zielordner nicht verwendbar: {exc}")
            return
        self._unlock_step(2, select=True)
        self.process_button.configure(state="disabled")
        self.preflight_results = []
        self.preflight_progress["value"] = 0
        for item in self.preflight_table.get_children():
            self.preflight_table.delete(item)
        threading.Thread(target=self._run_preflight, args=(source, target), daemon=True).start()

    def _run_preflight(self, source: Path, target: Path) -> None:
        try:
            results = run_preflight(source, lambda done, total, path: self.after(0, self._preflight_progress, done, total, path))
            write_preflight_report(results, target)
            self.after(0, self._finish_preflight, results)
        except Exception as exc:
            self.after(0, messagebox.showerror, "Vorpruefung", str(exc))

    def _preflight_progress(self, done: int, total: int, path: Path) -> None:
        self.preflight_progress["maximum"] = max(total, 1)
        self.preflight_progress["value"] = done
        self.preflight_status.set(f"Pruefe {done} von {total}: {path.name}")

    def _finish_preflight(self, results: list[PreflightResult]) -> None:
        self.preflight_results = results
        for index, result in enumerate(results):
            self.preflight_table.insert("", "end", iid=str(index), values=("Ja" if result.include else "Nein", result.status.upper(),
                result.extension, f"{result.size / 1048576:.2f}", result.path, result.reason), tags=(result.status,))
        counts = {status: sum(result.status == status for result in results) for status in ("ok", "warning", "error", "ignored")}
        self.preflight_status.set(f"Fertig: {len(results)} | OK {counts['ok']} | Warnungen {counts['warning']} | Fehler {counts['error']} | Ignoriert {counts['ignored']}")
        self.process_button.configure(state="normal" if any(result.include for result in results) else "disabled")

    def _toggle_preflight_item(self, _event=None) -> None:
        selected = self.preflight_table.selection()
        if not selected:
            return
        index = int(selected[0])
        result = self.preflight_results[index]
        if result.status in {"error", "ignored"} and not result.include:
            if not messagebox.askyesno("Problematische Quelle", "Diese Quelle trotzdem einplanen?"):
                return
        result.include = not result.include
        self.preflight_table.set(selected[0], "include", "Ja" if result.include else "Nein")
        self.process_button.configure(state="normal" if any(item.include for item in self.preflight_results) else "disabled")

    def _set_status_included(self, status: str, included: bool) -> None:
        for index, result in enumerate(self.preflight_results):
            if result.status == status:
                result.include = included
                self.preflight_table.set(str(index), "include", "Ja" if included else "Nein")
        self.process_button.configure(state="normal" if any(item.include for item in self.preflight_results) else "disabled")

    def _start_processing(self) -> None:
        selected = [Path(result.path) for result in self.preflight_results if result.include]
        if not selected:
            return
        write_preflight_report(self.preflight_results, Path(self.output_dir.get()))
        self._unlock_step(3, select=True)
        self.processing_progress["maximum"] = len(selected)
        self.processing_progress["value"] = 0
        self.processing_status.set(f"0 von {len(selected)} Quellen verarbeitet")
        threading.Thread(target=self._run_processing, args=(selected,), daemon=True).start()

    def _run_processing(self, paths: list[Path]) -> None:
        target = Path(self.output_dir.get())
        try:
            configure_logging(target / "parse_log.txt")
            with (target / "processing_options.json").open("w", encoding="utf-8") as file:
                json.dump({"input": self.input_path.get(), "output": str(target.resolve()),
                           "output_profile": self.profile.get(),
                           "pst_backend": self.pst_backend.get(), "markdown_links": self.link_mode.get(),
                           "selected_sources": len(paths)}, file, ensure_ascii=False, indent=2)
            frame = build_dataframe(Path(self.input_path.get()), DEFAULT_CACHE, refresh=self.refresh_cache.get(),
                hash_check=self.hash_check.get(), workers=max(1, min(4, os.cpu_count() or 1)),
                pst_backend={"Automatisch": "auto", "Ohne Outlook (libpff)": "libpff", "Klassisches Outlook": "outlook"}[self.pst_backend.get()],
                paths_override=paths, progress_callback=lambda done, total, path, mode: self.after(0, self._processing_update, done, total, path, mode))
            self._write_profile(frame, target)
            self.after(0, self._finish_processing, frame, None)
        except Exception as exc:
            self.after(0, self._finish_processing, pd.DataFrame(), str(exc))

    def _processing_update(self, done: int, total: int, path: Path, mode: str) -> None:
        self.processing_progress["value"] = done
        self.processing_status.set(f"{done} von {total} Quellen verarbeitet")
        self.processing_detail.set(f"{path.name} ({'Cache' if mode == 'cache' else 'neu geparst'})")

    def _write_profile(self, frame: pd.DataFrame, target: Path) -> None:
        profile = self.profile.get()
        link_mode = {"Vollstaendige URLs": "full", "Kompakte URLs": "compact", "Nur Linktext": "text_only"}[self.link_mode.get()]
        if profile == "Analysepaket":
            write_output(frame, target / "emails.parquet")
            write_output(frame, target / "emails.json")
            write_markdown_dataset(frame, target / "mail_workspace", link_mode)
        elif profile == "Markdown-Monatsordner":
            write_markdown_dataset(frame, target / "mail_workspace", link_mode)
        else:
            suffix = {"Parquet": ".parquet", "CSV": ".csv", "JSON": ".json", "Markdown": ".md"}[profile]
            write_output(frame, target / f"emails{suffix}", link_mode)

    def _finish_processing(self, frame: pd.DataFrame, error: str | None) -> None:
        if error:
            messagebox.showerror("Verarbeitung", error)
            self.processing_status.set("Verarbeitung fehlgeschlagen")
            return
        for item in self.result_table.get_children():
            self.result_table.delete(item)
        for _, row in frame.iterrows():
            status = str(row.get("parse_status", ""))
            self.result_table.insert("", "end", values=(row.get("sent_datetime_de", ""), row.get("from_email", ""),
                row.get("subject", ""), row.get("file_ext", ""), status), tags=(("error",) if status == "error" else ()))
        errors = int((frame.get("parse_status", pd.Series(dtype=str)) == "error").sum())
        planned = sum(result.include for result in self.preflight_results)
        self.result_status.set(f"{planned} Quellen verarbeitet | {len(frame)} Nachrichten | {errors} Parserfehler")
        self.result_output_path.set(str(Path(self.output_dir.get()).resolve()))
        self._unlock_step(4, select=True)

    def _copy_output_path(self) -> None:
        path = self.result_output_path.get()
        if not path:
            return
        self.clipboard_clear()
        self.clipboard_append(path)
        self.update_idletasks()

    def _open_output(self) -> None:
        path = Path(self.output_dir.get())
        if path.exists():
            os.startfile(path)

    def _open_log(self) -> None:
        path = Path(self.output_dir.get()) / "parse_log.txt"
        if path.exists():
            os.startfile(path)


def _enable_windows_dpi_awareness() -> None:
    if sys.platform != "win32":
        return
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


if __name__ == "__main__":
    _enable_windows_dpi_awareness()
    MailAnalystApp().mainloop()
