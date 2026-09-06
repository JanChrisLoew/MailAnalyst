"""Exercise busy, cancel, restart and close with a live Tk event loop."""

import json
import threading
import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import patch

import tests.test_gui as gui_tests
from mailanalyst.parsing.dispatch import parse_mail_file
from tests.samples import create_sources


class GuiSafetyTests(unittest.TestCase):
    setUp = gui_tests.GuiTests.setUp
    wait_for = gui_tests.GuiTests.wait_for

    def close_app(self):
        if self.app.jobs.thread is not None:
            self.app.jobs.cancel()
            self.app.jobs.thread.join(timeout=6)
        try:
            exists = self.app.winfo_exists()
        except tk.TclError:
            exists = False
        if exists:
            gui_tests.GuiTests.close_app(self)
        else:
            from mailanalyst.config import LOGGER
            for handler in LOGGER.handlers[:]:
                handler.close()
                LOGGER.removeHandler(handler)

    def prepare(self):
        self.wait_for(lambda: bool(self.app.system_check_results))
        self.source = create_sources(self.root)
        self.target = self.root / "output"
        self.app.input_path.set(str(self.source))
        self.app.output_dir.set(str(self.target))
        self.app.preflight_step._start_preflight()
        self.wait_for(lambda: bool(self.app.preflight_results))

    def gated_parser(self):
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)

        def parse(*args):
            entered.set()
            if not release.wait(5):
                raise RuntimeError("Test worker timeout")
            return parse_mail_file(*args)

        return entered, release, parse

    def test_double_start_navigation_cancel_and_restart(self):
        self.prepare()
        entered, release, parse = self.gated_parser()
        app = self.app
        with patch("mailanalyst.source_processing.parse_mail_file", side_effect=parse):
            app.processing_step._start_processing()
            self.wait_for(entered.is_set)
            worker = app.jobs.thread
            self.assertFalse(worker.daemon)
            app.processing_step._start_processing()
            app.preflight_step._start_preflight()
            app.system_step._start_system_check()
            app._select_step(1)
            self.assertIs(app.jobs.thread, worker)
            self.assertEqual(app.current_step, 3)
            self.assertTrue(all(button.instate(["disabled"]) for button in app.nav_buttons))
            self.assertEqual(str(app.notebook.tab(1, "state")), "disabled")
            self.assertTrue(app.preflight_step.process_button.instate(["disabled"]))
            app.activity.cancel()
            self.assertTrue(app.jobs.busy)
            release.set()
            self.wait_for(lambda: not app.jobs.busy)
        self.assertEqual(app.current_step, 2)
        manifest_path = next((self.target / "runs").glob("*/manifest.json"))
        self.assertEqual(json.loads(manifest_path.read_text(encoding="utf-8"))["status"], "cancelled")
        self.assertFalse((manifest_path.parent / "exports").exists())
        self.assertFalse(worker.is_alive())
        self.assertTrue(app.preflight_step.process_button.instate(["!disabled"]))
        app.processing_step._start_processing()
        self.wait_for(lambda: app.current_step == 4)
        self.assertEqual(len(list((self.target / "runs").iterdir())), 2)

    def test_close_waits_for_parser_and_suppresses_callbacks(self):
        self.prepare()
        entered, release, parse = self.gated_parser()
        with patch("mailanalyst.source_processing.parse_mail_file", side_effect=parse):
            self.app.processing_step._start_processing()
            self.wait_for(entered.is_set)
            worker = self.app.jobs.thread
            self.app.activity.close()
            self.assertTrue(self.app.winfo_exists())
            self.assertTrue(worker.is_alive())
            self.assertTrue(self.app.jobs.closing)
            release.set()
            self.wait_for(lambda: self.app.jobs.stopped)
        self.assertFalse(worker.is_alive())
        with self.assertRaises(tk.TclError):
            self.app.winfo_exists()
        manifest = next((self.target / "runs").glob("*/manifest.json"))
        self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["status"], "cancelled")

    def test_preflight_cancel_restores_retry_without_processing_old_sources(self):
        self.prepare()
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)

        def check(*args):
            entered.set()
            release.wait(5)
            return original(*args)

        from mailanalyst.checks.preflight import check_file as original
        with patch("mailanalyst.checks.preflight.check_file", side_effect=check):
            self.app.preflight_step._start_preflight()
            self.wait_for(entered.is_set)
            self.app.activity.cancel()
            release.set()
            self.wait_for(lambda: not self.app.jobs.busy)
        self.assertEqual(self.app.preflight_results, [])
        self.assertTrue(self.app.preflight_step.process_button.instate(["disabled"]))
        self.assertIn("abgebrochen", self.app.preflight_step.preflight_status.get())
        self.app.preflight_step._start_preflight()
        self.wait_for(lambda: bool(self.app.preflight_results))

    def test_worker_error_releases_busy_state_and_allows_next_job(self):
        self.wait_for(lambda: bool(self.app.system_check_results))
        received = []

        def fail(progress):
            raise ValueError("synthetic job error")

        self.assertTrue(self.app.jobs.submit(fail, received.append, received.append, lambda *args: None))
        self.assertFalse(self.app.jobs.submit(fail, received.append, received.append, lambda *args: None))
        self.wait_for(lambda: bool(received))
        self.assertEqual(received, ["synthetic job error"])
        self.assertFalse(self.app.jobs.busy)
        self.assertTrue(self.app.jobs.submit(lambda _: "restarted", received.append, received.append, lambda *args: None))
        self.wait_for(lambda: len(received) == 2)
        self.assertEqual(received[-1], "restarted")

    def test_close_idle_before_automatic_system_check(self):
        self.app.activity.close()
        self.assertTrue(self.app.jobs.stopped)
        with self.assertRaises(tk.TclError):
            self.app.winfo_exists()
