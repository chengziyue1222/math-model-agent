"""Compatibility entry point required by the figure-library prompt."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from build_figure_library import build

if __name__ == "__main__":
    print(build(Path(__file__).resolve().parent))
