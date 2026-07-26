"""Generate a traceable CUMCM-layout draft from registered results.

The script deliberately produces a *draft* when evidence coverage is incomplete.  Its
layout, however, is deterministic and is checked by validate_cumcm_layout.py.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


TITLE = "C题：生产企业原材料的订购与运输方案"
CONTEST = "数学建模竞赛"
DATE = "2026年7月"


def tex_escape(value: object) -> str:
    return str(value).replace("_", r"\_").replace("%", r"\%")


def main(root: Path) -> None:
    result = json.loads((root / "results" / "result_object.json").read_text(encoding="utf-8"))
    paper = root / "paper"
    paper.mkdir(exist_ok=True)
    ids = result["solution"]["top50_supplier_ids"]
    metrics = result["metrics"]
    constraints = result["constraints"]
    figures = json.loads((paper / "figure-registry.json").read_text(encoding="utf-8"))
    if len(ids) != 50:
        raise ValueError(f"expected 50 registered supplier ids, got {len(ids)}")

    supplier_count = int(result["solution"]["supplier_count"])
    demand = float(constraints["demand_product_equiv"])
    required = float(metrics["required_product_equiv"])
    capacity = float(metrics["maximum_planning_capacity"])
    loss = float(metrics["average_nonzero_loss"])
    claim = "CLAIM_TOP50"

    markdown = [
        "# 2021C 供应链建模回归报告", "", "## 摘要", "",
        "基于官方原始附件，本文建立供应商一致性排序、规划容量选集和 24 周滚动订货的分解式模型。",
        f"已登记的 Top-50 供应商名单含 {len(ids)} 个编号：[claim:{claim}]。",
        "规划容量采用正供货量的 75% 分位数，不等同于最坏情形鲁棒保证。", "",
        "## 复现说明", "", "全部数值来源于已登记的结果对象、图表与原始附件。",
    ]
    (paper / "main.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")

    template = (root / "template" / "cume-template.tex").read_text(encoding="utf-8")
    if "\\begin{document}" not in template:
        raise ValueError("CUMCM template has no document boundary")
    header = template.split("\\begin{document}", 1)[0]
    top50_rows = "\n".join(
        f"{index} & {tex_escape(supplier)} \\\\" for index, supplier in enumerate(ids, start=1)
    )

    tex = rf"""{header}\begin{{document}}
% Strict layout lifecycle: cover -> abstract/keywords -> body page 1.
\thispagestyle{{empty}}\pagenumbering{{gobble}}
\vspace*{{7cm}}
\begin{{center}}
{{\fontsize{{22pt}}{{33pt}}\selectfont\bfseries {TITLE}\par}}

\vspace{{2cm}}
{{\fontsize{{14pt}}{{21pt}}\selectfont {CONTEST}\par}}

\vspace{{1cm}}
{{\normalsize {DATE}\par}}
\end{{center}}
\newpage

\thispagestyle{{empty}}
\begin{{center}}
{{\fontsize{{14pt}}{{21pt}}\selectfont\bfseries 摘\quad 要}}
\end{{center}}\vspace{{0.6cm}}
针对生产企业原材料订购与运输的决策问题，本文基于官方原始附件构建供应商一致性排序、规划容量最小选集与24周滚动订货模型。对供货历史中的正供货量取75\%分位数作为规划容量，并在满足需求等价量的约束下选择供应商集合。求解结果表明，模型状态为{tex_escape(result['status'])}，规划集合包含{supplier_count}家供应商；需求等价量为{demand:.2f}，含损耗后的覆盖要求为{required:.2f}，规划容量上界为{capacity:.2f}。本文明确披露：该求解链是“排序—容量选集—滚动分配”的分解式流程，而非一体化最坏情形鲁棒优化。所有结论均链接至登记的结果对象和图表；在需求预测、供应商切换成本或合同约束变化时，应重新求解。

\noindent{{\bfseries 关键词：}}供应商排序；容量规划；整数规划；滚动订货；可追溯建模
\newpage

\pagestyle{{plain}}\pagenumbering{{arabic}}\setcounter{{page}}{{1}}
\section{{问题重述}}
原始附件给出402家供应商和8家转运商的历史记录。任务是以可审计方式完成供应商评价、订货与运输方案、原料组合及产能边界分析。本文只报告经注册结果对象支持的指标，单位为立方米。

