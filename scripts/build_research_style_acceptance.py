"""Per-entry, three-case export evidence; visual decisions require actual review.

The existing figure schema 3 remains the sole per-figure acceptance record.
This runner never awards visual PASS. References and contest results are separate.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, is_dataclass
import hashlib
import html
import json
import os
from pathlib import Path
import sys
import warnings

ROOT = Path(__file__).resolve().parents[1]
if os.environ.get('MATH_MODEL_USE_INSTALLED') != '1':
    sys.path.insert(0, str(ROOT / "code"))

import fitz
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw

from algorithms.figures import display_name, get_figure, get_spec, list_figures
from algorithms.figures.base import metadata_value
from algorithms.figures.examples import example_data
from algorithms.sci_figures import FigureContract, export_publication_figure
from figure_acceptance_evidence import artist_evidence


def serial(value):
    if is_dataclass(value):
        return serial(asdict(value))
    if isinstance(value, dict):
        return {k: serial(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serial(v) for v in value]
    return metadata_value(value)


def build(out, *, baseline=False, names=None, config=None, batch_id=None):
    out.mkdir(parents=True, exist_ok=True)
    records = []
    manifest_name = 'manifest.json' if batch_id is None else f'manifest-batch-{int(batch_id)}.json'
    names = names or list_figures()
    for case in ("standard", "long_labels", "dense"):
        folder = out / case
        folder.mkdir(exist_ok=True)
        for name in names:
            stem = folder / name
            try:
                data = example_data(name, case=case)
                source = stem.with_suffix(".data.json")
                source.write_text(json.dumps(serial(data), ensure_ascii=False, indent=2), encoding="utf-8")
                with warnings.catch_warnings(record=True) as caught:
                    fig = get_figure(name)(data=data, config={} if config is None else config, mode="preview")
                    fig.canvas.draw()
                    contract = FigureContract(
                        f"{display_name(name)}：{case}合成示例，仅检验图型表达",
                        ("caller-supplied synthetic fixture; all values retained",),
                        source_paths=(str(source),), plotting_code=(str(Path(__file__).resolve()),),
                        width_mm=float(fig.get_figwidth()*25.4), height_mm=float(fig.get_figheight()*25.4),
                        theme_name="cumcm-research", statistic="chart-specific; see saved input",
                        n_definition="synthetic fixture observations; no population inference",
                        uncertainty="only caller-computed bounds; no fabricated intervals",
                        randomness="fixed seed 20261010; chart-specific generation",
                    )
                    paths = export_publication_figure(fig, stem, contract, strict=False)
                payload = json.loads(Path(paths["metadata"]).read_text(encoding="utf-8"))
                # Keep the numerical regression evidence inside the existing
                # per-entry schema rather than a second acceptance ledger.
                payload["numerical_regression"] = {"artist_evidence": artist_evidence(fig), "status": "NOT_CHECKED"}
                Path(paths["metadata"]).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                with Image.open(paths["png"]) as im:
                    im.convert("L").save(stem.with_name(stem.name + "_gray").with_suffix(".png"), dpi=(450, 450))
                with fitz.open(paths["pdf"]) as doc:
                    doc[0].get_pixmap(matrix=fitz.Matrix(1.8, 1.8)).save(stem.with_name(stem.name + "_vector").with_suffix(".png"))
                records.append({"name": name, "case": case, "implementation": get_spec(name).implementation_level,
                                "metadata": str(Path(paths["metadata"]).relative_to(out)),
                                "physical_mm": (fig.get_size_inches()*25.4).tolist(),
                                "programmatic": payload["programmatic_audit"],
                                "warnings": sorted({str(w.message) for w in caught}),
                                "visual_review": "NOT_CHECKED",
                                "source_hash": hashlib.sha256(source.read_bytes()).hexdigest()})
                plt.close(fig)
            except Exception as exc:
                records.append({"name": name, "case": case, "error": f"{type(exc).__name__}: {exc}", "visual_review": "FAIL"})
                plt.close("all")
            (out / manifest_name).write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"case": case, "exported": sum("error" not in r for r in records), "errors": sum("error" in r for r in records)}), flush=True)
    # Disjoint name batches share the output folders while keeping independent
    # manifests. Assemble the full index/proofs only after every batch finishes.
    if batch_id is not None:
        return records
    proof = fitz.open()
    for r in records:
        if "error" in r:
            continue
        path = out / r["case"] / (r["name"] + ".pdf")
        with fitz.open(path) as doc:
            page = proof.new_page(width=210/25.4*72, height=297/25.4*72)
            page.insert_text((20/25.4*72, 30), f'{r["name"]} / {r["case"]} / natural physical size', fontsize=9)
            page.show_pdf_page(fitz.Rect(20/25.4*72, 45, 20/25.4*72+doc[0].rect.width, 45+doc[0].rect.height), doc, 0)
    proof.save(out / "physical-proofs.pdf", deflate=True)
    proof.close()
    contacts(out, records)
    index(out, records)
    return records


def contacts(out, records):
    for case in ("standard", "long_labels", "dense"):
        rows = [r for r in records if r["case"] == case and "error" not in r]
        for start in range(0, len(rows), 6):
            board = Image.new("RGB", (1800, 1950), "white")
            draw = ImageDraw.Draw(board)
            for i, r in enumerate(rows[start:start+6]):
                path = out / case / (r["name"] + ".png")
                with Image.open(path) as source:
                    im = source.convert("RGB")
                im.thumbnail((875, 605))
                x, y = i%2*900, i//2*650
                board.paste(im, (x+(875-im.width)//2, y+30))
                draw.text((x+12, y+7), f'{start+i+1}. {r["name"]} / {case}', fill="black")
            board.save(out / f"contact-{case}-{start//6+1:02d}.png")


def index(out, records):
    cards = []
    for name in sorted({r["name"] for r in records}):
        cards.append(f'<h2>{html.escape(display_name(name))} / {name}</h2><div class="row">')
        for r in [r for r in records if r["name"] == name]:
            if "error" in r:
                cards.append(f'<p>{html.escape(r["error"])}</p>')
            else:
                base = f'{r["case"]}/{name}'
                cards.append(f'<article><b>{r["case"]}</b><img src="{base}.png"><p><a href="{base}.pdf">PDF</a> · <a href="{base}.svg">SVG</a> · <a href="{base}_gray.png">灰度</a> · <a href="{base}.figure.json">验收记录</a></p></article>')
        cards.append('</div>')
    count=len({record['name'] for record in records})
    (out / 'index.html').write_text(f'<!doctype html><meta charset="utf-8"><title>图型逐项验收</title><style>body{{font:15px system-ui;margin:30px;color:#20252b}}.row{{display:flex;gap:15px}}article{{width:33%;border:1px solid #ddd;padding:10px}}img{{width:100%}}</style><h1>{count}个入口逐项验收</h1><p>三类合成数据仅检验模板；机器通过与视觉复核分开记录。未查看的成果保持NOT_CHECKED。</p>'+''.join(cards), encoding='utf-8')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/research-style-upgrade/gallery")
    parser.add_argument("--names", nargs="*")
    parser.add_argument("--width-mm", type=float)
    parser.add_argument("--batch-id", type=int, help="Independent manifest for a disjoint renderer batch; omits aggregate proofs")
    args = parser.parse_args()
    build(args.output, names=args.names, config={"width_mm": args.width_mm} if args.width_mm is not None else None, batch_id=args.batch_id)
