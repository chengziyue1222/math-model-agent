import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from scripts.run_standard_skill import main

if __name__ == "__main__":
    raise SystemExit(main(default_skill="research-model-literature"))
