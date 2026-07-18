#!/usr/bin/env python3
"""Check dependencies and the repository algorithm package without changing files."""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path


REQUIRED = ("numpy", "scipy", "matplotlib", "pandas", "sklearn", "networkx")


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    missing: list[str] = []
    versions: dict[str, str] = {}

    for name in REQUIRED:
        try:
            module = importlib.import_module(name)
            versions[name] = getattr(module, "__version__", "unknown")
        except Exception as exc:  # dependency diagnostics must report all failures
            missing.append(f"{name}: {exc}")

    algorithm_error = None
    export_count = None
    if not missing:
        sys.path.insert(0, str(repo_root / "code"))
        try:
            algorithms = importlib.import_module("algorithms")
            export_count = len(getattr(algorithms, "__all__", ()))
        except Exception as exc:
            algorithm_error = f"{type(exc).__name__}: {exc}"

    report = {
        "ok": not missing and algorithm_error is None,
        "python": sys.version.split()[0],
        "repo_root": str(repo_root),
        "versions": versions,
        "missing": missing,
        "algorithm_error": algorithm_error,
        "algorithm_exports": export_count,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
