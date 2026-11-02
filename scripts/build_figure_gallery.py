"""Rebuild traceable chart examples, A4 proofs and a local HTML gallery.

Run from the repository: python scripts/build_figure_gallery.py
Review states remain NOT_CHECKED until a reviewer actually inspects the artifacts.
"""
from __future__ import annotations

import hashlib
import html
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
sys.path.insert(0, str(ROOT / "skills/make-model-figures/scripts"))

import fitz
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from algorithms.sci_figures import FigureContract, export_publication_figure, paper_figure_rc_params, publication_size
from minimal_example import main as demos
from visualize import generate_figures, load_results, _problem_values, _heatmap_figure
from solve import average_power


def build(output=ROOT / "output/figure-upgrade"):
    output.mkdir(parents=True, exist_ok=True)
    demos(output / "examples", suite=True)
    originals = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT / "figures").glob("*.png")}
    generate_figures(output_dir=output / "real")
    # Check heatmap artist values independently against the model at every grid point.
    params, height, period, depth, omega, wave_number, power = _problem_values(load_results())
    with mpl.rc_context(paper_figure_rc_params()):
        fig = _heatmap_figure(params, height, depth, omega, wave_number)
    expected = np.array([[average_power([r,d,params[2],params[3]], omega,wave_number,height,depth)
                          for r in np.linspace(.5,5,50)] for d in np.linspace(.5,10,50)])
    actual = np.asarray(fig.axes[0].collections[0].get_array())
    np.testing.assert_array_equal(actual, expected)
    np.testing.assert_array_equal(fig.axes[0].lines[0].get_xydata()[0], params[:2])
    plt.close(fig)
    verification = {"grid_shape": list(expected.shape), "max_absolute_error": float(np.max(abs(expected-actual))),
                    "saved_point": params[:2].tolist(), "saved_point_power_W": power,
                    "grid_min_W": float(expected.min()), "grid_max_W": float(expected.max()),
                    "normalization": "linear, unchanged min/max; no smoothing or heatmap resampling",
                    "original_png_sha256": originals}
    # Compare the second real case to the preserved pre-change implementation.
    import types
    from visualize import _time_history_figure
    original_code = subprocess.check_output(["git", "show", "HEAD:code/visualize.py"], cwd=ROOT).decode("utf-8")
    (output / "visualize_before.py").write_text(original_code, encoding="utf-8")
    baseline = types.ModuleType("figure_before")
    baseline.__file__ = str(ROOT / "code/visualize.py")
    args = (params,height,period,depth,omega,wave_number,power)
    with mpl.rc_context():
        exec(compile(original_code, baseline.__file__, "exec"), baseline.__dict__)
        old = baseline._time_history_figure(*args)
    with mpl.rc_context(paper_figure_rc_params()):
        new = _time_history_figure(*args)
    for old_ax, new_ax in zip(old.axes,new.axes):
        for old_line,new_line in zip(old_ax.lines,new_ax.lines):
            np.testing.assert_array_equal(old_line.get_xydata(),new_line.get_xydata())
    verification["time_history_before_after"] = "all line arrays exactly equal; 2000 times, same initial state, RK45 and parameters"
    plt.close(old)
    plt.close(new)
    # A deterministic dense scatter demonstration with all observations retained.
    x = np.linspace(0,10,12000)
    y = np.sin(x) + .2*np.sin(71*x)
    source = output / "examples/dense_data.npz"
    np.savez(source, x=x, y=y)
    with mpl.rc_context(paper_figure_rc_params()):
        fig, ax = plt.subplots(figsize=publication_size(None, 75), constrained_layout=True)
        ax.scatter(x,y,s=1,alpha=.2,rasterized=True)
        ax.set(xlabel="x (s)", ylabel="响应 (m)", title="合成演示：12,000个点，全部保留")
        c = FigureContract("合成演示保留全部12,000个观测点", ("全部散点",), source_paths=(str(source),),
                           plotting_code=(str(Path(__file__).resolve()),), width_mm=150, units="s,m",
                           model_name="synthetic sinusoidal demonstration", randomness="deterministic formula",
                           n_definition="12000 formula-generated points, not independent measurements",
                           statistic="raw synthetic values", uncertainty="not estimated", data_transformations=("rasterized marks; no filtering",))
        export_publication_figure(fig, output / "examples/demo_dense", c, close=True)
    proof = fitz.open()
    cards = []
    for index, metadata_path in enumerate(sorted(output.glob("*/*.figure.json")), 1):
        stem = metadata_path.with_name(metadata_path.name.removesuffix(".figure.json"))
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        pdf = fitz.open(stem.with_suffix(".pdf"))
        page = proof.new_page(width=210/25.4*72, height=297/25.4*72)
        page.insert_text((25/25.4*72, 42), f"A4 proof {index}: {stem.name}", fontsize=10)
        page.insert_text((25/25.4*72, 57), "Natural physical size; print at 100%. Screen zoom is not a physical-size check.", fontsize=8)
        x0, y0 = 25/25.4*72, 30/25.4*72
        rect = fitz.Rect(x0,y0,x0+pdf[0].rect.width,y0+pdf[0].rect.height)
        page.show_pdf_page(rect, pdf, 0)
        page.draw_line((x0, y0+pdf[0].rect.height+25), (x0+100/25.4*72, y0+pdf[0].rect.height+25))
        page.insert_text((x0,y0+pdf[0].rect.height+39), "100 mm scale reference", fontsize=8)
        pdf.close()
        gray_path = stem.with_name(stem.name+"_gray.png")
        with Image.open(stem.with_suffix(".png")) as image:
            image.convert("L").save(gray_path)
        png = stem.with_suffix(".png").relative_to(output).as_posix()
        before = ROOT / "figures" / stem.with_suffix(".png").name
        before_html = f'<figure><img src="../../figures/{before.name}"><figcaption>原图（文件未改动）</figcaption></figure>' if before.exists() else ""
        changes = ("原线性功率范围不变；浅到深色板、描边星标、图外图例、上边距、2000/4000/6000 W等值线。保存参数点不称全局最优。" if "heatmap" in stem.name else
                   "最终150 mm宽；统一7–8 pt字体、线宽与色板；保留原数值、单位与计算过程。" if before.exists() else "合成数据仅验证模板能力；不代表真实研究结论。")
        sources = "<br>".join(html.escape(p) for p in payload["contract"]["source_paths"])
        warnings = "<br>".join(html.escape(w) for w in payload["audit"]["warnings"]) or "无"
        cards.append(f'<section><h2>{stem.name}</h2><div class="compare">{before_html}<figure><img src="{png}"><figcaption>新图</figcaption></figure></div>'
                     f'<p>{changes}</p><p>来源：{sources}</p><p>程序：{"PASS" if payload["audit"]["passed"] else "FAIL"}；视觉：{payload["visual_review"]["status"]}（以元数据为准）。</p>'
                     f'<p>警告：{warnings}</p><p><a href="{stem.with_suffix(".pdf").relative_to(output).as_posix()}">PDF</a> · '
                     f'<a href="{gray_path.relative_to(output).as_posix()}">灰度</a> · <a href="{metadata_path.relative_to(output).as_posix()}">元数据</a> · A4校样第{index}页</p></section>')
    proof.save(output / "physical_proofs.pdf")
    proof.close()
    verification["originals_unchanged"] = all(hashlib.sha256((ROOT / "figures" / name).read_bytes()).hexdigest()==digest for name,digest in originals.items())
    (output / "source_verification.json").write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding="utf-8")
    (output / "gallery.html").write_text('''<!doctype html><html lang="zh"><meta charset="utf-8"><title>建模图表改进画廊</title>
<style>body{font:16px/1.7 system-ui;max-width:1200px;margin:40px auto;color:#262626;padding:20px}section{border-top:1px solid #ddd;padding:24px 0}.compare{display:flex;gap:20px}figure{margin:0;flex:1;min-width:0}img{width:100%;height:auto}p{overflow-wrap:anywhere}a{color:#315D78}</style>
<h1>建模图表：改进与验证</h1><p>真实案例：波浪能热力图与时域三面板。原始输入、模型及原图均保留。其他样例明确为合成演示。</p>
<p><a href="physical_proofs.pdf">A4物理尺寸校样</a> · <a href="source_verification.json">源值核对</a> · <a href="review-summary.md">最终验收记录</a></p>
<p>校样中的图按实际毫米尺寸排版；屏幕缩放不代表物理尺寸。实物打印检查未执行。</p>'''+"\n".join(cards)+"</html>",encoding="utf-8")
    print(output / "gallery.html")
    subprocess.run(["pdftoppm", "-r", "110", "-png", str(output/"physical_proofs.pdf"), str(output/"proof")],check=True)


if __name__ == "__main__":
    build()
