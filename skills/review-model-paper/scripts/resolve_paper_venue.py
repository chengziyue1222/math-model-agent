"""Resolve explicit paper venue configuration through the installed library."""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--venue", choices=["CUMCM", "MCM/ICM", "MathorCup", "journal", "generic-research-report"])
    parser.add_argument("--config", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    from algorithms.venue_config import load_venue_config
    result = json.dumps(load_venue_config(args.config, venue=args.venue), ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result + "\n", encoding="utf-8")
    print(result)


if __name__ == "__main__":
    main()
