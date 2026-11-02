"""Build the modular figure-library capability report and gallery.

The gallery is deliberately explicit about synthetic examples.  It is a
template smoke test, not evidence from a scientific data set.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))


def parser_for_build():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/figure-library-gallery")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--category")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--no-zip", action="store_true", help="Do not create a preview ZIP")
    return parser


if __name__ == "__main__":
    _cli_args = parser_for_build().parse_args()

import matplotlib.pyplot as plt

from algorithms.figures import display_name, get_figure, get_spec, list_figures
from algorithms.sci_figures import FigureContract, export_publication_figure, publication_rc_params, resolve_cjk_font


def _apply_cjk_font(fig):
    """Apply the same CJK fallback used by the full random-preview builder."""
    font = resolve_cjk_font()
    if not font:
        return
    import matplotlib as mpl
    for artist in fig.findobj(mpl.text.Text):
        if any("\u4e00" <= char <= "\u9fff" for char in artist.get_text()):
            artist.set_fontfamily(font)


def _preview(name):
    def render(*args, **kwargs):
        return get_figure(name)(*args, mode="preview", **kwargs)
    return render


def _demo(name: str):
    from algorithms.figures.examples import example_data
    return get_figure(name)(data=example_data(name, seed=20261011), mode="preview")


def build(output: Path | None = None, *, limit: int | None = None,
          category: str | None = None, strict: bool = False, no_zip: bool = False):
    output = output or ROOT / "output/figure-library-gallery"
    output.mkdir(parents=True, exist_ok=True)
    source = output / "synthetic_gallery_source.json"
    source.write_text(json.dumps({"description": "synthetic data only", "seed": 0}, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = []
    errors = []
    names = [name for name in list_figures() if category is None or get_spec(name).category == category]
    if limit is not None:
        names = names[:max(0, limit)]
    for name in names:
        stem = output / name
        try:
            import matplotlib as mpl
            with mpl.rc_context(publication_rc_params(language="zh")):
                fig = _demo(name)
            _apply_cjk_font(fig)
            fig.set_size_inches(150/25.4, max(90, min(240, fig.get_size_inches()[1]*25.4))/25.4)
            contract = FigureContract(
                claim=f"{name} 模板展示数据结构与视觉编码",
                evidence=("synthetic demonstration",), source_paths=(str(source),),
                width_mm=150, height_mm=max(90, min(240, fig.get_size_inches()[1] * 25.4)), figure_role="data-overview",
                units="arbitrary unit", n_definition="formula-generated demonstration points; not independent measurements",
                statistic="descriptive template view", uncertainty="not estimated",
                randomness="deterministic formula; seed 0", data_transformations=("none; marks may be rasterized for dense views",),
                claim_status="uncertain", plotting_code=(str(Path(__file__).resolve()),),
            )
            # The gallery records font warnings instead of aborting: this
            # machine may not have a CJK font, and `visual_review` remains
            # NOT_CHECKED until a reviewer opens the proof on the target host.
            paths = export_publication_figure(fig, stem, contract, close=True, strict=False)
            payload = json.loads(Path(paths["metadata"]).read_text(encoding="utf-8"))
            figure_metadata = payload.get("figure_metadata") or {}
            spec = get_spec(name)
            manifest.append({"name": name, "name_zh": display_name(name), "category": spec.category,
                             "question_zh": spec.to_dict()["question_zh"], "implementation_level": spec.implementation_level,
                             "status": spec.status, "paper_suitable": spec.paper_suitable,
                             "files": {k: Path(v).name for k,v in paths.items()}, "audit": payload["audit"]["passed"],
                             "visual_review": payload["visual_review"]["status"], "synthetic": True,
                             "generic_demo": bool(figure_metadata.get("generic_demo"))})
        except Exception as exc:
            errors.append({"name": name, "error": f"{type(exc).__name__}: {exc}"})
            plt.close("all")
    (output / "preview_manifest.json").write_text(json.dumps({"schema_version": 1, "generated_from": "scripts/build_figure_library.py", "synthetic_notice": "合成数据，仅用于模板演示，不代表真实研究结果", "figures": manifest, "errors": errors}, ensure_ascii=False, indent=2), encoding="utf-8")
    catalog = [get_spec(name).to_dict() for name in names]
    (output / "figure_catalog_zh.json").write_text(json.dumps({"schema_version": 1, "description": "中文图表语义目录；英文 name 是稳定代码键，name_zh 是可直接传给 get_figure/get_spec 的中文名称。", "figures": catalog}, ensure_ascii=False, indent=2), encoding="utf-8")
    cards_by_category = {}
    for item in manifest:
        demo_note = item.get("implementation_level", "adapter")
        cards_by_category.setdefault(item["category"], []).append(f'<article><h2>{item["name_zh"]}</h2><p class="key">{item["name"]} · {demo_note}</p><p class="question">{item["question_zh"]}</p><img src="{item["files"]["png"]}" loading="lazy"><p><a href="{item["files"]["pdf"]}">PDF</a> · <a href="{item["files"]["svg"]}">SVG</a> · <a href="{item["files"]["metadata"]}">元数据</a></p><p>程序审计：{"PASS" if item["audit"] else "FAIL"}；视觉复核：{item["visual_review"]}</p></article>')
    sections = ''.join(f'<section><h2>{category}</h2><div class="grid">{"".join(cards)}</div></section>' for category, cards in cards_by_category.items())
    html = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>数学建模图表库</title><style>body{font:14px/1.5 system-ui,"Microsoft YaHei",sans-serif;max-width:1500px;margin:auto;padding:24px;color:#262626}section{margin:32px 0}section>h2{font-size:22px;border-bottom:2px solid #315D78;padding:8px 0}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}article{border:1px solid #ddd;background:#fff;padding:10px;min-width:0}article h2{font-size:17px;margin:0 0 2px}.key{color:#777;font-size:11px;margin:0 0 4px}.question{font-size:12px;min-height:34px;margin:4px 0;color:#444}img{width:100%;height:220px;object-fit:contain;background:#fafafa}a{color:#315D78}@media(max-width:900px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:600px){.grid{grid-template-columns:1fr}}</style><h1>数学建模图表代码库</h1><p>按图表的统计含义和建模用途分组。英文键用于兼容代码，中文名用于实际调用和元数据。合成数据仅用于模板演示，不代表真实研究结果。</p>' + sections + '</html>'
    (output / "index.html").write_text(html, encoding="utf-8")
    failed_audits = [item["name"] for item in manifest if not item["audit"]]
    qa = ["# 图表库画廊 QA 报告", "", f"- 注册图型：{len(list_figures())}", f"- 成功导出：{len(manifest)}", f"- 导出失败：{len(errors)}", f"- 程序审计通过：{len(manifest) - len(failed_audits)}；警告：{len(failed_audits)}", "- 所有示例均为合成数据，仅用于模板演示，不代表真实研究结果。", "- 程序审计通过不等于人工视觉复核通过；当前视觉状态保持 `NOT_CHECKED`。", "- 需要人工复核：字体字形、最终印刷尺寸、灰度辨识、图注与研究主张的一致性。"]
    if failed_audits:
        qa.extend(["", "## 程序审计警告", "", "以下示例在当前主机存在字体字形警告，因此保留 `audit.passed=false`，不能标记为完全通过：", "", "- " + "\n- ".join(failed_audits)])
    if errors: qa.extend(["", "## 失败项", ""] + [f"- `{e['name']}`：{e['error']}" for e in errors])
    (output / "qa-report.md").write_text("\n".join(qa) + "\n", encoding="utf-8")
    result = {"output": str(output), "registered": len(list_figures()), "selected": len(names),
              "exported": len(manifest), "errors": errors}
    if strict and (errors or failed_audits):
        raise RuntimeError(f"figure library build failed: {len(errors)} exports, {len(failed_audits)} audits")
    if not no_zip:
        import shutil
        archive = shutil.make_archive(str(output), "zip", root_dir=output)
        result["zip"] = archive
    return result


if __name__ == "__main__":
    args = _cli_args
    result = build(args.output, limit=args.limit, category=args.category, strict=args.strict, no_zip=args.no_zip)
    print(json.dumps(result, ensure_ascii=False, indent=2))

