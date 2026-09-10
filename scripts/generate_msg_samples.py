"""Create a fresh synthetic MSG corpus and explicit expectations for manual tests."""

import argparse
import json
from pathlib import Path

from tests.msg_samples import CASES, create_msg_sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New directory; must not exist")
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False)
    source = create_msg_sources(root)
    (root / "expected.json").write_text(json.dumps(CASES, ensure_ascii=False, indent=2), encoding="utf-8")
    print(source)


if __name__ == "__main__":
    main()
