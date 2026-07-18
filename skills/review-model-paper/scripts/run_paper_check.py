#!/usr/bin/env python3
"""Run the repository paper checker against a LaTeX/Typst file or directory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paper_path")
    parser.add_argument("--figures-dir", default="figures")
    parser.add_argument("--results-file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repo_root / "code"))
    try:
        from algorithms import check_paper
    except Exception as exc:
        print(f"Cannot import repository paper checker: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    report = check_paper(
        args.paper_path,
        figures_dir=args.figures_dir,
        results_file=args.results_file,
    )
    print(report.summary())
    return 0 if report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
