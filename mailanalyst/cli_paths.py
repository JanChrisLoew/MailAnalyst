"""Reject destructive collisions among CLI sources and destinations."""

from mailanalyst.cache import sqlite_path
from mailanalyst.discovery import discover_mail_files
from mailanalyst.logging_setup import default_log_path


def validate_paths(args):
    sources = {path.resolve() for path in discover_mail_files(args.input)}
    files = [args.output.resolve(), (args.log_output or default_log_path(args.output)).resolve(),
             sqlite_path(args.cache).resolve()]
    if args.list_output:
        files.append(args.list_output.resolve())
    if len(set(files)) != len(files) or sources.intersection(files):
        raise ValueError("Quellen, Cache, Log und Exportdateien brauchen getrennte Pfade")
    if args.markdown_dir:
        directory = args.markdown_dir.resolve()
        protected = sources | set(files) | {args.output.parent.resolve() / "runs"}
        if any(path == directory or path.is_relative_to(directory) for path in protected):
            raise ValueError("Markdown-Ziel darf Quellen oder andere Ausgaben nicht enthalten")
