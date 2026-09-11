"""Download the pinned public libpff PST fixture into an ignored directory."""

import argparse
from pathlib import Path
from urllib.request import urlopen

from tests.pst_fixture import PST_FIXTURE_SHA256, PST_FIXTURE_URL, require_fixture


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists():
        raise ValueError(f"Zieldatei existiert bereits: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urlopen(PST_FIXTURE_URL, timeout=60) as response:
            data = response.read()
        output.write_bytes(data)
        require_fixture(output)
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    print(f"PST-Testdatei: {output}")
    print(f"SHA-256: {PST_FIXTURE_SHA256}")


if __name__ == "__main__":
    main()
