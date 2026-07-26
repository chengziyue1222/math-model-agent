"""Fail closed when a generated CUMCM paper loses the strict layout profile."""
from __future__ import annotations

import argparse
from pathlib import Path


REQUIRED = {
    "A4 margins": ("left=3.17cm", "right=3.17cm", "top=2.54cm", "bottom=2.54cm"),
    "Song/Hei fonts": ("SimSun", "SimHei"),
    "paragraph spacing": (r"\setlength{\parindent}{2em}", r"\linespread{1.5}"),
    "heading hierarchy": (r"\titleformat{\section}", r"\titleformat{\subsection}", r"\fontsize{16pt}{24pt}"),
    "float and three-line tables": (r"\setlength{\floatsep}", r"\toprule", r"\midrule", r"\bottomrule"),
    "cover": (r"\thispagestyle{empty}\pagenumbering{gobble}", r"\vspace*{7cm}"),
    "abstract and body reset": ("摘\\quad 要", r"\pagenumbering{arabic}\setcounter{page}{1}"),
    "caption, bibliography, code appendix": (r"\@makecaption", r"\begin{thebibliography}", r"\begin{pycode}"),
}


def main(tex_path: Path) -> int:
    text = tex_path.read_text(encoding="utf-8")
    missing = {name: [token for token in tokens if token not in text] for name, tokens in REQUIRED.items()}
    missing = {name: tokens for name, tokens in missing.items() if tokens}
    if missing:
        for name, tokens in missing.items():
            print(f"FAIL {name}: {', '.join(tokens)}")
        return 1
    print(f"PASS strict_cumcm_layout {tex_path}")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tex", required=True, type=Path)
    raise SystemExit(main(parser.parse_args().tex))
