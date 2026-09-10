"""Record the source tree and installed dependency versions for a local build."""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import subprocess
import zipfile
from datetime import datetime, timezone

from mailanalyst.version import APP_VERSION

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, timeout=15)


def metadata(snapshot=None):
    paths = sorted(set(git("ls-files", "-z", "--cached", "--others", "--exclude-standard").split(b"\0")))
    digest = hashlib.sha256()
    contents = {}
    for name in paths:
        if not name:
            continue
        path = ROOT / name.decode("utf-8")
        if not path.is_file():
            continue
        data = path.read_bytes()
        digest.update(name + b"\0" + hashlib.sha256(data).digest())
        contents[name.decode("utf-8")] = data
    if snapshot is not None:
        with zipfile.ZipFile(snapshot, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in contents.items():
                archive.writestr(name, data)
    return {"app_version": APP_VERSION, "build_status": "built",
            "built_at": datetime.now(timezone.utc).isoformat(), "python": platform.python_version(),
            "source_revision": git("rev-parse", "HEAD").decode().strip(),
            "source_dirty": bool(git("status", "--porcelain")), "source_tree_sha256": digest.hexdigest(),
            "dependencies": dict(sorted((d.metadata["Name"], d.version) for d in importlib.metadata.distributions()))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(metadata(args.output.parent / "source_snapshot.zip"), indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
