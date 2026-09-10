"""Check local file targets in maintained project documentation (not historical reports)."""

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def main():
    files = [ROOT / name for name in ("README.md", "PROJECT_GOALS.md", "AGENTS.md", "docs/STATUS.md")]
    files.extend((ROOT / "docs/01_guides").glob("*.md"))
    missing = []
    for path in files:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if "://" not in target and not target.startswith("#"):
                target = target.split("#")[0]
                if not (path.parent / target).exists():
                    missing.append(f"{path.relative_to(ROOT)}: {target}")
    if missing:
        raise SystemExit("\n".join(missing))
    print(f"Local link targets verified in {len(files)} documents; section anchors are not checked.")


if __name__ == "__main__":
    main()
