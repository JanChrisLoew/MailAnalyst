"""Exercise the real Tk event loop with synthetic sources and isolated output."""

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
        for event in self.app.tk.call("after", "info"):
            self.app.after_cancel(event)
        self.app.destroy()
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
        self.assertEqual(len(app.preflight_results), 2)
        app.processing_step._start_processing()
        app.output_dir.set(str(self.root / "changed-after-start"))
        app.profile.set("CSV")
        self.wait_for(lambda: app.current_step == 4)
        self.assertEqual(len(app.result_step.result_table.get_children()), 2)
        self.assertEqual(app.result_output_path.get(), str(target.resolve()))
        self.assertTrue((target / "emails.parquet").exists())
        self.assertTrue((target / ".mailanalyst_cache/mail_metadata.pkl").exists())
        self.assertTrue((target / "mail_workspace/index.jsonl").exists())
        self.assertEqual(len(json.loads((target / "emails.json").read_text(encoding="utf-8"))), 2)
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
