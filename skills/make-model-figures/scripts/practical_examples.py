"""Render saved synthetic practical-chart inputs as publication bundles.

Requires the installed math-model-agent wheel. Does not invent real results.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

from algorithms.figures import get_figure
from algorithms.figures.base import metadata_value
from algorithms.figures.practical import FIELDS
from algorithms.figures.practical_examples import example
from algorithms.sci_figures import FigureContract, export_publication_figure, resolve_cjk_font


def cases():
    result = {name: (name, example(name)) for name in FIELDS}
    result["polar_angular"] = ("polar_stacked_bar", {**example("polar_stacked_bar"), "orientation": "angular"})
    result["polar_percent"] = ("polar_stacked_bar", {**example("polar_stacked_bar"), "percent": True})
    result["person_silhouette"] = ("pictogram", {**example("pictogram"), "pictogram_mode": "silhouette"})
    result["person_waffle"] = ("pictogram", {"categories": ["支持", "保留", "质疑", "未明确"], "values": [18, 12, 1, 9], "icon_value": 1, "array_layout": "waffle", "group_colors": ["#087E8B", "#D49A2A", "#C45B45", "#A3ABB5"], "simulated": True, "source": "synthetic count example; not the original interviews"})
    result["calendar_vertical"] = ("calendar_heatmap", {**example("calendar_heatmap"), "layout": "vertical"})
    result["calendar_pie"] = ("calendar_glyphs", {**example("calendar_glyphs"), "glyph": "pie", "groups": ["A", "B", "C"], "values": [[0, 0, 0], [1, 1, 0], [3, 1, 2], [1, 1, 2], [2, 4, 2]]})
    return result


def main(output):
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    index = []
    for case, (key, data) in cases().items():
        source = output / f"{case}.data.json"
        source.write_text(json.dumps(metadata_value(data), ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        saved = json.loads(source.read_text(encoding="utf-8"))
        fig = get_figure(key)(data=saved, mode="preview")
        fig.suptitle("模拟数据 · " + case, fontsize=9, fontfamily=resolve_cjk_font() or "DejaVu Sans")
        width = 150
        height = 140 if case == "calendar_vertical" else 80 if "calendar" in case else 110 if key in {"sparkline_matrix", "matrix_pie", "polar_stacked_bar"} else 90
        fig.set_size_inches(width/25.4, height/25.4)
        contract = FigureContract(
            "模拟预览：检查输入编码与布局，未建立真实建模结论", tuple(FIELDS[key]),
            source_paths=(str(source),), plotting_code=(str(Path(__file__).resolve()),),
            width_mm=width, height_mm=height, claim_status="question", question="图型字段与数值映射是否正确？",
            units="见输入字段及轴标注", randomness="固定演示数组，无随机抽样", n_definition="全部保存的模拟输入",
            statistic="直接绘制保存值", uncertainty="无输入区间，不生成区间", model_name="explicit synthetic demonstration",
            scenario="simulated preview", data_transformations=(str(fig._figure_metadata.get("encoding", "按字段绘制")),),
        )
        paths = export_publication_figure(fig, output / case, contract, close=True)
        index.append({"case": case, "key": key, "source": source.name, "outputs": paths, "simulated": True})
    (output / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(index)} reproducible synthetic bundles to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("practical-figures"))
    main(parser.parse_args().output)
