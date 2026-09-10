"""Write checksums for a completed portable package."""

import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    root = args.directory.resolve()
    destination = root / "package_manifest.json"
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path != destination:
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            rows.append({"path": path.relative_to(root).as_posix(), "size": path.stat().st_size, "sha256": digest})
    destination.write_text(json.dumps(rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
