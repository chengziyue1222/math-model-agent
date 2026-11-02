"""Resolve writing/review policy without imposing a contest on generic work."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--venue", choices=["CUMCM", "MCM/ICM", "MathorCup", "journal", "generic-research-report"])
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "code"))
    from algorithms.venue_config import load_venue_config
    result = load_venue_config(args.config, venue=args.venue)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
