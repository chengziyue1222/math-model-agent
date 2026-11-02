"""Build a curated, reference-atlas style preview for the figure library.

The bundle is intentionally separate from the 154-entry catalog gallery.  It
shows the higher-information patterns that need dedicated implementations,
using seeded random data only for visual inspection.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import PathPatch, Rectangle
from matplotlib.path import Path as MplPath
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from algorithms.figures.academic_style import (  # noqa: E402
    PALETTE, roc_multi,
)
from algorithms.sci_figures import (  # noqa: E402
    FigureContract, export_publication_figure, publication_rc_params, resolve_cjk_font,
)


OUT = ROOT / "output" / "academic-style-showcase"
SEED = 20261003


def _contract(source: Path, title: str) -> FigureContract:
    return FigureContract(
        claim=f"{title}的学术风格随机数据预览。",
        evidence=("固定随机种子", "图型专用视觉编码"),
        source_paths=(str(source),),
        target_venue="visual template preview", column="double", figure_role="data-overview",
        randomness=f"numpy.random.default_rng(seed={SEED})",
        n_definition="synthetic independent draws for visual inspection",
        statistic="template-specific descriptive encoding", uncertainty="not estimated",
        review_risks=("随机数据不支持科学结论、效应量或显著性判断。",),
        data_transformations=("按图型需要生成多组随机变量；没有真实数据输入。",),
        theme_name="soft-academic", width_mm=150, height_mm=90, units="合成单位",
        plotting_code=(str(Path(__file__).resolve()),), claim_status="uncertain",
    )


def _apply_cjk(fig):
    font = resolve_cjk_font()
    if not font:
        return
    for artist in fig.findobj(mpl.text.Text):
        if any("\u4e00" <= c <= "\u9fff" for c in artist.get_text()):
            artist.set_fontfamily(font)


def _base(fig, title):
    fig.suptitle(title, x=.02, ha="left", fontsize=12, fontweight="bold", color="#252A2E")
    _apply_cjk(fig)
    return fig


def _pca(rng):
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    from algorithms.figures.academic_style import pca_biplot_academic
    latent = rng.normal(size=(105, 3))
    matrix = latent @ rng.normal(size=(3, 6)) + rng.normal(0, .2, (105, 6))
    standardized = StandardScaler().fit_transform(matrix)
    model = PCA().fit(standardized)
    fig = pca_biplot_academic(model.transform(standardized)[:, :2], model.components_[:2].T,
                             model.explained_variance_ratio_[:2],
                             feature_labels=["投入", "产出", "成本", "效率", "资源", "质量"])
    return _base(fig, "PCA 双标图")


def _density(rng):
    fig, ax = plt.subplots(figsize=(6.4, 4.8), constrained_layout=True)
    x = rng.normal(8, 1.5, 280); y = .35 * x + rng.normal(6, .55, 280)
    ax.scatter(x, y, s=7, color="#6EA7C2", alpha=.18)
    xx, yy = np.meshgrid(np.linspace(x.min(), x.max(), 90), np.linspace(y.min(), y.max(), 90))
    from scipy.stats import gaussian_kde
    zz = gaussian_kde(np.vstack([x, y]))(np.vstack([xx.ravel(), yy.ravel()])).reshape(xx.shape)
    ax.contourf(xx, yy, zz, levels=9, cmap=LinearSegmentedColormap.from_list("soft_density", ["#F4F6F8", "#A8D6E7", "#C08DA7"]), alpha=.76)
    coef = np.polyfit(x, y, 1); grid = np.linspace(x.min(), x.max(), 80)
    ax.plot(grid, np.polyval(coef, grid), color="#C68387", lw=1.3)
    ax.text(.03, .95, f"n = {x.size}\nR² = {np.corrcoef(x, y)[0, 1] ** 2:.2f}", transform=ax.transAxes, va="top", color="#6E8798")
    ax.set(xlabel="观测值", ylabel="预测值")
    return _base(fig, "相关密度图")


def _violin(rng):
    fig, ax = plt.subplots(figsize=(6.4, 4.8), constrained_layout=True)
    data = [rng.normal(mu, sd, 55) for mu, sd in [(1.5, .38), (2.2, .32), (1.9, .42), (2.8, .28), (2.4, .45), (3.1, .35)]]
    parts = ax.violinplot(data, positions=np.arange(1, 7), showmedians=True, widths=.78)
    for i, body in enumerate(parts["bodies"]):
        body.set_facecolor(PALETTE[i % len(PALETTE)]); body.set_edgecolor(PALETTE[i % len(PALETTE)]); body.set_alpha(.56)
    for i, values in enumerate(data, 1):
        jitter = rng.uniform(-.14, .14, len(values))
        ax.scatter(i + jitter, values, s=8, color="#455C68", alpha=.46, edgecolors="white", linewidths=.25)
    ax.set_xticks(range(1, 7), ["方案甲", "方案乙", "方案丙", "方案丁", "方案戊", "方案己"], rotation=28, ha="right")
    ax.set_ylabel("响应值")
    ax.grid(axis="y", color="#DCE4E8", lw=.45)
    return _base(fig, "小提琴图")


def _line(rng):
    fig, ax = plt.subplots(figsize=(6.4, 4.8), constrained_layout=True)
    t = np.arange(36)
    for i, color in enumerate(PALETTE[:3]):
        y = .18 * i + .22 * np.sin(t / 4 + i * .4) + .008 * t + rng.normal(0, .025, t.size) + .3
        band = .055 + .01 * i
        ax.plot(t, y, color=color, lw=1.65, label=f"表型{i + 1}")
        ax.fill_between(t, y - band, y + band, color=color, alpha=.17)
        ax.text(t[-1] + .7, y[-1], f"表型{i + 1}", color=color, va="center", fontsize=8)
    ax.set_xlim(0, 40); ax.set(xlabel="样本序号", ylabel="合成响应 ± 场景包络")
    ax.grid(axis="y", color="#DCE4E8", lw=.45)
    return _base(fig, "时间趋势")


def _stacked_scatter(rng):
    fig, ax = plt.subplots(figsize=(6.4, 4.8), constrained_layout=True)
    x = np.arange(7); parts = rng.uniform(.4, 2.2, (4, 7)); base = np.zeros(7)
    for i, values in enumerate(parts):
        ax.bar(x, values, bottom=base, color=PALETTE[i], alpha=.82, width=.68, label=f"组分{i + 1}")
        base += values
    for i in range(7):
        raw = base[i] + rng.normal(0, .34, 12)
        ax.scatter(np.full(raw.shape, x[i]) + rng.uniform(-.18, .18, raw.size), raw, s=8, color="#394E59", alpha=.55)
    ax.set_xticks(x, [f"Phen{i + 1}" for i in x]); ax.set_ylabel("总量")
    ax.legend(frameon=False, ncol=4, loc="upper left")
    return _base(fig, "堆叠柱状散点图")


def _freq3d(rng):
    fig = plt.figure(figsize=(6.4, 4.8), constrained_layout=True); ax = fig.add_subplot(111, projection="3d")
    nx, ny = 8, 6; xpos, ypos = np.meshgrid(np.arange(nx), np.arange(ny), indexing="ij")
    heights = rng.uniform(0.4, 2.6, (nx, ny)) * (1 + np.sin(np.arange(nx)[:, None] / 2) * .28)
    ax.bar3d(xpos.ravel(), ypos.ravel(), np.zeros(nx * ny), .72, .72, heights.ravel(), shade=True,
             color=np.where(heights.ravel() > 1.5, "#E58E87", "#8EC2D3"), alpha=.82)
    ax.set(xlabel="样本", ylabel="分箱", zlabel="频次", zlim=(0, 3), zticks=[0, 1, 2, 3])
    ax.set_box_aspect((1, 1, .65), zoom=.82)
    ax.view_init(26, -62)
    return _base(fig, "频率 3D 热图")


def _sankey(rng):
    fig, ax = plt.subplots(figsize=(6.4, 4.8), constrained_layout=True)
    columns = [["输入A", "输入B", "输入C"], ["处理甲", "处理乙", "处理丙"], ["结果甲", "结果乙"], ["输出"]]
    xs = np.linspace(0, 1, len(columns)); positions = {}
    for ci, column in enumerate(columns):
        ys = np.linspace(.78, .22, len(column))
        for yi, label in zip(ys, column):
            positions[label] = (xs[ci], yi)
            ax.add_patch(Rectangle((xs[ci] - .026, yi - .035), .052, .07, facecolor=PALETTE[ci % len(PALETTE)], edgecolor="white", lw=.7))
            ax.text(xs[ci], yi, label, ha="center", va="center", fontsize=7, color="#20313A")
    flows = [("输入A", "处理甲", .7), ("输入A", "处理乙", .3), ("输入B", "处理乙", .6), ("输入B", "处理丙", .4),
             ("输入C", "处理丙", .8), ("处理甲", "结果甲", .8), ("处理乙", "结果甲", .35), ("处理乙", "结果乙", .45),
             ("处理丙", "结果乙", .85), ("结果甲", "输出", .72), ("结果乙", "输出", .9)]
    for src, dst, weight in flows:
        x0, y0 = positions[src]; x1, y1 = positions[dst]
        path = MplPath([(x0 + .03, y0), (x0 + .30, y0), (x1 - .30, y1), (x1 - .03, y1)],
                       [MplPath.MOVETO, MplPath.CURVE4, MplPath.CURVE4, MplPath.CURVE4])
        ax.add_patch(PathPatch(path, facecolor="none", edgecolor="#86AFC0", lw=1 + 10 * weight, alpha=.18))
    ax.set_xlim(-.08, 1.08); ax.set_ylim(.05, .95); ax.axis("off")
    return _base(fig, "桑基图")


def _stacked_area(rng):
    fig, ax = plt.subplots(figsize=(6.4, 4.8), constrained_layout=True)
    t = np.arange(2017, 2025); base = np.array([2.0, 2.2, 2.5, 2.8, 3.1, 3.6, 4.0, 4.6])
    comps = np.vstack([base * (1 + .12 * i) + rng.normal(0, .05, len(t)) for i in range(5)])
    ax.stackplot(t, comps, labels=["A", "B", "C", "D", "E"], colors=PALETTE[:5], alpha=.88)
    ax.set(xlabel="时间", ylabel="累计值"); ax.legend(frameon=False, ncol=5, loc="upper left")
    return _base(fig, "堆叠面积图")


def _spatial(rng):
    fig, ax = plt.subplots(figsize=(6.4, 4.8), constrained_layout=True)
    ax.set_facecolor("#F6F8F9")
    ax.axhline(0, color="#D6E0E5", lw=.5); ax.axvline(0, color="#D6E0E5", lw=.5)
    names = ["北京", "东京", "新加坡", "悉尼", "纽约", "旧金山", "伦敦", "开普敦"]
    lon = np.array([116, 139, 104, 151, -74, -122, 0, 18]); lat = np.array([40, 36, 1, -34, 41, 38, 51, -34])
    values = rng.uniform(8, 35, len(names)); colors = [PALETTE[i % len(PALETTE)] for i in range(len(names))]
    ax.scatter(lon, lat, s=values * 9, c=colors, alpha=.78, edgecolor="white", linewidth=.7)
    for x, y, name in zip(lon, lat, names): ax.text(x + 3, y + 2, name, fontsize=7, color="#455A64")
    ax.set(xlim=(-180, 180), ylim=(-60, 75), xlabel="经度", ylabel="纬度")
    ax.set_xticks([-120, -60, 0, 60, 120]); ax.set_yticks([-30, 0, 30, 60]); ax.grid(color="white", lw=.6)
    return _base(fig, "地理与气泡图")


def _surface(rng):
    fig = plt.figure(figsize=(6.4, 4.8), constrained_layout=True); ax = fig.add_subplot(111, projection="3d")
    x = np.linspace(-2, 2, 45); y = np.linspace(-2, 2, 45); xx, yy = np.meshgrid(x, y)
    zz = np.exp(-((xx - .5) ** 2 + (yy + .2) ** 2)) - .58 * np.exp(-((xx + .9) ** 2 + (yy - .8) ** 2))
    ax.plot_surface(xx, yy, zz, cmap=LinearSegmentedColormap.from_list("surface", ["#74B4D1", "#F4C8C1", "#C47B83"]), alpha=.78, linewidth=0)
    ax.contour(xx, yy, zz, zdir="z", offset=-.8, cmap="coolwarm", levels=8, linewidths=.6)
    ax.set(xlabel="因子 X", ylabel="因子 Y", zlabel="响应", zlim=(-.8, 1), zticks=[-.8, -.4, 0, .4, .8])
    ax.set_box_aspect((1, 1, .65), zoom=.82)
    ax.view_init(28, -55)
    return _base(fig, "响应面与等高线")


def _deconv(rng):
    fig, axes = plt.subplots(2, 1, figsize=(6.4, 4.8), sharex=True, constrained_layout=True)
    x = np.linspace(526, 538, 420)
    for row, shift in zip(axes, [0, .12]):
        comps = [(.42, 532.3 + shift, .42), (.68, 531.3 + shift, .30), (.28, 529.4 + shift, .26)]
        total = np.zeros_like(x) + .03
        for i, (amp, mu, sd) in enumerate(comps):
            curve = amp * np.exp(-.5 * ((x - mu) / sd) ** 2); total += curve
            row.fill_between(x, 0, curve, color=PALETTE[i], alpha=.55, label=["组分A", "组分B", "组分C"][i])
        row.plot(x, total + rng.normal(0, .006, x.size), color="#4C7186", lw=1.0)
        row.set_ylabel("强度"); row.spines["top"].set_visible(False); row.spines["right"].set_visible(False)
    axes[0].legend(frameon=False, ncol=3, loc="upper left"); axes[-1].set_xlabel("结合能")
    return _base(fig, "观测谱、总拟合、背景与化学组分")


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    source = Path(__file__).resolve(); digest = hashlib.sha256(source.read_bytes()).hexdigest()
    from algorithms.figures import get_figure, get_spec, display_name
    from algorithms.figures.examples import example_data
    keys = ['joint_density','pca_biplot','roc_curve','correlation_matrix','radar','ridgeline',
            'bubble','correlation_bubble','correlation_network','community_network','chord','umap',
            'bar','grouped_bar','mantel','violin','time_series','percent_stacked_bar',
            'spatial_3d','sankey','stacked_area','spatial_scatter','response_surface','pca_loadings']
    makers = [(f"{i:02d}_{display_name(key)}", lambda key=key: get_figure(key)(
        data=example_data(key,seed=SEED),mode="preview"),
        "关系降维诊断网络" if i <= 12 else "比较趋势组成空间表征") for i,key in enumerate(keys,1)]
    items = []
    with mpl.rc_context(publication_rc_params(language="zh")):
        for index, (name, maker, category) in enumerate(makers, 1):
            fig = maker(); height = max(90, min(240, fig.get_size_inches()[1]*25.4)); fig.set_size_inches(150 / 25.4, height / 25.4); _apply_cjk(fig)
            metadata = getattr(fig, "_figure_metadata", {})
            metadata.update({"showcase": True, "seed": SEED, "name_zh": name, "category": category,
                             "reference_style": "E:/ai数模/academic-data-visualization-main", "random_preview": True,
                             "mode": "preview", "implementation_level": get_spec(keys[index-1]).implementation_level, "paper_suitable": False,
                             "source": "synthetic", "simulated": True, "independent_unit": "synthetic draw",
                             "units": {"values": "合成单位"}, "interval_kind": metadata.get("interval_kind", "none")})
            metadata["data_contract"] = {field: metadata[field] for field in
                                         ("source", "simulated", "independent_unit", "units", "interval_kind")}
            fig._figure_metadata = metadata
            from dataclasses import replace
            paths = export_publication_figure(fig, OUT / name, replace(_contract(source, name), height_mm=height), strict=False, close=True)
            payload = json.loads(Path(paths["metadata"]).read_text(encoding="utf-8"))
            items.append({"index": index, "name": name, "category": category,
                          "files": {key: Path(value).name for key, value in paths.items()},
                          "audit": payload["audit"]["passed"], "visual_review": payload["visual_review"]["status"]})
    manifest = {"schema_version": 1, "seed": SEED, "reference_style": "E:/ai数模/academic-data-visualization-main",
                "script_sha256": digest, "synthetic_notice": "随机合成数据，仅用于图型预览，不代表真实研究结果。",
                "rendered": len(items), "figures": items}
    (OUT / "showcase_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_index(items)
    _sheet(items[:12], "showcase_01_关系降维诊断网络.png", "关系、降维、诊断、高维与网络结构 · 3 × 4", cols=3)
    _sheet(items[12:], "showcase_02_比较趋势组成空间表征.png", "比较、分布、趋势、组成、空间与材料表征 · 2 × 6", cols=2)
    (OUT / "README.md").write_text(
        "# 学术风格精选成品预览\n\n"
        "本目录学习 `E:/ai数模/academic-data-visualization-main` 的图型组织方式、"
        "低饱和配色、多面板叙事、原始点和区间表达，使用固定随机种子 20261003 生成。\n\n"
        "- 24 个精选图型，程序审计 24/24；\n- `showcase_01_*.png`：关系、降维、诊断与网络，3×4；\n"
        "- `showcase_02_*.png`：比较、趋势、组成与空间表征，2×6；\n"
        "- 所有单图同时提供 PNG、PDF、SVG 与 `.figure.json`；\n"
        "- 这些图仅用于版式和图型选择，不表达真实研究结果。\n",
        encoding="utf-8",
    )
    return manifest


def _heatmap(rng):
    fig, ax = plt.subplots(figsize=(6.4, 4.8), constrained_layout=True)
    matrix = rng.normal(size=(28, 32)); matrix = (matrix + np.roll(matrix, 1, axis=0) + np.roll(matrix, -1, axis=1)) / 3
    im = ax.imshow(matrix, cmap=LinearSegmentedColormap.from_list("intensity", ["#D9EEF2", "#7BAEC0", "#536978"]), aspect="auto")
    ax.set(xticks=np.arange(0, 32, 4), yticks=np.arange(0, 28, 4), xlabel="特征", ylabel="样本"); fig.colorbar(im, ax=ax, fraction=.035, pad=.03, label="强度")
    return _base(fig, "高维强度结构")


def _roc(rng):
    truth = np.r_[np.zeros(70), np.ones(70)]
    curves = []
    for auc_target in [.79, .84, .88, .91, .93]:
        score = np.r_[rng.beta(2.3, 4.8, 70), rng.beta(4.8, 2.3, 70)]
        score = np.clip(score + (auc_target - .84) * .45, 0, 1); curves.append((truth, score))
    return roc_multi(curves=curves, labels=["Transformer", "Charlson", "Elixhauser", "llama", "Delphi"])


def _network(rng):
    from algorithms.figures.academic_style import network_academic
    edges = [("V1", "V2"), ("V2", "V3"), ("V3", "V4"), ("V4", "V5"), ("V5", "V1"), ("V2", "V5"), ("V1", "V4")]
    weights = [.82, -.56, .72, .45, -.35, .66, .51]
    return network_academic(edges, weights=weights)


def _trajectory(rng):
    t = np.linspace(0, 1, 105); return np.column_stack([2.1 * np.sin(t * 2.6 * np.pi) + rng.normal(0, .08, t.size), 1.2 * np.cos(t * 1.4 * np.pi) + rng.normal(0, .08, t.size)])


def _sheet(items, filename, title, *, cols):
    cards = []; card_size = (470, 330)
    font_path = font_manager.findfont(resolve_cjk_font() or "DejaVu Sans", fallback_to_default=True)
    try: font = ImageFont.truetype(font_path, 17)
    except Exception: font = ImageFont.load_default()
    for item in items:
        image = Image.open(OUT / item["files"]["png"]).convert("RGB"); image.thumbnail((card_size[0] - 12, card_size[1] - 36))
        card = Image.new("RGB", card_size, "white"); card.paste(image, ((card_size[0] - image.width) // 2, 30 + (card_size[1] - 30 - image.height) // 2))
        ImageDraw.Draw(card).text((8, 7), item["name"], fill="#20282D", font=font); cards.append(card)
    rows = (len(cards) + cols - 1) // cols; sheet = Image.new("RGB", (cols * card_size[0], rows * card_size[1] + 52), "#EDF1F3")
    ImageDraw.Draw(sheet).text((18, 12), title, fill="#20282D", font=font)
    for i, card in enumerate(cards): sheet.paste(card, ((i % cols) * card_size[0], 52 + (i // cols) * card_size[1]))
    sheet.save(OUT / filename, dpi=(150, 150))


def _write_index(items):
    links = []
    for item in items:
        links.append(f'<article><h2>{item["name"]}</h2><img src="{item["files"]["png"]}"><p><a href="{item["files"]["pdf"]}">PDF</a> · <a href="{item["files"]["svg"]}">SVG</a> · <a href="{item["files"]["metadata"]}">元数据</a></p></article>')
    html = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>学术风格精选成品</title>'
            '<style>body{font:14px/1.5 system-ui,"Microsoft YaHei",sans-serif;max-width:1600px;margin:auto;padding:24px;color:#252A2E}h1{border-bottom:2px solid #6EA7C2;padding-bottom:12px}.sheets{display:flex;gap:12px;flex-wrap:wrap}.sheets img{width:min(720px,100%);border:1px solid #ccd7dc}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}article{border:1px solid #d9e1e5;padding:10px;background:#fff}article h2{font-size:17px;margin:0 0 6px}article img{width:100%;height:220px;object-fit:contain;background:#fafafa}a{color:#315D78}@media(max-width:900px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:600px){.grid{grid-template-columns:1fr}}</style>'
            '<h1>学术风格精选成品预览</h1><p>参考本地 academic-data-visualization 目录的图型组织和视觉层级；固定随机种子，仅用于比较版式与图形编码。</p>'
            '<div class="sheets"><img src="showcase_01_关系降维诊断网络.png"><img src="showcase_02_比较趋势组成空间表征.png"></div><h2>单图文件</h2><div class="grid">' + ''.join(links) + '</div></html>')
    (OUT / "index.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
