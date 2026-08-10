"""Fail closed when a generated CUMCM paper loses the strict layout profile."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = {
    "A4 margins": ("left=2.5cm", "right=2.5cm", "top=2.5cm", "bottom=2.8cm"),
    "Song/Hei fonts": ("SimSun", "SimHei"),
    "paragraph spacing": (r"\setlength{\parindent}{2em}", r"\linespread{1.65}"),
    "heading hierarchy": (r"\titleformat{\section}", r"\titleformat{\subsection}", r"\fontsize{15pt}{22pt}"),
    "float and three-line tables": (r"\setlength{\floatsep}", r"\toprule", r"\midrule", r"\bottomrule"),
    "front matter and contents": (r"\PaperTitle", "摘\\quad 要", r"\tableofcontents"),
    "no running header": (r"\pagestyle{plain}",),
    "abstract and body reset": (r"\pagenumbering{arabic}\setcounter{page}{1}",),
    "caption, bibliography, code appendix": (
        r"\@makecaption",
        r"\begin{thebibliography}",
        r"\begin{pycode}",
        "numbers=left",
        "numbersep=7pt",
    ),
}


def validate_layout(tex_path: Path) -> dict[str, object]:
    text = tex_path.read_text(encoding="utf-8")
    missing = {name: [token for token in tokens if token not in text] for name, tokens in REQUIRED.items()}
    missing = {name: tokens for name, tokens in missing.items() if tokens}
    return {
        "status": "FAIL" if missing else "PASS",
        "profile": "cumcm_modeling_paper_v2",
        "tex_path": str(tex_path),
        "checks": {
            name: {"passed": name not in missing, "missing_tokens": missing.get(name, [])}
            for name in REQUIRED
        },
    }


def main(tex_path: Path, report_path: Path | None = None) -> int:
    report = validate_layout(tex_path)
    missing = {
        name: check["missing_tokens"]
        for name, check in report["checks"].items()
        if not check["passed"]
    }
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if missing:
        for name, tokens in missing.items():
            print(f"FAIL {name}: {', '.join(tokens)}")
        return 1
    print(f"PASS strict_cumcm_layout {tex_path}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tex", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    raise SystemExit(main(args.tex, args.report))
