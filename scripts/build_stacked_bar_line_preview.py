"""Build an illustrative percentage-stack and quantity-line chart (not research data)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from algorithms.figures import DataContract, get_figure  # noqa: E402
from algorithms.sci_figures import FigureContract, export_publication_figure  # noqa: E402


def build(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    # Schematic shares and reference-style quantities demonstrate the layout;
    # these are not recovered observations from the user's screenshot.
    data = {
        "categories": ["主题1", "主题2", "主题3", "主题4", "主题5"],
        "values": [[4, 69, 27], [3, 33, 64], [6, 44, 50], [57, 22, 21], [90, 4, 6]],
        "groups": ["中性", "消极", "积极"],
        "line_values": [2817, 3202, 368, 1009, 604],
    }
    source = output / "示例数据.json"
    source.write_text(json.dumps({"simulated": True, "description": "仅用于演示图型，非真实研究数据",
                                  **data}, ensure_ascii=False, indent=2), encoding="utf-8")
    fig = get_figure("percent_stacked_bar_line")(
        data=data, mode="preview", title="不同主题的情感倾向占比（示例）",
        xlabel="主题", ylabel="情感倾向占比 (%)", right_ylabel="文本数量 (条)",
        line_label="文本数量", contract=DataContract(
            source=str(source.resolve()), simulated=True, independent_unit="示例主题",
            units={"values": "比例权重", "line_values": "条"},
        ),
    )
    fig.set_size_inches(150 / 25.4, 100 / 25.4)
    export_contract = FigureContract(
        claim="检查不同主题的情感占比和文本数量能否在同一图中清楚阅读",
        claim_status="question", figure_role="data-overview",
        evidence=("100% 堆叠柱", "右轴文本数量折线及数值标注"),
        source_paths=(str(source.resolve()),), plotting_code=(str(Path(__file__).resolve()),),
        units="占比：%；文本数量：条", n_definition="5 个示例主题，非真实抽样",
        statistic="逐主题归一化占比及独立给定的文本数量", uncertainty="演示数据，无推断区间",
        data_transformations=("每行组成值归一化到 100%；数量折线不变",),
        review_risks=("两个纵轴代表不同单位，交点不表示数值相等或统计关联",),
        randomness="固定示意数据，无随机抽样", theme_name="custom:reference-stack-line",
        width_mm=150, height_mm=100,
    )
    return export_publication_figure(fig, output / "百分比堆叠柱折线图", export_contract, close=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/stacked-bar-line-preview")
    print(json.dumps(build(parser.parse_args().output), ensure_ascii=False, indent=2))
