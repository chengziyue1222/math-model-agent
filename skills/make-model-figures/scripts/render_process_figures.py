"""Problem adapter: export traceable figures for the chemical-process forecast."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import roc_curve

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT / "code") not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT / "code"))

from algorithms.figure_config import load_figure_config
from algorithms.sci_figures import FigureContract, export_publication_figure, publication_rc_params, publication_size


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _claim_binding(root: Path, figure_id: str):
    from algorithms.figure_handoff import claim_binding
    return claim_binding(root, figure_id)


def main(root: Path) -> None:
    figures, results, paper = root / "figures", root / "results", root / "paper"
    figures.mkdir(exist_ok=True)
    panel, q1, q2, q3, tradeoff = (pd.read_csv(path) for path in (root / "data" / "processed" / "process_panel.csv", results / "q1_predictions.csv", results / "q2_alert_predictions.csv", results / "q3_time_predictions.csv", results / "q2_threshold_tradeoff.csv"))
    project_config = root / "config/paper_style.yaml"
    cfg = load_figure_config(project_config if project_config.exists() else {})
    specs: list[tuple[str, str, str, plt.Figure]] = []
    with plt.rc_context(publication_rc_params(config=cfg)):
        fig, ax = plt.subplots(figsize=publication_size(None, 65, config=cfg)); sample=panel.iloc[:1000]; ax.plot(sample.time, sample.SO2, label="SO2", lw=.8); ax.plot(sample.time, sample.H2S, label="H2S", lw=.8); ax.set(xlabel="time", ylabel="standardized output", title="Output concentrations in the first 1,000 samples"); ax.legend(); specs.append(("FIG_RAW_OUTPUT", "fig_raw_output", "data/processed/process_panel.csv", fig))
        fig, ax = plt.subplots(figsize=publication_size(None, 70, config=cfg)); image=ax.imshow(panel.drop(columns="time").corr(), cmap="coolwarm", vmin=-1, vmax=1); ax.set_xticks(range(7), panel.drop(columns="time").columns, rotation=45, ha="right"); ax.set_yticks(range(7), panel.drop(columns="time").columns); fig.colorbar(image, ax=ax, label="correlation"); ax.set_title("Input-output correlation matrix"); specs.append(("FIG_CORRELATION", "fig_correlation", "data/processed/process_panel.csv", fig))
        fig, axes = plt.subplots(1, 2, figsize=publication_size(None, 68, config=cfg));
        for axis, actual, predicted, label in zip(axes, (q1.SO2_actual, q1.H2S_actual), (q1.SO2_prediction, q1.H2S_prediction), ("SO2", "H2S")):
            axis.scatter(actual, predicted, s=4, alpha=.35); lo=min(actual.min(), predicted.min()); hi=max(actual.max(), predicted.max()); axis.plot([lo,hi],[lo,hi],"r--",lw=.8); axis.set(xlabel="actual", ylabel="prediction", title=label)
        fig.suptitle("Q1 chronological test predictions"); specs.append(("FIG_Q1_SCATTER", "fig_q1_scatter", "results/q1_predictions.csv", fig))
        fig, axes = plt.subplots(1, 2, figsize=publication_size(None, 65, config=cfg));
        for axis, residual, label in zip(axes, (q1.SO2_actual-q1.SO2_prediction, q1.H2S_actual-q1.H2S_prediction), ("SO2 residual", "H2S residual")):
            axis.hist(residual, bins=35, color="#4C78A8", alpha=.8); axis.axvline(0,color="black",lw=.7); axis.set(title=label, xlabel="actual - prediction")
        fig.suptitle("Q1 residual distributions"); specs.append(("FIG_Q1_RESIDUAL", "fig_q1_residual", "results/q1_predictions.csv", fig))
        fig, ax = plt.subplots(figsize=publication_size(None, 65, config=cfg)); ax.plot(tradeoff["quantile"], tradeoff["f1"], marker="o", label="F1"); ax.plot(tradeoff["quantile"], tradeoff["accuracy"], marker="s", label="accuracy"); ax.plot(tradeoff["quantile"], tradeoff["roc_auc"], marker="^", label="ROC-AUC"); ax.set(xlabel="training output quantile used as threshold", ylabel="validation score", title="Q2 threshold strictness trade-off"); ax.legend(); specs.append(("FIG_Q2_TRADEOFF", "fig_q2_tradeoff", "results/q2_threshold_tradeoff.csv", fig))
        fig, ax = plt.subplots(figsize=publication_size(None, 65, config=cfg)); fpr,tpr,_=roc_curve(q2.actual_event,q2.event_probability); ax.plot(fpr,tpr,label="test ROC"); ax.plot([0,1],[0,1],"k--",lw=.7); ax.set(xlabel="false positive rate",ylabel="true positive rate",title="Q2 future-window alert discrimination"); ax.legend(); specs.append(("FIG_Q2_ROC", "fig_q2_roc", "results/q2_alert_predictions.csv", fig))
        fig, ax = plt.subplots(figsize=publication_size(None, 65, config=cfg)); ordered=q2.iloc[:400]; ax.plot(ordered.time, ordered.event_probability, lw=.8); ax.scatter(ordered.time[ordered.actual_event==1], ordered.event_probability[ordered.actual_event==1], s=8, color="crimson", label="actual future event"); ax.set(xlabel="forecast origin",ylabel="event probability",title="Q2 alert probabilities over chronological test origins"); ax.legend(); specs.append(("FIG_Q2_PROBABILITY", "fig_q2_probability", "results/q2_alert_predictions.csv", fig))
        fig, ax = plt.subplots(figsize=publication_size(None, 65, config=cfg)); events=q3[q3.actual_event==1]; ax.scatter(events.actual_first_delay, events.predicted_first_delay, s=7, alpha=.45); ax.plot([10,70],[10,70],"r--",lw=.8); ax.set(xlabel="actual first-event delay",ylabel="predicted delay",title="Q3 timing prediction on actual future events"); specs.append(("FIG_Q3_TIMING", "fig_q3_timing", "results/q3_time_predictions.csv", fig))
    registry, audits = [], []
    for figure_id, stem_name, data_file, fig in specs:
        fig.tight_layout()
        stem = figures / stem_name
        exported = export_publication_figure(fig, stem, FigureContract(claim="待检验：" + (fig._suptitle.get_text() if fig._suptitle else fig.axes[0].get_title()), claim_status="question", question="Verify the displayed process-model evidence on the stated chronological split", width_mm=fig.get_figwidth()*25.4, height_mm=fig.get_figheight()*25.4, plotting_code=(str(Path(__file__).resolve()),), units="standardized process variable, probability or delay", uncertainty="no intervals estimated", data_transformations=({"FIG_RAW_OUTPUT": "first 1000 source rows", "FIG_CORRELATION": "Pearson correlation excluding time; diverging midpoint 0 means no linear correlation", "FIG_Q1_RESIDUAL": "actual-prediction; histogram with 35 bins", "FIG_Q2_PROBABILITY": "first 400 test origins", "FIG_Q3_TIMING": "filter actual_event==1", "FIG_Q2_ROC": "ROC computed from actual_event and event_probability"}.get(figure_id, "raw saved values on declared split"),), evidence=(figure_id,), source_paths=(str((root/data_file).resolve()),), model_name="chemical process temporal forecast", randomness="deterministic model seed 20260728", n_definition="chronological test rows or listed source rows", statistic="displayed raw value or held-out metric"), close=True, config=cfg)
        metadata_path=Path(exported["metadata"]); metadata=json.loads(metadata_path.read_text(encoding="utf-8")); metadata["source_data"]={"path":data_file,"sha256":sha(root/data_file)}; metadata_path.write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        claim_ids, inserted, completion_status = _claim_binding(root, figure_id)
        registry.append({"figure_id":figure_id,"path":str(stem.with_suffix('.pdf').relative_to(root)).replace('\\\\','/'),"metadata":str(metadata_path.relative_to(root)).replace('\\\\','/'),"data_file":data_file,"data_sha256":sha(root/data_file),"claim_ids":claim_ids,"unit":"standardized process variable or probability","title":figure_id,"sample_size":int(len(pd.read_csv(root/data_file))),"sample_definition":"source rows; displayed filters recorded in metadata","visual_review":metadata["visual_review"],"completion_status":completion_status,"inserted_in_body":inserted,"sha256":sha(stem.with_suffix('.pdf'))})
        audits.append({"figure_id":figure_id,"metadata":str(metadata_path.relative_to(root)).replace('\\\\','/'),**metadata["audit"]})
    (paper / "figure-registry.json").write_text(json.dumps(registry,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (root / "reports" / "figure_audit_report.json").write_text(json.dumps({"status":"NEEDS_VISUAL_REVIEW" if all(item["passed"] for item in audits) else "FAIL","visual_review":"NOT_CHECKED","figure_count":len(audits),"format":"pdf/svg/png at 450 dpi","audits":audits},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--root",type=Path,required=True); main(parser.parse_args().root)
