"""Enforce module size, dependency direction and acyclic package imports."""

import ast
import importlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ArchitectureTests(unittest.TestCase):
    def test_python_files_stay_within_200_lines(self):
        paths = list(ROOT.glob("*.py"))
        for directory in ("mailanalyst", "tests", "scripts"):
            paths.extend((ROOT / directory).rglob("*.py"))
        oversized = {str(path.relative_to(ROOT)): len(path.read_text(encoding="utf-8").splitlines())
                     for path in paths if len(path.read_text(encoding="utf-8").splitlines()) > 200}
        self.assertEqual(oversized, {})

    def test_package_dependencies_are_acyclic_and_do_not_import_entrypoints(self):
        graph = {}
        for path in (ROOT / "mailanalyst").rglob("*.py"):
            module = ".".join(path.relative_to(ROOT).with_suffix("").parts)
            dependencies = set()
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if isinstance(node, ast.ImportFrom):
                    dependencies.add(node.module or "")
                elif isinstance(node, ast.Import):
                    dependencies.update(alias.name for alias in node.names)
            self.assertFalse(dependencies & {"mail_analyst", "mail_analyst_gui", "preflight", "system_check"}, module)
            if not module.startswith("mailanalyst.gui"):
                self.assertFalse(any(d.startswith(("tkinter", "mailanalyst.gui")) for d in dependencies), module)
            graph[module] = {d for d in dependencies if d.startswith("mailanalyst.")}
        visited = set()

        def visit(module, ancestors):
            self.assertNotIn(module, ancestors, f"Import cycle: {ancestors} -> {module}")
            if module in visited:
                return
            for dependency in graph.get(module, ()):
                visit(dependency, ancestors + [module])
            visited.add(module)

        for module in graph:
            visit(module, [])
            importlib.import_module(module)
