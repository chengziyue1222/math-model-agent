"""Render a broad random-data preview of the registered figure library.

This is an exploration bundle for visual selection.  It uses one fixed RNG
seed, several independent synthetic groups, and labels every artifact as a
random template preview.  It never overwrites the real-data delivery bundle.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from matplotlib import font_manager
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from algorithms.figures import DataContract, display_name, get_figure, get_spec, list_figures  # noqa: E402
from algorithms.sci_figures import FigureContract, export_publication_figure, publication_rc_params, resolve_cjk_font  # noqa: E402


OUT_ROOT = ROOT / "output" / "random-figure-previews"
SEED = 20261003


def _safe_stem(index: int, name: str) -> str:
    label = re.sub(r'[<>:"/\\|?*]', "_", display_name(name)).strip() or name
    return f"{index:03d}_{label}"


def _source_manifest():
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    script = Path(__file__).resolve()
    digest = hashlib.sha256(script.read_bytes()).hexdigest()
    payload = {
        "description": "Seeded random data for visual template selection; not observed research data.",
        "seed": SEED,
        "script": str(script),
        "script_sha256": digest,
        "warning": "所有图仅用于图型预览，不代表真实研究结果。",
    }
    path = OUT_ROOT / "random_source_manifest.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _contract(name: str, source: Path, *, specialized: bool):
    status = "学术风格实现" if specialized else "兼容适配器"
    return FigureContract(
        claim=f"{display_name(name)}的{status}随机数据模板预览。",
        evidence=("seeded random groups", "chart-specific visual encoding"),
        source_paths=(str(source),),
        target_venue="visual template preview",
        column="double",
        figure_role="data-overview",
        randomness=f"numpy.random.default_rng(seed={SEED})",
        n_definition="synthetic independent draws generated only for visual inspection",
        statistic="template-specific descriptive encoding",
        uncertainty="not estimated; synthetic preview only",
        review_risks=("随机数据不支持科学结论、效应量或显著性判断。",),
        data_transformations=("按图型需要生成多组随机变量；没有真实数据输入。",),
        theme_name="modeling-default",
        width_mm=150,
        height_mm=90,
        units="合成单位",
        plotting_code=(str(Path(__file__).resolve()),),
        claim_status="uncertain",
    )


def _contract_data(rng, *, n=72):
    values = rng.normal(0, 1, n)
    groups = [rng.normal(loc, 0.55 + i * 0.05, n) for i, loc in enumerate((-1.0, -0.25, 0.45, 1.1))]
    x = np.linspace(0, 1, n)
    trend = 0.65 * x + rng.normal(0, 0.14, n)
    matrix = rng.normal(0, 1, (8, 8))
    matrix = (matrix + matrix.T) / 2
    return {"values": values, "groups": groups, "x": x, "trend": trend, "matrix": matrix}


def _make(name: str, rng, contract):
    from algorithms.figures.examples import example_data
    data = example_data(name, seed=SEED)
    data['contract'] = contract
    return get_figure(name)(data=data, mode="preview")


def _contact_sheet(items, *, filename: str, cols: int = 4, card_size=(380, 285)):
    cards = []
    try:
        font_path = font_manager.findfont(resolve_cjk_font() or "DejaVu Sans", fallback_to_default=True)
        label_font = ImageFont.truetype(font_path, 15)
    except Exception:
        label_font = ImageFont.load_default()
    for item in items:
        path = OUT_ROOT / item["files"]["png"]
        image = Image.open(path).convert("RGB")
        image.thumbnail((card_size[0] - 16, card_size[1] - 38))
        card = Image.new("RGB", card_size, "white")
        card.paste(image, ((card_size[0] - image.width) // 2, 28 + (card_size[1] - 28 - image.height) // 2))
        ImageDraw.Draw(card).text((8, 7), item["name_zh"], fill="#111111", font=label_font)
        cards.append(card)
    if not cards:
        return
    rows = (len(cards) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * card_size[0], rows * card_size[1]), (238, 238, 238))
    for index, card in enumerate(cards):
        sheet.paste(card, ((index % cols) * card_size[0], (index // cols) * card_size[1]))
    sheet.save(OUT_ROOT / filename, dpi=(150, 150))


def _write_gallery(items):
    groups = {}
    for item in items:
        groups.setdefault(item["category"], []).append(item)
    sections = []
    for category, entries in groups.items():
        cards = []
        for item in entries:
            kind = item.get("implementation_level", "adapter")
            cards.append(f'<article><h2>{item["name_zh"]}</h2><p class="key">{item["name"]} · {kind}</p><img src="{item["files"]["png"]}" loading="lazy"><p><a href="{item["files"]["pdf"]}">PDF</a> · <a href="{item["files"]["svg"]}">SVG</a> · <a href="{item["files"]["metadata"]}">元数据</a></p><p>程序审计：{"PASS" if item["audit"] else "WARN"}；视觉复核：{item["visual_review"]}</p></article>')
        sections.append(f"<section><h2>{category}</h2><div class='grid'>{''.join(cards)}</div></section>")
    html = ('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>随机数据图表预览</title>'
            '<style>body{font:14px/1.5 system-ui,"Microsoft YaHei",sans-serif;max-width:1600px;margin:auto;padding:24px;color:#262626}section{margin:30px 0}section>h2{border-bottom:2px solid #315D78;padding:7px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}article{border:1px solid #ddd;background:#fff;padding:9px}article h2{font-size:17px;margin:0}.key{font-size:11px;color:#777;margin:2px 0 5px}img{width:100%;height:220px;object-fit:contain;background:#fafafa}a{color:#315D78}@media(max-width:1000px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:650px){.grid{grid-template-columns:1fr}}</style>'
            '<h1>数学建模图表库：随机数据成品预览</h1><p>固定随机种子，仅用于比较图型、版式和视觉编码。不要把这些图当作真实研究结果。154 个注册项统一采用学术风格实现。</p>'
            '<p><a href="../academic-style-showcase/index.html">打开精选学术风格成品（3×4 / 2×6）</a></p>' + ''.join(sections) + '</html>')
    (OUT_ROOT / "index.html").write_text(html, encoding="utf-8")


def _apply_cjk_font(fig):
    """Set a real CJK face on free-text artists such as NetworkX node labels."""
    font = resolve_cjk_font()
    if not font:
        return
    for artist in fig.findobj(mpl.text.Text):
        text = artist.get_text()
        if any("\u4e00" <= char <= "\u9fff" for char in text):
            artist.set_fontfamily(font)


def build():
    source = _source_manifest()
    rng = np.random.default_rng(SEED)
    items, errors = [], []
    specs = {name: get_spec(name) for name in list_figures()}
    specialized = {name for name, spec in specs.items() if spec.implementation_level == "dedicated"}
    with mpl.rc_context(publication_rc_params(language="zh")):
        for index, name in enumerate(list_figures(), start=1):
            stem = _safe_stem(index, name)
            try:
                contract_data = DataContract(source="synthetic", simulated=True, independent_unit="synthetic draw", units={"values": "合成单位"})
                fig = _make(name, rng, contract_data)
                if not hasattr(fig, "_figure_metadata"):
                    fig._figure_metadata = {}
                fig._figure_metadata.update({"name": name, "name_zh": display_name(name),
                                             "category": specs[name].category, "random_preview": True,
                                             "implementation_level": specs[name].implementation_level,
                                             "specialized_implementation": name in specialized, "seed": SEED})
                _apply_cjk_font(fig)
                if not any(ax.get_title() for ax in fig.axes):
                    fig.suptitle(display_name(name), fontsize=8)
                height = max(90, min(240, fig.get_size_inches()[1] * 25.4))
                fig.set_size_inches(150 / 25.4, height / 25.4)
                contract = _contract(name, source, specialized=name in specialized)
                from dataclasses import replace
                contract = replace(contract, height_mm=float(height))
                paths = export_publication_figure(fig, OUT_ROOT / stem, contract, strict=False, close=True)
                payload = json.loads(Path(paths["metadata"]).read_text(encoding="utf-8"))
                items.append({"name": name, "name_zh": display_name(name), "category": specs[name].category,
                              "implementation_level": specs[name].implementation_level, "status": specs[name].status,
                              "paper_suitable": specs[name].paper_suitable, "specialized": name in specialized,
                              "files": {k: Path(v).name for k, v in paths.items()},
                              "audit": payload["audit"]["passed"], "visual_review": payload["visual_review"]["status"]})
            except Exception as exc:
                errors.append({"name": name, "name_zh": display_name(name), "error": f"{type(exc).__name__}: {exc}"})
                plt.close("all")
    manifest = {"schema_version": 1, "seed": SEED, "synthetic_notice": "随机合成数据，仅用于图型预览，不代表真实研究结果。",
                "registered": len(specs), "rendered": len(items), "errors": errors, "figures": items}
    (OUT_ROOT / "preview_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_gallery(items)
    _contact_sheet(items, filename="contact_sheet.png")
    for category, entries in {c: [item for item in items if item["category"] == c] for c in sorted({item["category"] for item in items})}.items():
        safe = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", category)
        _contact_sheet(entries, filename=f"category_{safe}.png", cols=3, card_size=(440, 300))
    return manifest


if __name__ == "__main__":
    print(json.dumps(build(), ensure_ascii=False, indent=2))
