"""Build preview-ready figures from the real AIS/navigation data set.

The script reads ``E:\\数据要素`` without modifying that project or its raw files.
It writes a reproducible delivery bundle under ``output/real-data-preview``:
PNG proof, editable PDF/SVG, per-figure contracts, a source manifest and an
HTML gallery.  Every figure is descriptive; no simulated observations are
mixed into the plots.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm, Normalize
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from algorithms.sci_figures import (  # noqa: E402
    FigureContract,
    FigureDesignBrief,
    export_publication_figure,
    get_modeling_palette,
    publication_rc_params,
)
from algorithms.figures.base import attach_metadata  # noqa: E402


DATA_ROOT = Path(r"E:\数据要素")
OUT_ROOT = ROOT / "output" / "real-data-preview"
TRAJECTORY = DATA_ROOT / "data" / "processed" / "trajectory_cleaned.csv"
EDGES = DATA_ROOT / "data" / "processed" / "waterway_edges_weighted.csv"
NODES = DATA_ROOT / "data" / "processed" / "waterway_nodes.csv"
SHIPS = DATA_ROOT / "data" / "outputs" / "船舶特征属性_完整版.csv"


def _sha256(path: Path, chunk: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(chunk), b""):
            digest.update(block)
    return digest.hexdigest()


def _source_manifest() -> tuple[Path, dict[str, str]]:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    paths = [TRAJECTORY, EDGES, NODES, SHIPS]
    manifest = {
        "description": "Real AIS/navigation inputs used for preview figures; raw files are read-only.",
        "data_root": str(DATA_ROOT),
        "files": [
            {"path": str(path), "bytes": path.stat().st_size, "sha256": _sha256(path)}
            for path in paths
        ],
    }
    target = OUT_ROOT / "source_manifest.json"
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    hashes = {item["path"]: item["sha256"] for item in manifest["files"]}
    return target, hashes


def _load_data():
    trajectory = pd.read_csv(
        TRAJECTORY,
        usecols=["ship_name", "heading", "speed", "lat_smooth", "lon_smooth", "time"],
        parse_dates=["time"],
    )
    edges = pd.read_csv(EDGES)
    nodes = pd.read_csv(NODES)
    raw_ships = pd.read_csv(SHIPS)
    ship = raw_ships.iloc[:, [1, 4, 5, 6, 7, 8, 9, 10, 17, 18, 19, 20]].copy()
    ship.columns = [
        "ship_name", "ship_type", "length_m", "width_m", "height_m", "gt",
        "dwt", "draft_m", "ais_records", "mean_speed_kn", "max_speed_kn", "range_km",
    ]
    for column in ship.columns[2:]:
        ship[column] = pd.to_numeric(ship[column], errors="coerce")
    type_labels = {
        "dredger": "挖泥船", "type_030": "未分类（030）", "type_65": "未分类（65）",
        "type_74": "未分类（74）", "type_89": "未分类（89）",
    }
    ship["ship_type"] = ship["ship_type"].replace(type_labels)
    trajectory["ship_name"] = trajectory["ship_name"].astype(str)
    ship["ship_name"] = ship["ship_name"].astype(str)
    return trajectory, edges, nodes, ship


def _fig(title: str, *, width: float = 150, height: float = 92):
    fig, ax = plt.subplots(figsize=(width / 25.4, height / 25.4), constrained_layout=True)
    ax.set_title(title)
    return fig, ax


def _contract(*, claim: str, evidence: tuple[str, ...], source_manifest: Path,
              source_hashes: dict[str, str], units: str, n_definition: str,
              statistic: str, transformations: tuple[str, ...], risks: tuple[str, ...] = (),
              design_brief: FigureDesignBrief | None = None):
    return FigureContract(
        claim=claim,
        evidence=evidence,
        source_paths=(str(source_manifest),),
        source_hashes=source_hashes,
        target_venue="preview for mathematical-modeling results",
        column="double",
        figure_role="data-overview",
        randomness="none; computed from supplied observations",
        n_definition=n_definition,
        statistic=statistic,
        uncertainty="descriptive display; no inferential interval claimed",
        review_risks=risks,
        data_transformations=transformations,
        theme_name="modeling-default",
        design_brief=design_brief,
        width_mm=150,
        height_mm=92,
        units=units,
        plotting_code=(str(Path(__file__).resolve()),),
        claim_status="verified",
    )


def _finish(fig, key: str, name_zh: str, category: str, metadata: dict):
    attach_metadata(fig, name=key, name_zh=name_zh, category=category, **metadata)
    return fig


def _plot_trajectory_density(trajectory, source_manifest, source_hashes):
    fig, ax = _fig("AIS轨迹空间密度")
    valid = trajectory.dropna(subset=["lon_smooth", "lat_smooth"])
    counts = ax.hexbin(valid["lon_smooth"], valid["lat_smooth"], gridsize=150,
                       mincnt=1, bins="log", cmap="YlGnBu", linewidths=0)
    cb = fig.colorbar(counts, ax=ax, pad=0.02)
    cb.set_label("网格内轨迹点数（对数刻度）")
    ax.set(xlabel="经度（°E）", ylabel="纬度（°N）")
    ax.set_aspect("equal", adjustable="box")
    return fig, _contract(
        claim=f"清洗后的AIS轨迹包含 {len(valid):,} 个有效位置点，空间密度集中在主要航道范围内。",
        evidence=("lat_smooth", "lon_smooth", "hexbin count"), source_manifest=source_manifest,
        source_hashes=source_hashes, units="经纬度：度；网格计数：轨迹点数",
        n_definition="one cleaned AIS trajectory record",
        statistic="hexagonal bin count with logarithmic color normalization",
        transformations=("使用清洗后的平滑经纬度；仅去除缺失坐标记录；不抽样。",),
        risks=("该图显示轨迹覆盖和记录密度，不等同于航道通行概率。",),
    )


def _plot_ship_speed(trajectory, ship, source_manifest, source_hashes, palette):
    stats = trajectory.groupby("ship_name", as_index=False).agg(
        mean_speed_kn=("speed", "mean"), records=("speed", "size")
    ).merge(ship[["ship_name", "ship_type"]], on="ship_name", how="left")
    stats["ship_type"] = stats["ship_type"].fillna("未匹配类型")
    types = stats["ship_type"].value_counts().head(6).index.tolist()
    data = [stats.loc[stats.ship_type.eq(kind), "mean_speed_kn"].dropna().to_numpy() for kind in types]
    fig, ax = _fig("船舶层面平均航速分布")
    parts = ax.violinplot(data, positions=np.arange(len(types)), showmedians=True, showextrema=True)
    for i, body in enumerate(parts["bodies"]):
        body.set_facecolor(palette[i % len(palette)]); body.set_edgecolor("#303030"); body.set_alpha(.8)
    ax.set_xticks(np.arange(len(types)), types, rotation=25, ha="right")
    ax.set(xlabel="船舶类型", ylabel="船舶平均航速（节）")
    ax.text(.99, .02, f"船舶层面 n={len(stats):,}", transform=ax.transAxes, ha="right", va="bottom", fontsize=6)
    return fig, _contract(
        claim=f"按船舶汇总后，{len(stats):,} 艘船的平均航速在主要船舶类型间存在分布差异。",
        evidence=("speed", "ship_type", "ship-level mean speed"), source_manifest=source_manifest,
        source_hashes=source_hashes, units="航速：节",
        n_definition="one vessel, with mean computed across its cleaned AIS speed records",
        statistic="median and kernel-shaped distribution per vessel type",
        transformations=("先按船舶求平均航速，再按船舶类型分组；只展示船舶数最多的六类。",),
        risks=("类型样本量不均衡；小类别不用于总体比较。",),
    )


def _plot_edge_frequency(edges, source_manifest, source_hashes, palette):
    fig, ax = _fig("航段距离、耗时与通行频次")
    size = 20 + 80 * np.sqrt(edges["ship_count"].clip(lower=1) / edges["ship_count"].max())
    scatter = ax.scatter(edges["distance_km"], edges["mean_duration"],
                         c=edges["traversal_count"], s=size, cmap="YlOrRd",
                         norm=LogNorm(vmin=max(1, edges.traversal_count.min()), vmax=edges.traversal_count.max()),
                         alpha=.86, edgecolor="white", linewidth=.35)
    cb = fig.colorbar(scatter, ax=ax, pad=0.02); cb.set_label("航段通行次数（对数刻度）")
    ax.set(xlabel="航段距离（km）", ylabel="平均通行耗时（min）")
    ax.text(.99, .02, f"航段 n={len(edges):,}；点大小∝船舶数", transform=ax.transAxes, ha="right", va="bottom", fontsize=6)
    return fig, _contract(
        claim=f"{len(edges):,} 条航段的平均耗时与距离、通行频次共同呈现航道边权差异。",
        evidence=("distance_km", "mean_duration", "traversal_count", "ship_count"), source_manifest=source_manifest,
        source_hashes=source_hashes, units="距离：km；耗时：min；计数：次/艘",
        n_definition="one directed waterway edge",
        statistic="edge-level mean duration; color encodes traversal count",
        transformations=("船舶数用于点大小；通行次数使用对数颜色归一化；不删除边。",),
        risks=("相关关系不表示距离对耗时的因果作用。",),
    )


def _plot_time_duration(edges, source_manifest, source_hashes, palette):
    columns = ["duration_早高峰", "duration_日间", "duration_晚高峰", "duration_夜间"]
    labels = ["早高峰", "日间", "晚高峰", "夜间"]
    values = [pd.to_numeric(edges[column], errors="coerce").dropna().to_numpy() for column in columns]
    fig, ax = _fig("航段不同时段耗时分布")
    parts = ax.violinplot(values, positions=np.arange(4), showmedians=True, showextrema=True)
    for i, body in enumerate(parts["bodies"]):
        body.set_facecolor(palette[(i + 1) % len(palette)]); body.set_edgecolor("#303030"); body.set_alpha(.8)
    ax.set_xticks(np.arange(4), labels)
    ax.set(xlabel="时段", ylabel="航段平均耗时（min）")
    return fig, _contract(
        claim="航段平均耗时在早高峰、日间、晚高峰和夜间具有可比较的分布形态。",
        evidence=tuple(columns), source_manifest=source_manifest, source_hashes=source_hashes,
        units="耗时：min", n_definition="one directed edge per time-period aggregation",
        statistic="edge-level distribution with median marker",
        transformations=("四个时段字段按原始定义绘制；未合并或标准化时段。",),
        risks=("各时段的边覆盖可能不同；图中不作显著性检验。",),
    )


def _plot_network(edges, nodes, source_manifest, source_hashes, palette):
    fig, ax = _fig("航道节点与加权边网络")
    node_lookup = nodes.set_index("node_id")[["lon", "lat"]].to_dict("index")
    weights = np.log1p(edges["traversal_count"].clip(lower=0))
    norm = Normalize(vmin=float(weights.min()), vmax=float(weights.max()))
    for row, weight in zip(edges.itertuples(index=False), weights):
        left, right = node_lookup.get(row.from_node), node_lookup.get(row.to_node)
        if left is None or right is None:
            continue
        ax.plot([left["lon"], right["lon"]], [left["lat"], right["lat"]],
                color=mpl.colormaps["YlOrRd"](norm(weight)), lw=.35 + 1.3 * norm(weight), alpha=.62, zorder=1)
    node_size = 12 + 50 * np.sqrt(nodes["ship_count"].clip(lower=1) / nodes["ship_count"].max())
    points = ax.scatter(nodes["lon"], nodes["lat"], c=nodes["avg_speed"], s=node_size,
                        cmap="viridis", edgecolor="white", linewidth=.25, zorder=2)
    cb = fig.colorbar(points, ax=ax, pad=0.02); cb.set_label("节点平均航速（节）")
    ax.set(xlabel="经度（°E）", ylabel="纬度（°N）")
    ax.set_aspect("equal", adjustable="box")
    return fig, _contract(
        claim=f"航道网络由 {len(nodes):,} 个节点和 {len(edges):,} 条有向边构成，边宽反映通行频次。",
        evidence=("node coordinates", "edge endpoints", "traversal_count", "avg_speed"),
        source_manifest=source_manifest, source_hashes=source_hashes,
        units="坐标：度；边权：次；节点速度：节", n_definition="one waterway node or directed edge",
        statistic="log-scaled edge traversal count and node mean speed",
        transformations=("边宽按 log(1+通行次数) 缩放；节点大小按船舶数平方根缩放。",),
        risks=("该图使用节点直线连接作为拓扑示意，不表示真实航道中心线几何。",),
    )


def _plot_ship_dimensions(ship, source_manifest, source_hashes, palette):
    fig, ax = _fig("船舶尺度与总吨位")
    data = ship.dropna(subset=["length_m", "width_m", "gt"]).copy()
    types = data["ship_type"].value_counts().head(7).index
    data["类型"] = np.where(data["ship_type"].isin(types), data["ship_type"], "其他")
    labels = data["类型"].unique().tolist()
    color = {label: palette[i % len(palette)] for i, label in enumerate(labels)}
    for label in labels:
        subset = data[data["类型"].eq(label)]
        ax.scatter(subset["length_m"], subset["width_m"], s=16 + 50 * np.sqrt(subset["gt"].clip(lower=1) / data["gt"].max()),
                   color=color[label], alpha=.72, label=label, edgecolor="white", linewidth=.25)
    ax.set(xlabel="船长（m）", ylabel="船宽（m）")
    ax.legend(title="船舶类型", ncol=2, loc="upper left")
    ax.text(.99, .02, "点大小∝总吨位（GT）", transform=ax.transAxes, ha="right", va="bottom", fontsize=6)
    return fig, _contract(
        claim=f"{len(data):,} 艘船舶的长宽尺度与总吨位呈现类型分层和体量差异。",
        evidence=("length_m", "width_m", "gt", "ship_type"), source_manifest=source_manifest,
        source_hashes=source_hashes, units="长度：m；总吨位：GT",
        n_definition="one vessel in the static vessel profile table",
        statistic="vessel-level scatter; marker area encodes GT",
        transformations=("保留七个船舶数最多的类型，其余合并为‘其他’以保证图例可读。",),
        risks=("总吨位的大小编码用于比较，不代表线性视觉读数。",),
    )


def _plot_ship_correlation(ship, source_manifest, source_hashes):
    columns = ["length_m", "width_m", "height_m", "gt", "dwt", "draft_m", "mean_speed_kn", "range_km"]
    labels = ["船长", "船宽", "船高", "总吨位", "载重吨", "吃水", "平均航速", "航行范围"]
    data = ship[columns].apply(pd.to_numeric, errors="coerce")
    corr = data.corr(min_periods=20).to_numpy()
    fig, ax = _fig("船舶特征相关矩阵")
    image = ax.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(len(labels)), labels, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)), labels)
    for i in range(corr.shape[0]):
        for j in range(corr.shape[1]):
            if np.isfinite(corr[i, j]):
                ax.text(j, i, f"{corr[i, j]:.2f}", ha="center", va="center", fontsize=6.2,
                        color="white" if abs(corr[i, j]) > .55 else "#262626")
    cb = fig.colorbar(image, ax=ax, pad=0.02); cb.set_label("Pearson相关系数")
    return fig, _contract(
        claim="船舶静态尺度、载重、吃水和速度特征之间存在可量化的线性相关结构。",
        evidence=tuple(columns), source_manifest=source_manifest, source_hashes=source_hashes,
        units="原始字段单位：m、GT、节、km", n_definition="one vessel profile; pairwise complete observations",
        statistic="Pearson correlation coefficient", transformations=("对数值字段按船舶进行成对完整相关计算；不填补缺失。",),
        risks=("相关不表示因果；部分字段存在缺失且有效样本量可能因变量对而异。",),
    )


def _plot_hourly(trajectory, source_manifest, source_hashes):
    hourly = trajectory.set_index("time").resample("1h").agg(
        轨迹点数=("speed", "size"), 平均航速=("speed", "mean")
    )
    fig, axes = plt.subplots(2, 1, figsize=(150 / 25.4, 92 / 25.4), sharex=True, constrained_layout=True)
    axes[0].plot(hourly.index, hourly["轨迹点数"], color="#3C6E8F", lw=1.1)
    axes[0].fill_between(hourly.index, hourly["轨迹点数"].to_numpy(), color="#3C6E8F", alpha=.14)
    axes[0].set_ylabel("轨迹点数 / 小时")
    axes[0].set_title("AIS小时流量与平均航速")
    axes[1].plot(hourly.index, hourly["平均航速"], color="#D97745", lw=1.1)
    axes[1].set(xlabel="时间", ylabel="平均航速（节）")
    axes[1].tick_params(axis="x", rotation=25)
    return _finish(fig, "hourly_traffic_speed", "小时流量与平均航速", "时间序列与动态过程", {"rows": len(hourly)}), _contract(
        claim="清洗后的AIS记录在研究时间窗内呈现小时级记录量和平均航速变化。",
        evidence=("time", "speed", "hourly count", "hourly mean speed"), source_manifest=source_manifest,
        source_hashes=source_hashes, units="记录数：点/小时；速度：节",
        n_definition="one cleaned AIS record; aggregated into one-hour bins",
        statistic="hourly count and arithmetic mean speed",
        transformations=("按时间重采样到一小时；不插值缺失时段。",),
        risks=("记录量变化同时受AIS采样频率和船舶活动影响。",),
        design_brief=FigureDesignBrief(core_message="同时呈现观测覆盖量和速度过程，避免将采样量误读为流量。", canvas_ratio="custom", layout_recipe="workflow-to-result", hero_panel="小时轨迹点数", support_sequence=("小时平均航速",)),
    )


def _write_gallery(items):
    cards = []
    for item in items:
        cards.append(
            f'<article><h2>{item["name_zh"]}</h2><p>{item["key"]} · {item["category"]}</p>'
            f'<img src="{item["files"]["png"]}" loading="lazy"><p>'
            f'<a href="{item["files"]["pdf"]}">PDF</a> · '
            f'<a href="{item["files"]["svg"]}">SVG</a> · '
            f'<a href="{item["files"]["metadata"]}">元数据</a></p>'
            f'<p>程序审计：{"PASS" if item["audit"] else "FAIL"}；视觉复核：{item["visual_review"]}</p></article>'
        )
    html = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>真实数据图表预览</title>'
            '<style>body{font:14px/1.5 system-ui,"Microsoft YaHei",sans-serif;max-width:1450px;margin:auto;padding:24px;color:#262626}'
            'main{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}article{border:1px solid #ddd;padding:12px;background:#fff}'
            'article h2{font-size:18px;margin:0 0 4px}img{width:100%;height:300px;object-fit:contain;background:#fafafa}a{color:#315D78}'
            '@media(max-width:800px){main{grid-template-columns:1fr}}</style>'
            '<h1>数学建模真实数据图表预览</h1><p>数据来源：E:\\数据要素。图中使用真实AIS、航道网络和船舶属性数据；没有混入随机观测。每张图附有PDF、SVG、PNG和.figure.json。</p>'
            '<main>' + "".join(cards) + '</main></html>')
    (OUT_ROOT / "index.html").write_text(html, encoding="utf-8")


def _write_readme(report):
    lines = [
        "# 真实数据图表预览包",
        "",
        "本目录由 `scripts/build_real_data_preview.py` 生成，读取 `E:\\数据要素` 中的真实 AIS 轨迹、航道网络和船舶属性数据。原始数据只读，未混入随机观测。",
        "",
        f"- 轨迹记录：{report['data_summary']['trajectory_rows']:,}",
        f"- 船舶：{report['data_summary']['vessel_count']:,}",
        f"- 航道节点：{report['data_summary']['node_count']:,}",
        f"- 航道边：{report['data_summary']['edge_count']:,}",
        f"- 时间范围：{report['data_summary']['time_min']} 至 {report['data_summary']['time_max']}",
        "",
        "每张图均提供 450 DPI RGB PNG、可编辑 PDF/SVG 和 `.figure.json`。PNG 适合直接发送预览，PDF/SVG 适合后续排版。",
        "",
        "## 使用限制",
        "",
        "这些图是基于真实数据的描述性预览，不自动代表因果关系、显著性结论或最终论文主张。节点网络图用节点直线连接表示拓扑关系，不等同于真实航道中心线。",
        "",
        "## 重新生成",
        "",
        "```powershell",
        "python scripts/build_real_data_preview.py",
        "```",
    ]
    (OUT_ROOT / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build():
    source_manifest, source_hashes = _source_manifest()
    trajectory, edges, nodes, ship = _load_data()
    palette = get_modeling_palette("modeling-default")["categorical"]
    builders = [
        ("01_轨迹空间密度", "轨迹空间分布", _plot_trajectory_density),
        ("02_船舶平均航速分布", "单变量与分布", _plot_ship_speed),
        ("03_航段距离耗时频次", "关系与相关", _plot_edge_frequency),
        ("04_航段时段耗时", "单变量与分布", _plot_time_duration),
        ("05_航道节点加权网络", "网络、流量与空间关系", _plot_network),
        ("06_船舶尺度总吨位", "关系与相关", _plot_ship_dimensions),
        ("07_船舶特征相关矩阵", "热图与矩阵", _plot_ship_correlation),
        ("08_小时流量平均航速", "时间序列与动态过程", _plot_hourly),
    ]
    items, errors = [], []
    with mpl.rc_context(publication_rc_params(language="zh")):
        for stem, category, builder in builders:
            try:
                if builder is _plot_ship_speed:
                    fig, contract = builder(trajectory, ship, source_manifest, source_hashes, palette)
                elif builder is _plot_edge_frequency:
                    fig, contract = builder(edges, source_manifest, source_hashes, palette)
                elif builder is _plot_time_duration:
                    fig, contract = builder(edges, source_manifest, source_hashes, palette)
                elif builder is _plot_network:
                    fig, contract = builder(edges, nodes, source_manifest, source_hashes, palette)
                elif builder is _plot_ship_dimensions:
                    fig, contract = builder(ship, source_manifest, source_hashes, palette)
                elif builder is _plot_ship_correlation:
                    fig, contract = builder(ship, source_manifest, source_hashes)
                elif builder is _plot_hourly:
                    fig, contract = builder(trajectory, source_manifest, source_hashes)
                else:
                    fig, contract = builder(trajectory, source_manifest, source_hashes)
                # Most builders use the stem as the stable English-ish file key;
                # the metadata carries the Chinese semantic name.
                name_zh = stem.split("_", 1)[1]
                if not hasattr(fig, "_figure_metadata"):
                    _finish(fig, stem, name_zh, category, {})
                else:
                    fig._figure_metadata.update({"name_zh": name_zh, "category": category, "real_data": True})
                paths = export_publication_figure(fig, OUT_ROOT / stem, contract, strict=False, close=True)
                payload = json.loads(Path(paths["metadata"]).read_text(encoding="utf-8"))
                items.append({"key": stem, "name_zh": name_zh, "category": category,
                              "files": {key: Path(value).name for key, value in paths.items()},
                              "audit": payload["audit"]["passed"], "visual_review": payload["visual_review"]["status"]})
            except Exception as exc:  # keep the successful figures deliverable
                errors.append({"key": stem, "error": f"{type(exc).__name__}: {exc}"})
                plt.close("all")
    report = {"schema_version": 1, "data_root": str(DATA_ROOT), "figures": items, "errors": errors,
              "data_summary": {"trajectory_rows": int(len(trajectory)), "vessel_count": int(ship.ship_name.nunique()),
                               "edge_count": int(len(edges)), "node_count": int(len(nodes)),
                               "time_min": str(trajectory.time.min()), "time_max": str(trajectory.time.max())}}
    (OUT_ROOT / "preview_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_gallery(items)
    _write_readme(report)
    return report


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
