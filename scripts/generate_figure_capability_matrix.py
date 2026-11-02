"""Generate the figure capability matrix from the runtime registry."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

from algorithms.figures import get_spec, list_figures


def _cell(value):
    if value is None:
        return "—"
    if isinstance(value, (list, tuple)):
        return ", ".join(f"`{item}`" for item in value) or "—"
    return str(value).replace("|", r"\|")


def generate(output: Path) -> Path:
    names = list_figures()
    levels = {}
    for name in names:
        spec = get_spec(name)
        levels[spec.implementation_level] = levels.get(spec.implementation_level, 0) + 1
    lines = [
        "# 图表库能力矩阵（由 registry 自动生成）", "",
        "> 本文件由 `scripts/generate_figure_capability_matrix.py` 生成。请修改注册表后重新生成，不要手工维护表格。",
        "", f"注册项总数：**{len(names)}**。",
        f"注册为专用的入口（独立语义仍须终审）：**{levels.get('dedicated', 0)}**；别名不计入。",
        f"仅要求 values 的注册项：**{sum(get_spec(n).required_fields == ('values',) for n in names)}**。",
        f"paper_suitable=True：**{sum(get_spec(n).paper_suitable for n in names)}**。",
        "", "## 实现等级统计", "",
        "| implementation_level | 数量 | 含义 |", "|---|---:|---|",
        f"| dedicated | {levels.get('dedicated', 0)} | 专用图形语义与校验实现 |",
        f"| adapter | {levels.get('adapter', 0)} | 学术视觉适配器，需核对输入语义 |",
        f"| alias | {levels.get('alias', 0)} | 兼容别名，不计为独立图型 |",
        f"| template | {levels.get('template', 0)} | 版式或流程预览模板 |",
        "", "## 完整目录", "",
        "| English key | 中文名称 | category | implementation_level | status | required_fields | paper_suitable | qa_status | alias_of | 允许真实论文使用 |",
        "|---|---|---|---|---|---|---:|---|---|---|",
    ]
    for name in names:
        spec = get_spec(name)
        allowed = "是" if spec.paper_suitable else (
            "否（仅版式预览；尚无正式统计入口）" if spec.implementation_level in {"adapter", "template"}
            and name not in {"cross_validation", "model_interval"} else "否（需完成数据和视觉复核）")
        lines.append("| " + " | ".join([
            f"`{spec.name}`", spec.name_zh, spec.category,
            f"`{spec.implementation_level}`", spec.status,
            _cell(spec.required_fields), str(spec.paper_suitable).lower(),
            spec.qa_status, _cell(spec.to_dict().get("alias_of")), allowed,
        ]) + " |")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/figure-library-capability-matrix.md")
    args = parser.parse_args()
    print(generate(args.output))
