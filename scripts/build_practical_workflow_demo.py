"""Build a synthetic transportation paper and a portable numerical support ZIP.

The paper is a teaching example, not an attested competition submission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]

REPRODUCER = '''"""Reproduce the synthetic allocation result and publication figures."""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

root = Path(__file__).resolve().parents[1]
d = json.loads((root / "data/transportation.json").read_text(encoding="utf-8"))
c = np.array(d["unit_cost"], dtype=float)
s = np.array(d["capacity"], dtype=float)
b = np.array(d["demand"], dtype=float)
n, m = c.shape
A = np.zeros((n, n*m))
B = np.zeros((m, n*m))
for i in range(n): A[i, i*m:(i+1)*m] = 1
for j in range(m): B[j, j::m] = 1

def solve(cost, supply):
    res = linprog(cost.ravel(), A_ub=A, b_ub=supply, A_eq=B, b_eq=b,
                  bounds=(0, None), method="highs")
    assert res.success, res.message
    x = res.x.reshape(n, m)
    assert np.all(x >= -1e-8)
    assert np.all(x.sum(axis=1) <= supply + 1e-8)
    assert np.allclose(x.sum(axis=0), b, atol=1e-8)
    primal = float(np.sum(x*cost))
    dual = float(supply @ res.ineqlin.marginals + b @ res.eqlin.marginals)
    assert abs(primal - dual) < 1e-8
    return x, primal, dual

x, optimal, dual = solve(c, s)
remaining_s, remaining_b = s.copy(), b.copy()
baseline = np.zeros_like(x)
i = j = 0
while i < n and j < m:
    q = min(remaining_s[i], remaining_b[j])
    baseline[i, j] = q
    remaining_s[i] -= q
    remaining_b[j] -= q
    if remaining_s[i] <= 1e-8: i += 1
    if remaining_b[j] <= 1e-8: j += 1
baseline_cost = float(np.sum(baseline*c))
shifted_supply = s + np.array([-10, 10, 0])
shifted, shifted_cost, _ = solve(c, shifted_supply)
scales = [.9, .95, 1., 1.05, 1.1]
sensitivity = [solve(c*factor, s)[1] for factor in scales]
checks = {"feasible": True, "primal_dual_agreement": True,
          "baseline_feasible": bool(np.allclose(baseline.sum(0), b)),
          "baseline_comparison": bool(optimal <= baseline_cost)}
out = {"status": "PASS", "simulated": True, "allocation": x.tolist(),
       "optimal_cost": optimal, "dual_cost": dual, "baseline_cost": baseline_cost,
       "saving_percent": (baseline_cost-optimal)/baseline_cost*100,
       "capacity_shift_cost": shifted_cost, "capacity_shift_allocation": shifted.tolist(),
       "cost_factors": scales, "sensitivity_costs": sensitivity, "checks": checks}
assert all(checks.values())
(root / "results").mkdir(exist_ok=True)
(root / "results/results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

fonts = {f.name for f in font_manager.fontManager.ttflist}
font = next((f for f in ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC"] if f in fonts), "DejaVu Sans")
plt.rcParams.update({"font.family": font, "axes.unicode_minus": False, "svg.fonttype": "none"})
(root / "figures").mkdir(exist_ok=True)
fig, ax = plt.subplots(figsize=(150/25.4, 88/25.4))
for i in range(n):
    for j in range(m):
        if x[i,j] > 0: ax.scatter(j, i, s=420*x[i,j]/75, c="#087E8B", edgecolors="white")
        ax.text(j, i+.38, f"{x[i,j]:g}", ha="center", fontsize=9)
ax.set(xticks=range(m), xticklabels=["地区甲", "地区乙", "地区丙"],
       yticks=range(n), yticklabels=["供应商A", "供应商B", "供应商C"],
       xlim=(-.6, m-.4), ylim=(n-.35, -.65), xlabel="需求地区", ylabel="供应商")
for value in [5, 50, 75]: ax.scatter([], [], s=420*value/75, color="#087E8B", label=f"{value} 件")
ax.legend(loc="upper left", bbox_to_anchor=(1,1), frameon=False, fontsize=8, labelspacing=1.5)
ax.set_title("最优调运数量（模拟案例）", fontsize=11)
fig.subplots_adjust(left=.16, right=.76, bottom=.18, top=.84)
for extension in ["pdf", "svg", "png"]:
    fig.savefig(root / "figures" / ("allocation." + extension), dpi=450)
plt.close(fig)
fig, ax = plt.subplots(figsize=(150/25.4, 80/25.4))
ax.plot(scales, sensitivity, marker="o", color="#087E8B")
ax.set(xlabel="全体单位成本乘数", ylabel="最优总成本 / 元", xticks=scales)
ax.set_title("统一成本缩放敏感性（模拟案例）", fontsize=11)
ax.grid(axis="y", color="#dfe4e8", linewidth=.5)
fig.subplots_adjust(left=.18, right=.95, bottom=.21, top=.83)
for extension in ["pdf", "svg", "png"]:
    fig.savefig(root / "figures" / ("sensitivity." + extension), dpi=450)
plt.close(fig)
print(json.dumps({"status": "PASS", "optimal_cost": optimal, "baseline_cost": baseline_cost}))
'''


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def build(output):
    output = output.resolve()
    for folder in ("src", "data", "reports", "proofs"):
        (output / folder).mkdir(parents=True, exist_ok=True)
    (output / "src/reproduce.py").write_text(REPRODUCER, encoding="utf-8")
    shutil.copy2(ROOT / "examples/supplier_allocation/data/transportation.json", output / "data/transportation.json")
    (output / "requirements.txt").write_text("numpy>=1.21\nscipy>=1.9\nmatplotlib>=3.9\n", encoding="utf-8")
    (output / "README.md").write_text("# 模拟教学案例\n\n安装依赖：python -m pip install -r requirements.txt\n\n复算：python src/reproduce.py\n\n重新生成结果与两组 PDF/SVG/450 DPI PNG。中文字体需安装 Microsoft YaHei、SimHei 或 Noto Sans CJK SC 之一；缺字体会回退英文基础字形，需补装后重新绘图。模型数据为仓库合成数据，无真实业务或访谈结论。\n", encoding="utf-8")
    subprocess.run([sys.executable, str(output / "src/reproduce.py")], cwd=output, check=True)
    r = json.loads((output / "results/results.json").read_text(encoding="utf-8"))
    prefix = (ROOT / "skills/write-model-paper/assets/cume-template.tex").read_text(encoding="utf-8").split(r"\newcommand{\PaperTitle}")[0]
    body = r'''
\newcommand{\PaperTitle}{供应商调运优化与实用图表证据交接示例}
\begin{document}
\pagenumbering{arabic}\setcounter{page}{1}
\begin{center}{\fontsize{18pt}{26pt}\selectfont\heitifont\PaperTitle}\end{center}
\begin{center}{\large\heitifont 摘\quad 要}\end{center}
本文使用明确标注的合成数据，演示模型、保存结果、图表、论文与复算支撑包的交接。三个供应商向三个地区运输同一类物资，在满足需求且不超产能的条件下最小化线性运输成本。
以西北角法作为可行基线，线性规划求得最优成本 1060 元，基线成本 1685 元，降低 37.09\%。重新计算目标、供需守恒以及原始与对偶目标一致性均通过。气泡矩阵直接呈现全部九个调运单元，面积与件数严格成比例，零值仍显示数值。敏感性曲线来自五次重新求解，不绘制未经计算的置信带。
本示例不代表真实参赛成绩或业务结论，也未接受独立专家审核。它用于检查可复现交付与最终页面，不以图表数量判断论文质量。

\noindent\textbf{关键词：}运输问题；线性规划；供需守恒；可复现；图表证据
\newpage
\section{问题重述}
给定供应商产能、地区需求和单位运费，确定各运输路径的调运件数。问题一要求给出最小成本方案并与可行基线比较；问题二要求检查成本和产能变化的影响。输入来自支撑包的合成数据文件，数量单位为件，单位运费为元/件。
\section{假设与符号}
所有物资可分割，单位运费固定，无运输损耗、路径拥堵或启动成本；全部需求必须满足。$x_{ij}\geq0$ 为供应商 $i$ 到地区 $j$ 的运输量，$s_i$ 为产能，$d_j$ 为需求，$c_{ij}$ 为单位运费。总供给与总需求均为 200 件。
\begin{table}[H]\centering\caption{合成输入数据}
\begin{tabular}{lrrrr}\toprule 对象&地区甲&地区乙&地区丙&产能\\\midrule
供应商A&8&6&10&80\\供应商B&9&7&4&70\\供应商C&3&4&2&50\\\bottomrule\end{tabular}
\end{table}
\section{模型建立与求解}
建立线性规划：
\begin{align*}
\min_x\quad&\sum_{i=1}^{3}\sum_{j=1}^{3}c_{ij}x_{ij},\\
\text{s.t.}\quad&\sum_jx_{ij}\leq s_i,\quad i=1,2,3,\\
&\sum_ix_{ij}=d_j,\quad(d_1,d_2,d_3)=(60,75,65),\\
&x_{ij}\geq0.
\end{align*}
程序使用 SciPy 的 HiGHS 接口求解\cite{scipy}，终止状态必须成功后才能登记结果。独立复算所有行列和与目标函数，并检查求解器给出的对偶目标与原始目标一致，容差为 $10^{-8}$。这一证明适用于当前连续线性模型。
\section{问题一：调运结果与基线}
最优调运矩阵为 $\left[\begin{smallmatrix}5&75&0\\5&0&65\\50&0&0\end{smallmatrix}\right]$。其行和为 80、70、50，列和为 60、75、65，所有需求得到满足。成本为 1060 元，与对偶目标一致。西北角法成本为 1685 元，是满足相同供需约束的基线，改善幅度为 $(1685-1060)/1685=37.09\%$。
\begin{figure}[H]\centering\includegraphics[width=150mm]{figures/allocation.pdf}\caption{全部调运结果，气泡面积与件数成比例；零值标为0。模拟数据，无抽样误差区间。}\end{figure}
图中地区乙全部由A供应，地区丙全部由B供应，地区甲由三家共同供应。圆面积用同一标尺，不使用最小面积偏移；图例给出5、50、75件。数值标签避免仅凭圆大小比较细小差异。
\section{问题二：敏感性与局限}
将全部单位成本同时乘以 0.90、0.95、1.00、1.05、1.10，重新求解成本分别为 954、1007、1060、1113、1166 元。在相同可行域下，正的统一成本乘数保留最优方案，目标按比例变化。这是特定扰动族的检验，不能据此断言任意运费变化均稳健。
\begin{figure}[H]\centering\includegraphics[width=150mm]{figures/sensitivity.pdf}\caption{五次求解得到的最优成本；连线辅助阅读，不代表未计算的预测区间。}\end{figure}
另将A产能减少10件、B产能增加10件，总产能仍为200件，重新求解成本为 SHIFT 元。产能转移会改变可行路径与最优分配，应重新求解。本模型不包含整数包装、固定发车费和不确定需求；加入这些条件需修改模型并重新验证。
\section{结论与复现说明}
当前合成输入下最优成本1060元，比可行基线下降37.09\%。支撑包保存输入、完整程序、结果与校验；在独立目录运行可重新生成数值和图表。结论仅适用于该合成案例。
\section*{AI工具使用声明}
本教学示例使用了 AI 工具辅助编程、写作与排版，过程及核验见《AI工具使用详情》。未完成人工审签，正式参赛需由参赛者核对。\par
\begingroup\linespread{1.05}\small
\begin{thebibliography}{9}
\bibitem{scipy}SciPy. scipy.optimize.linprog 官方 API 文档，https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.linprog.html.
\end{thebibliography}
\endgroup
\newpage
\section*{附录：完整文件清单与自编程序}
本论文为合成教学示例，支撑包中的完整文件清单如下：
\begin{itemize}
\item \texttt{src/reproduce.py}：独立求解、验证和制图程序。
\item \texttt{data/transportation.json}：全部合成输入。
\item \texttt{results/results.json}：机器结果、基线与敏感性。
\item \texttt{requirements.txt}：第三方依赖清单。
\item \texttt{README.md}：安装与复算说明。
\item AI工具使用详情.pdf：辅助工具与核验记录。
\end{itemize}
程序全文如下，亦提供相同源文件。第三方库通过依赖管理器安装。
\lstinputlisting[style=modelcode]{src/reproduce.py}
\begin{pycode}
# Entry command from the support root:
# python src/reproduce.py
\end{pycode}
\end{document}
'''.replace("SHIFT", f'{r["capacity_shift_cost"]:.0f}')
    # The table is generated from the saved input rather than maintaining a second copy.
    data = json.loads((output / "data/transportation.json").read_text(encoding="utf-8"))
    for row, label in enumerate(["供应商A", "供应商B", "供应商C"]):
        old = ["8&6&10&80", "9&7&4&70", "3&4&2&50"][row]
        new = "&".join(str(v) for v in [*data["unit_cost"][row], data["capacity"][row]])
        body = body.replace(label + "&" + old, label + "&" + new)
    (output / "paper.tex").write_text(prefix + body, encoding="utf-8")
    details = r'''\documentclass[12pt,a4paper]{article}
\usepackage[margin=2.5cm]{geometry}\usepackage{fontspec}\setmainfont{SimSun}
\XeTeXlinebreaklocale "zh"\XeTeXlinebreakskip=0pt plus 1pt
\begin{document}\section*{AI工具使用详情}
\subsection*{工具与模型}Codex，本对话的AI编程助手。精确模型版本以会话界面记录为准，本文件不虚构版本编号。
\subsection*{使用目的与环节}辅助改进数学建模 skill、制图程序、验证脚本，并生成这一合成教学论文及其支撑材料。
\subsection*{提示与交互过程}用户要求执行实用图表改进方案，随后提供五图成果代码作为学习参考；助手阅读方案、图型与代码，编写通用模式和验证，再构建本示例。
\subsection*{输出采用情况}采用辅助生成的完整源程序、图注、模型说明和排版。模型数值以程序运行保存的结果为准。
\subsection*{人工修改状态}本次没有参赛团队人工修改或审签记录；不得将助手的修改和自动测试称为参赛者人工审核。使用者后续修改需自行补充记录。
\subsection*{核验方法}程序校验非负、产能、需求、可行基线与原始/对偶目标，复算目标1060元。另运行支撑包独立目录复算，检查PDF页面与图表。原始访谈未用于本示例。
\end{document}'''
    (output / "ai-details.tex").write_text(details, encoding="utf-8")
    for source in ("paper.tex", "ai-details.tex"):
        for _ in range(2):
            run = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", source], cwd=output, capture_output=True, text=True, encoding="utf-8", errors="replace")
            (output / "reports" / f"{Path(source).stem}-compile.txt").write_text(run.stdout + run.stderr, encoding="utf-8")
            if run.returncode:
                raise RuntimeError(f"{source} failed; see compile log")
    shutil.copy2(output / "ai-details.pdf", output / "AI工具使用详情.pdf")
    files = ["src/reproduce.py", "data/transportation.json", "results/results.json", "requirements.txt", "README.md", "AI工具使用详情.pdf"]
    manifest = {"files": [{"path": name, "sha256": hashlib.sha256((output/name).read_bytes()).hexdigest()} for name in files],
                "dependencies": {"file": "requirements.txt", "install": "python -m pip install -r requirements.txt", "fonts": ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC"], "font_installation": "Install one declared CJK font using the operating system font installer."},
                "reproduce": {"command": ["{python}", "src/reproduce.py"], "timeout_seconds": 120}}
    write_json(output / "support-manifest.json", manifest)
    with zipfile.ZipFile(output / "support.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for name in files:
            archive.write(output / name, name)
    write_json(output / "reports/model-validation.json", {"status": "PASS", "simulated": True, "checks": r["checks"], "metrics": {k:r[k] for k in ["optimal_cost", "dual_cost", "baseline_cost", "saving_percent", "capacity_shift_cost"]}})
    import fitz
    from PIL import Image, ImageDraw
    with fitz.open(output / "paper.pdf") as doc:
        cols, cell_w, cell_h = 3, 480, 680
        contact = Image.new("RGB", (cols*cell_w, ((len(doc)+cols-1)//cols)*cell_h), "white")
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=120)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            img.save(output / "proofs" / f"page-{i+1}.png")
            img.thumbnail((cell_w-12, cell_h-25))
            contact.paste(img, ((i%cols)*cell_w, (i//cols)*cell_h+20))
            ImageDraw.Draw(contact).text(((i%cols)*cell_w+10, (i//cols)*cell_h+5), f"Page {i+1}", fill="black")
        contact.save(output / "proofs/contact.png")
    print(f"Saved reproducible paper and support ZIP: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/practical-workflow-demo")
    build(parser.parse_args().output)
