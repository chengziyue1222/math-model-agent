"""Create a structured, evidence-first model plan for the 2021C supplier-chain case."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def dump(root: Path, relative: str, value) -> None:
    path = root / relative; path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def main(root: Path) -> None:
    decomposition = {"problem_id":"cumcm-2021-c", "questions":[
        {"id":"Q1","objective":"rank 402 suppliers and publish the full Top-50","validation":"bootstrap rank stability"},
        {"id":"Q2","objective":"minimum robust supplier set and 24-week ordering/transport plan","validation":"inventory and capacity constraints"},
        {"id":"Q3","objective":"material-mix procurement policy","validation":"cost-risk Pareto comparison"},
        {"id":"Q4","objective":"maximum feasible weekly capacity","validation":"supplier and carrier bounds"}]}
    candidates = [{"name":"entropy-CRITIC TOPSIS","use":"Q1","risk":"ordinal assumptions"},{"name":"MILP","use":"Q2/Q4","risk":"scenario simplification"},{"name":"rolling LP","use":"Q2/Q3","risk":"forecast dependence"}]
    dump(root,"results/problem_decomposition.json",decomposition); dump(root,"results/candidate_models.json",candidates)
    dump(root,"results/baseline_plan.json",{"name":"equal-share feasible allocation","validation":"compare cost and supplier count"})
    dump(root,"results/selected_model_plan.json",{"primary":"rank consensus + robust MILP + rolling LP","disclosure":"Q2 is decomposed, not an integrated robust optimization model"})
    dump(root,"results/risk_register.json",[{"risk":"supplier-count explosion","mitigation":"report implementation complexity"},{"risk":"static schedule","mitigation":"rolling weekly capacities"}])
    (root/"reports").mkdir(exist_ok=True); (root/"reports/model_selection_report.md").write_text("# Model selection\n\nFour questions are solved by a disclosed decomposition: ranking, set selection, rolling allocation, and capacity maximization. A simple feasible allocation is retained as a baseline.\n",encoding="utf-8")

if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--root",type=Path,required=True); main(parser.parse_args().root)
