"""Regenerate maintained repository counts and the current figure index."""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from algorithms import __all__
from algorithms.figures import list_figures


def main():
    modules = sum(p.name != "__init__.py" for p in (ROOT / "code/algorithms").glob("*.py"))
    exports = len(__all__)
    for name in ("README.md", "使用说明.md", "code/algorithms/__init__.py"):
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        text = re.sub(r"\d+ 个(?: Python)?算法与质量模块", lambda m: f"{modules} 个" + (" Python" if "Python" in m[0] else "") + "算法与质量模块", text)
        text = re.sub(r"\d+ 个模块文件", f"{modules} 个模块文件", text)
        text = re.sub(r"\d+ 个公开导出", f"{exports} 个公开导出", text)
        path.write_text(text, encoding="utf-8")
    from scripts.generate_figure_capability_matrix import generate
    generate(ROOT / "docs/figure-library-capability-matrix.md")
    print(f"Generated {modules} module files, {exports} public exports and {len(list_figures())} figure entries")


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    main()
