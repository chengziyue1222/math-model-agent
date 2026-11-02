"""Evidence-driven recipes; no simulated observations or inferred intervals."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import textwrap

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D

from .figure_config import load_figure_config, semantic_style
from .sci_figures import publication_size, paper_figure_rc_params, get_modeling_palette


@dataclass(frozen=True)
class TemplateSpec:
    question: str
    required: tuple[str, ...]
    optional: tuple[str, ...]
    conditions: str
    avoid: str
    layout: str
    caption: str
    interface: str = "render_template(name, data, config=None, **overrides)"
    units: str = "Provide units and metric/sample definitions; never infer from filenames."
    uncertainty: str = "Intervals require interval_kind; omitted intervals are not estimated."
    colors: str = "Stable object names; configured semantic_styles override deterministic mapping."
    example: str = "skills/make-model-figures/scripts/minimal_example.py"


TEMPLATES = {
    "prediction": TemplateSpec("预测在何时开始、偏差多大？", ("x", "observed", "predicted", "forecast_start", "units"),
        ("lower", "upper", "interval_kind", "residuals"), "Aligned observations and predictions on a declared split",
        "Do not mix training and test rows", "Trend; optional residual panel", "{split}; n={n}; {interval_kind}; residual = observed - predicted"),
    "comparison": TemplateSpec("统一指标下哪个模型表现更好？", ("names", "values", "metric", "direction", "split", "units"),
        ("lower", "upper", "interval_kind"), "Same split and metric definition for all models",
        "Incomparable splits; cross-fold spread labeled as independent-sample CI", "Sorted horizontal points", "{metric} ({units}), {direction}; split={split}; {interval_kind}"),
    "optimization": TemplateSpec("优化是否收敛、运行是否稳定、约束是否满足？", ("iterations", "objective", "units"),
        ("runs", "constraint_names", "slack", "slack_units"), "Saved objective sequence; slack >= 0 means feasible",
        "Do not fabricate repeated runs", "Convergence plus available run/slack panels", "Objective history; runs={n}; nonnegative slack means feasible"),
    "sensitivity": TemplateSpec("参数变化如何影响响应与可行域？", ("x", "response", "units"),
        ("y", "feasible", "threshold", "xlabel", "ylabel", "midpoint", "midpoint_meaning"), "1D response or rectangular 2D grid",
        "No smoothing/interpolation; midpoint needs scientific meaning", "Line or heatmap with feasible boundary", "Fixed remaining parameters; original response scale ({units}); threshold={threshold}"),
    "robustness": TemplateSpec("情景变化下收益、风险与失效边界如何变化？", ("names", "benefit", "units"),
        ("risk", "risk_units", "failure_threshold"), "Observed or computed scenario outputs",
        "Scenario range is not a confidence interval", "Scenario points or risk-benefit scatter", "Scenarios={names}; risk={risk_units}; failure threshold={failure_threshold}"),
    "mechanism": TemplateSpec("输入如何经变量关系、求解和验证形成输出？", ("nodes", "edges", "units"),
        (), "Nodes supply id,label,stage; stages: input,variables,solve,validate,output",
        "Edges express declared dependencies, not inferred causal effects", "Layered directed graph", "Declared model dependencies; arrows={edge meaning}"),
}


def template_registry():
    return {name: asdict(spec) for name, spec in TEMPLATES.items()}


def _numeric(data, key, ndim=1):
    values = np.asarray(data[key], dtype=float)
    if values.ndim != ndim or not values.size or not np.isfinite(values).all():
        raise ValueError(f"{key} must contain finite {ndim}D values")
    return values


def _interval(data, values):
    if not ({"lower", "upper"} & data.keys()):
        return None
    if not all(k in data for k in ("lower", "upper", "interval_kind")) or not data["interval_kind"]:
        raise ValueError("interval requires lower, upper and explicit interval_kind")
    lo, hi = _numeric(data, "lower"), _numeric(data, "upper")
    if lo.shape != values.shape or hi.shape != values.shape or np.any(lo > values) or np.any(hi < values):
        raise ValueError("interval endpoints must bracket the supplied values")
    return lo, hi


def render_template(name, data, config=None, **overrides):
    spec = TEMPLATES[name]
    missing = set(spec.required) - data.keys()
    if missing:
        raise ValueError(f"{name} missing required fields: {sorted(missing)}")
    cfg = load_figure_config(config, **overrides)
    omitted = []
    with mpl.rc_context(paper_figure_rc_params(config=cfg)):
        count = 1
        if name == "prediction" and data.get("residuals", False):
            count = 2
        if name == "optimization":
            count += int("runs" in data) + int("slack" in data)
        fig, axes = plt.subplots(count, 1, figsize=publication_size(None, None, config=cfg),
                                 squeeze=False, constrained_layout=True)
        ax = axes[0, 0]
        palette = get_modeling_palette(cfg["theme"])
        if name == "prediction":
            x, obs, pred = (_numeric(data, k) for k in ("x", "observed", "predicted"))
            if not (x.shape == obs.shape == pred.shape) or np.any(np.diff(x) <= 0):
                raise ValueError("prediction arrays must be aligned with strictly increasing x")
            ax.plot(x, obs, label="观测", **semantic_style("观测", cfg), markevery=max(1, len(x)//12))
            ax.plot(x, pred, label="预测", **semantic_style("预测", cfg), markevery=max(1, len(x)//12))
            ax.axvline(data["forecast_start"], color=palette["grey"], linestyle="--", label="预测起点")
            interval = _interval(data, pred)
            if interval:
                ax.fill_between(x, *interval, color=semantic_style("预测", cfg)["color"], alpha=.18, label=data["interval_kind"])
            else:
                omitted.append("No interval supplied; no uncertainty band drawn")
            ax.set(xlabel="时间", ylabel=data["units"])
            ax.legend(loc="upper left", bbox_to_anchor=(0, 1.3), ncol=4)
            if count == 2:
                residual = axes[1, 0]
                residual.plot(x, obs-pred, color=palette["grey"])
                residual.axhline(0, color=palette["ink"], linestyle=":")
                residual.set(xlabel="时间", ylabel=f"观测 - 预测 ({data['units']})")
                residual.sharex(ax)
            else:
                omitted.append("Residual panel not requested")
        elif name == "comparison":
            values = _numeric(data, "values")
            names = list(data["names"])
            if len(names) != len(values) or len(set(names)) != len(names):
                raise ValueError("comparison requires unique aligned model names")
            if data["direction"] not in {"min", "max"}:
                raise ValueError("direction must be min or max")
            for field in ("split", "metric"):
                if isinstance(data[field], (tuple, list)) and len(set(data[field])) != 1:
                    raise ValueError(f"comparison {field} differs between models")
            order = np.argsort(values if data["direction"] == "min" else -values, kind="stable")
            interval = _interval(data, values)
            for y, i in enumerate(order):
                style = semantic_style(names[i], cfg)
                ax.plot(values[i], y, linestyle="none", marker=style["marker"], color=style["color"])
                if interval:
                    ax.hlines(y, interval[0][i], interval[1][i], color=style["color"])
            ax.set_yticks(range(len(names)), [textwrap.fill(names[i], 16) for i in order])
            ax.invert_yaxis()
            ax.set(xlabel=f"{data['metric']} ({data['units']}) · {'越小越好' if data['direction']=='min' else '越大越好'}", ylabel="模型")
            fig._comparison_order = [names[i] for i in order]
            if not interval:
                omitted.append("No interval supplied; point estimates only")
        elif name == "optimization":
            iterations, objective = _numeric(data, "iterations"), _numeric(data, "objective")
            if iterations.shape != objective.shape:
                raise ValueError("objective and iterations must align")
            ax.plot(iterations, objective)
            ax.set(xlabel="迭代", ylabel=f"目标 ({data['units']})")
            index = 1
            if "runs" in data:
                runs = _numeric(data, "runs")
                if len(runs) < 2:
                    raise ValueError("run distribution requires at least two actual runs")
                axes[index, 0].plot(runs, np.arange(len(runs)), "o")
                axes[index, 0].set(xlabel=f"各次运行结果 ({data['units']})", ylabel="运行编号")
                index += 1
            else:
                omitted.append("No repeated runs supplied; distribution omitted")
            if "slack" in data:
                slack = _numeric(data, "slack")
                if "constraint_names" not in data or "slack_units" not in data or len(data["constraint_names"]) != len(slack):
                    raise ValueError("slack requires aligned constraint_names and slack_units")
                axes[index, 0].barh(data["constraint_names"], slack, color=palette["categorical"][0])
                axes[index, 0].axvline(0, color=palette["accent"], linestyle="--")
                axes[index, 0].set(xlabel=f"约束余量 ≥ 0 为可行 ({data['slack_units']})", ylabel="约束")
        elif name == "sensitivity":
            x = _numeric(data, "x")
            response = _numeric(data, "response", 2 if "y" in data else 1)
            if "y" in data:
                y = _numeric(data, "y")
                if response.shape != (len(y), len(x)):
                    raise ValueError("response shape must be (len(y), len(x))")
                cmap = LinearSegmentedColormap.from_list("model-sequential", palette["sequential"])
                norm = None
                if "midpoint" in data:
                    if not data.get("midpoint_meaning"):
                        raise ValueError("diverging scale requires midpoint_meaning")
                    cmap = LinearSegmentedColormap.from_list("model-diverging", palette["diverging"])
                    norm = TwoSlopeNorm(data["midpoint"], vmin=response.min(), vmax=response.max())
                ax.grid(False)
                image = ax.pcolormesh(x, y, response, shading="nearest", cmap=cmap, norm=norm, rasterized=response.size>5000)
                fig.colorbar(image, ax=ax, label=data["units"], pad=.04)
                handles = []
                if "feasible" in data:
                    feasible = np.asarray(data["feasible"], dtype=bool)
                    if feasible.shape != response.shape:
                        raise ValueError("feasible mask must match response")
                    if feasible.any() and not feasible.all():
                        ax.contour(x, y, feasible, levels=[.5], colors=[palette["ink"]], linestyles="--")
                        handles.append(Line2D([], [], color=palette["ink"], linestyle="--", label="可行域边界"))
                if "threshold" in data and response.min() < data["threshold"] < response.max():
                    ax.contour(x, y, response, levels=[data["threshold"]], colors=[palette["accent"]])
                    handles.append(Line2D([], [], color=palette["accent"], label=f"响应 = {data['threshold']} {data['units']}"))
                if handles:
                    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.02), ncol=2)
                ax.set(xlabel=data.get("xlabel", "参数 x"), ylabel=data.get("ylabel", "参数 y"))
            else:
                if x.shape != response.shape:
                    raise ValueError("x and response must align")
                ax.plot(x, response)
                if "threshold" in data:
                    ax.axhline(data["threshold"], color=palette["accent"], linestyle="--", label="阈值")
                    ax.legend()
                ax.set(xlabel=data.get("xlabel", "参数 x"), ylabel=data["units"])
        elif name == "robustness":
            benefit = _numeric(data, "benefit")
            if len(data["names"]) != len(benefit):
                raise ValueError("scenario names and benefit must align")
            risk = _numeric(data, "risk") if "risk" in data else np.arange(len(benefit))
            if risk.shape != benefit.shape or ("risk" in data and "risk_units" not in data):
                raise ValueError("risk requires aligned values and risk_units")
            for i, label in enumerate(data["names"]):
                style = semantic_style(label, cfg)
                ax.plot(risk[i], benefit[i], linestyle="none", marker=style["marker"], color=style["color"])
                ax.annotate(label, (risk[i], benefit[i]), xytext=(4, 4), textcoords="offset points")
            ax.margins(.2)
            if "risk" not in data:
                ax.set_xticks(risk, data["names"])
            if "failure_threshold" in data:
                ax.axhline(data["failure_threshold"], color=palette["accent"], linestyle="--", label="失效边界")
                ax.legend()
            ax.set(xlabel=f"风险 ({data['risk_units']})" if "risk" in data else "情景", ylabel=f"收益 ({data['units']})")
        else:
            # Reuse the existing directed layout engine; render its geometry in physical units.
            from .diagram import FlowchartLayout, FlowNode, FlowEdge
            stages = {"input", "variables", "solve", "validate", "output"}
            nodes = data["nodes"]
            if any(n.get("stage") not in stages for n in nodes):
                raise ValueError("each mechanism node requires a declared stage")
            ids = [n["id"] for n in nodes]
            if len(set(ids)) != len(ids) or any(a not in ids or b not in ids for a,b in data["edges"]):
                raise ValueError("mechanism node ids must be unique and edges must reference them")
            layout = FlowchartLayout([FlowNode(n["id"], n["label"]) for n in nodes],
                                     [FlowEdge(a, b) for a,b in data["edges"]])
            layout.auto_layout()
            positions = {key: (p["x"], -p["y"]) for key, p in layout.positions.items()}
            for a,b in data["edges"]:
                ax.annotate("", xy=positions[b], xytext=positions[a],
                            arrowprops={"arrowstyle": "->", "color": palette["grey"], "shrinkA": 18, "shrinkB": 18})
            for n in nodes:
                ax.text(*positions[n["id"]], textwrap.fill(n["label"], 18), ha="center", va="center",
                        bbox={"boxstyle": "round,pad=.5", "facecolor": "white", "edgecolor": semantic_style(n["stage"], cfg)["color"]})
            xx, yy = zip(*positions.values())
            ax.set(xlim=(min(xx)-120, max(xx)+120), ylim=(min(yy)-60, max(yy)+60))
            ax.axis("off")
        fig._figure_config = cfg
        fig._template_metadata = {"name": name, "question": spec.question, "omitted_panels": omitted,
                                  "interval_kind": data.get("interval_kind", "none supplied"),
                                  "midpoint_meaning": data.get("midpoint_meaning"),
                                  "axis_sharing": "prediction shares x; distinct optimization quantities retain separate axes"}
        return fig
