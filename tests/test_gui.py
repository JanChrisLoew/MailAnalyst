"""Exercise the real Tk event loop with synthetic sources and isolated output."""

import gc
import json
import tempfile
import threading
import time
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

from mailanalyst.config import LOGGER
from mailanalyst.gui.app import MailAnalystApp
from mailanalyst.gui.resources import _resource_path
from tests.samples import create_sources


class GuiTests(unittest.TestCase):
    def setUp(self):
        # Destroyed Tk interpreter cycles must be collected on the GUI thread.
        gc.collect()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        try:
            self.app = MailAnalystApp()
        except tk.TclError as exc:
            if "display" in str(exc).lower():
                self.skipTest(f"No graphical display: {exc}")
            raise
        self.app.withdraw()
        self.addCleanup(self.close_app)
        self.errors = []
        self.app.report_callback_exception = lambda *args: self.errors.append(str(args))
        self.error_patch = patch("tkinter.messagebox.showerror", side_effect=lambda *args: self.errors.append(str(args)))
        self.error_patch.start()
        self.addCleanup(self.error_patch.stop)

    def close_app(self):
        app = self.app
        for event in app.tk.call("after", "info"):
            app.after_cancel(event)
        app.destroy()
        self.app = None
        del app
        # Tk variables must be finalized by the thread that owned the interpreter.
        gc.collect()
        for handler in LOGGER.handlers[:]:
            handler.close()
            LOGGER.removeHandler(handler)

    def wait_for(self, predicate):
        deadline = time.monotonic() + 20
        while not predicate() and not self.errors and time.monotonic() < deadline:
            self.app.update()
            time.sleep(0.01)
        self.assertEqual(self.errors, [])
        self.assertTrue(predicate(), "GUI workflow timed out")

    def test_system_preflight_processing_and_result(self):
        app = self.app
        self.assertEqual(len(app.notebook.tabs()), 5)
        self.assertTrue(_resource_path("assets/fonts/OFL.txt").is_file())
        self.wait_for(lambda: bool(app.system_check_results))
        self.assertIn(1, app.unlocked_steps)
        source = create_sources(self.root)
        target = self.root / "output"
        app.input_path.set(str(source))
        app.output_dir.set(str(target))
        app.preflight_step._start_preflight()
        self.wait_for(lambda: bool(app.preflight_results))
        self.assertEqual(len(app.preflight_results), 3)
        self.assertEqual(sum(row.status == "ignored" for row in app.preflight_results), 1)
        ignored = next(i for i, row in enumerate(app.preflight_results) if row.status == "ignored")
        app.preflight_step.preflight_table.selection_set(str(ignored))
        app.preflight_step._toggle_preflight_item()
        self.assertFalse(app.preflight_results[ignored].include)
        app.processing_step._start_processing()
        app.output_dir.set(str(self.root / "changed-after-start"))
        app.profile.set("CSV")
        self.wait_for(lambda: app.current_step == 4)
        self.assertEqual(app.notebook.select(), str(app.result_tab))
        self.assertEqual(len(app.result_step.result_table.get_children()), 2)
        run = Path(app.result_output_path.get())
        self.assertEqual(run.parent, target.resolve() / "runs")
        self.assertTrue((run / "exports/emails.parquet").exists())
        self.assertTrue((target / ".mailanalyst_cache/mail_metadata.sqlite3").exists())
        self.assertTrue((run / "exports/mail_workspace/index.jsonl").exists())
        self.assertEqual(len(json.loads((run / "exports/emails.json").read_text(encoding="utf-8"))), 2)
        self.assertFalse((self.root / "changed-after-start").exists())

    def test_background_errors_arrive_on_main_thread(self):
        self.wait_for(lambda: bool(self.app.system_check_results))
        received = []

        def fail(progress):
            raise ValueError("synthetic failure")

        main_thread = threading.get_ident()
        self.app.jobs.submit(fail, lambda _: self.fail("Unexpected success"),
                             lambda error: received.append((error, threading.get_ident())), lambda *args: None)
        self.wait_for(lambda: bool(received))
        self.assertEqual(received, [("synthetic failure", main_thread)])

    def test_large_result_uses_bounded_preview_and_total_counts(self):
        import pandas as pd
        self.wait_for(lambda: bool(self.app.system_check_results))
        frame = pd.DataFrame([{"subject": "synthetic", "parse_status": "ok"}] * 600)
        frame.attrs.update(total_messages=50000, total_errors=3)
        self.app.result_step.show_results(frame, 1, self.root)
        self.assertEqual(len(self.app.result_step.result_table.get_children()), 500)
        self.assertIn("50000 Nachrichten", self.app.result_step.result_status.get())
        self.assertIn("3 Parserfehler", self.app.result_step.result_status.get())

    def test_preflight_selection_is_keyboard_accessible(self):
        from mailanalyst.checks.preflight import PreflightResult

        step = self.app.preflight_step
        row = PreflightResult("synthetic.eml", ".eml", 10, 0, "ok", "synthetic", True)
        step._finish_preflight([row])
        step.preflight_table.selection_set("0")
        self.assertTrue(step.preflight_table.bind("<Return>"))
        step._toggle_preflight_item()
        self.assertFalse(row.include)
        self.assertEqual(step.preflight_table.set("0", "include"), "Nein")

    def test_core_columns_fit_and_details_dialog_has_parent(self):
        system = self.app.system_step.system_table
        preflight = self.app.preflight_step.preflight_table
        result = self.app.result_step.result_table
        self.assertGreaterEqual(system.column("check", "width"), 250)
        self.assertGreaterEqual(preflight.column("include", "width"), 100)
        core = ("sent_datetime_de", "from_email", "subject", "file_ext", "parse_status")
        self.assertLessEqual(sum(result.column(name, "width") for name in core), 820)

        result.insert("", "end", iid="0", values=("",) * len(result["columns"]))
        result.selection_set("0")
        self.app.result_step.page_rows = {"0": {"subject": "Test", "source_path": "synthetic.eml",
                                                  "parse_status": "ok", "parse_error": ""}}
        with patch("mailanalyst.gui.steps.result.messagebox.showinfo") as showinfo:
            self.app.result_step._show_details()
        self.assertIs(showinfo.call_args.kwargs["parent"], self.app)

    def test_config_actions_fit_at_minimum_size_and_dialogs_have_parent(self):
        self.app.geometry("980x640")
        self.app.deiconify()
        self.app.update_idletasks()
        button = self.app.config_step.start_button
        self.assertLessEqual(button.winfo_rooty() + button.winfo_height(),
                             self.app.winfo_rooty() + self.app.winfo_height())

        with patch("mailanalyst.gui.steps.config.filedialog.askdirectory", return_value="") as askdirectory:
            self.app.config_step._choose_output()
        self.assertIs(askdirectory.call_args.kwargs["parent"], self.app)
