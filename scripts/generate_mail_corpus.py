"""Generate a repeatable mixed MSG/EML corpus; never overwrite an existing directory."""

import argparse
from pathlib import Path

from tests.corpus_samples import create_corpus


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeat", type=int, default=1, help="1..1000 repetitions of 22 mail variants")
    args = parser.parse_args()
    expected = create_corpus(args.output.resolve(), args.repeat)
    print(f"{len(expected)} messages: {args.output.resolve() / 'input'}")
    print("Negative probes are separate in negative/; attachment payloads are inventory placeholders.")


if __name__ == "__main__":
    main()
