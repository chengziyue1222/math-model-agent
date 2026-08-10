from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_canonical_paper_style_is_explicit():
    style = yaml.safe_load((ROOT / "config" / "paper_style.yaml").read_text(encoding="utf-8"))
    assert style["page"]["running_header"] == "none"
    assert style["page"]["margins_mm"]["left"] == 25
    assert style["typography"]["line_spacing"] == 1.65
    assert style["typography"]["appendix_code_pt"] == 8.5
    assert style["tables"]["style"] == "three-line"


def test_both_cumcm_templates_follow_the_canonical_layout():
    templates = (
        ROOT / "template" / "cume-template.tex",
        ROOT / "skills" / "write-model-paper" / "assets" / "cume-template.tex",
    )
    for template in templates:
        text = template.read_text(encoding="utf-8")
        assert "left=2.5cm,right=2.5cm,top=2.5cm,bottom=2.8cm" in text
        assert r"\linespread{1.65}" in text
        assert r"\pagestyle{plain}" in text
        assert r"\tableofcontents" in text
        assert r"\renewcommand{\contentsname}{目录}" in text
        assert r"\newcommand{\PaperTitle}" in text