\section{{模型总体框架}}
\subsection{{分解式求解链}}
首先依据供货活跃率与规划容量形成一致性排序；随后以二元变量$x_i$表示供应商是否进入规划集合，以$q_i$表示单周订货量。最后按滚动周期输出订货基线。该分解避免将尚未建模的切换成本伪称为优化结果。

\begin{{figure}}[H]
\centering
\includegraphics[width=0.85\linewidth]{{../figures/fig_supplier_scores.pdf}}
\caption{{供应商一致性评分}}
\end{{figure}}

\section{{模型建立与求解}}
\subsection{{规划容量选集}}
令$c_i$为供应商$i$的规划容量，$D$为含损耗后的需求等价量，则核心覆盖约束写作
\begin{{equation}}
\sum_i c_i x_i \ge D,\qquad x_i\in\{{0,1\}}.
\end{{equation}}
以最少供应商数为目标：
\begin{{equation}}
\min\ \sum_i x_i.
\end{{equation}}
这里$c_i$由正供货量的75\%分位数确定，平均非零损耗率为{loss:.4f}。因此该容量是规划情景参数，不是最坏情形保证。

\begin{{table}}[H]
\centering
\caption{{登记结果的关键容量指标}}
\begin{{tabular}}{{lrr}}
\toprule
指标 & 数值 & 单位 \\
\midrule
需求等价量 & {demand:.2f} & m$^3$ \\
含损耗覆盖要求 & {required:.2f} & m$^3$ \\
规划容量上界 & {capacity:.2f} & m$^3$ \\
规划集合供应商数 & {supplier_count} & 家 \\
\bottomrule
\end{{tabular}}
\tabnote{{数据来源：登记的 \texttt{{result\_object.json}}。}}
\end{{table}}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.85\linewidth]{{../figures/fig_top50_capacity.pdf}}
\caption{{Top-50供应商的规划容量}}
\end{{figure}}

\section{{结果、局限与复现}}
\subsection{{供应商排序结果}}
完整Top-50名单由已登记声明{tex_escape(claim)}支持，包含50个供应商编号。名单和评分图由同一结果对象派生，禁止以手工名单替代。

\subsection{{局限性}}
当前规划容量采用75\%分位数；供应商切换、合同成本与最坏情形扰动均未进入目标函数。需求预测变化后必须重求订货与运输计划。

\subsection{{复现说明}}
本稿由正式 Skill 运行记录、官方原始附件、结果对象和图表登记表生成。图表登记数为{len(figures)}；文本中的关键名单声明为[claim:{tex_escape(claim)}]。

\section{{参考文献}}
\begin{{thebibliography}}{{9}}
\bibitem{{cumcm2021c}} 中国大学生数学建模竞赛组委会. 2021高教社杯全国大学生数学建模竞赛C题：生产企业原材料的订购与运输[EB/OL]. 2021.
\end{{thebibliography}}

\appendix
\section{{Top-50供应商编号}}
\begin{{longtable}}{{rr}}
\caption{{已登记的Top-50供应商编号}}\\
\toprule 序号 & 供应商编号 \\
\midrule
\endfirsthead
\toprule 序号 & 供应商编号 \\
\midrule
\endhead
{top50_rows}
\bottomrule
\end{{longtable}}

\section{{代码附录}}
\begin{{pycode}}[caption={{可复现求解入口（摘录）}}]
# 通过 solve-model Skill 读取原始附件并生成结果对象；
# 本文只消费已登记的 results/result_object.json。
run_standard_skill("solve-model")
\end{{pycode}}
\end{{document}}
"""
    (paper / "main.tex").write_text(tex, encoding="utf-8")
    (paper / "paper_generation_report.json").write_text(
        json.dumps({
            "status": "DRAFT_GENERATED",
            "layout_profile": "strict_cumcm_a4_v1",
            "layout_validator": "skills/write-model-paper/scripts/validate_cumcm_layout.py",
            "claim_bindings": 1,
            "blocked_claims": ["competition-paper completeness"],
            "template": "template/cume-template.tex",
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (paper / "claim_usage_report.json").write_text(json.dumps({claim: "used"}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    main(parser.parse_args().root)
