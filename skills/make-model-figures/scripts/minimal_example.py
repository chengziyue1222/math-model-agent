"""Executable synthetic demonstration; needs installed math-model-agent package.

python <skill>/scripts/minimal_example.py --output figures --suite
No repository checkout or author-specific paths are required.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

# Help must remain available even when the optional installed runtime is
# missing.  Parse and exit before importing any package from the wheel.
if any(argument in {"-h", "--help"} for argument in sys.argv[1:]):
    _help_parser = argparse.ArgumentParser(description=__doc__)
    _help_parser.add_argument("--output", type=Path, default=Path("figure-demo"))
    _help_parser.add_argument("--suite", action="store_true")
    _help_parser.parse_args()
    raise SystemExit(0)

# An optional isolated wheel environment avoids replacing other installed algorithms.
# Normal installations simply import the package. No author-specific path is stored.
try:
    if importlib.util.find_spec("algorithms.figure_templates") is None:
        raise ModuleNotFoundError("algorithms.figure_templates")
except ModuleNotFoundError:
    runtime_root = Path(__file__).resolve().parents[3] / "runtimes/math-model-figures"
    candidate = Path(os.environ.get("MATH_MODEL_FIGURES_PYTHON", str(
        runtime_root / ("Scripts/python.exe" if os.name == "nt" else "bin/python"))))
    if candidate.is_file() and candidate.resolve() != Path(sys.executable).resolve():
        raise SystemExit(subprocess.call([str(candidate), str(Path(__file__).resolve()), *sys.argv[1:]]))
    raise SystemExit("Install the repository-built math-model-agent wheel, or set MATH_MODEL_FIGURES_PYTHON to its environment's Python.")

import numpy as np
import matplotlib as mpl

from algorithms.figure_templates import render_template, template_registry
from algorithms.sci_figures import FigureContract, FigureDesignBrief, export_publication_figure, paper_figure_rc_params


def examples():
    x = np.linspace(0, 10, 81)
    return {
        "comparison": dict(names=["基线模型", "带物理约束的预测模型（中文长标签示例）", "方案乙"],
                           values=[3.1, 1.8, 2.4], metric="MAE", direction="min", split="synthetic test", units="m"),
        "prediction": dict(x=x.tolist(), observed=np.sin(x).tolist(), predicted=(np.sin(x)+.1*np.cos(x)).tolist(),
                           forecast_start=6, residuals=True, units="m"),
        "optimization": dict(iterations=list(range(1,21)), objective=(10/np.arange(1,21)).tolist(), units="s",
                             runs=[.45,.5,.52,.48], constraint_names=["容量", "资源"], slack=[.2,.4], slack_units="1"),
        "sensitivity": dict(x=[0,1,2,3], y=[0,1,2], response=[[0,1,2,3],[1,2,3,4],[2,3,4,5]],
                            feasible=[[False,False,True,True],[False,True,True,True],[True,True,True,True]], threshold=3, units="W"),
        "robustness": dict(names=["基准", "低需求", "高需求"], benefit=[4,3,6], risk=[1,2,4], risk_units="1", units="万元", failure_threshold=2),
        "mechanism": dict(nodes=[dict(id=str(i),label=label,stage=stage) for i,(label,stage) in enumerate(
            [("输入数据", "input"),("变量与约束", "variables"),("模型求解", "solve"),("独立验证", "validate"),("决策输出", "output")])],
            edges=[[str(i),str(i+1)] for i in range(4)], units="not applicable; declared dependencies"),
    }


def main(output, suite=False):
    output.mkdir(parents=True, exist_ok=True)
    cases = examples()
    if not suite:
        cases = {"comparison": cases["comparison"]}
    for name, data in cases.items():
        source = output / f"demo_{name}_data.json"
        source.write_text(json.dumps({"synthetic": True, "data": data}, ensure_ascii=False, indent=2), encoding="utf-8")
        fig = render_template(name, data, height_mm=135 if name in {"optimization", "mechanism"} else 90)
        with mpl.rc_context(paper_figure_rc_params(config=fig._figure_config)):
            fig.suptitle("合成数据演示 · " + name)
        claim = ("合成比较样例：约束模型MAE为1.8 m，低于基线3.1 m" if name=="comparison"
                 else "待检验（合成演示）：" + template_registry()[name]["question"])
        contract = FigureContract(
            claim, ("explicit synthetic demonstration inputs",), source_paths=(str(source.resolve()),),
            plotting_code=(str(Path(__file__).resolve()),), width_mm=fig.get_figwidth()*25.4,
            height_mm=fig.get_figheight()*25.4, question=template_registry()[name]["question"],
            units=data["units"], claim_status="verified" if name=="comparison" else "question",
            model_name="synthetic demonstration", scenario="synthetic; not a scientific finding",
            randomness="fixed formulas and arrays; no random sampling", n_definition="all supplied demo rows",
            statistic="raw supplied values", uncertainty="no interval supplied", data_transformations=("comparison sorted by MAE; residual=observed-predicted",),
            design_brief=FigureDesignBrief(claim),
        )
        paths = export_publication_figure(fig, output / f"demo_{name}", contract, close=True)
        print(paths["metadata"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("figure-demo"))
    parser.add_argument("--suite", action="store_true")
    args = parser.parse_args()
    main(args.output, args.suite)
