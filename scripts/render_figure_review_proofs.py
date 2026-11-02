"""Render PNG, PDF and grayscale proof sheets for explicit visual sampling."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import fitz
from PIL import Image, ImageDraw, ImageFont, ImageOps

SAMPLES = {
    "comparison": ["bar", "grouped_bar", "forest"],
    "distribution": ["histogram", "boxplot", "violin"],
    "relationship": ["scatter", "scatter_trend", "joint_density"],
    "time": ["time_series", "error_band", "forecast_interval"],
    "matrix": ["heatmap", "response_surface", "transition_matrix"],
    "evaluation": ["roc_curve", "pr_curve", "calibration_curve"],
    "optimization": ["pareto", "tornado", "robustness_envelope"],
    "multivariate": ["pca_biplot", "pca_loadings", "cluster_scatter"],
    "network": ["community_network", "weighted_network", "sankey", "alluvial"],
    "multi_metric": ["radar", "ranking", "score_bar"],
    "diagram": ["algorithm_flow", "geometry", "technical_route"],
    "spatial": ["spatial_scatter", "spatial_heatmap", "spatial_3d"],
}


def render(directory, output):
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((directory / "preview_manifest.json").read_text(encoding="utf-8"))
    entries = {item["name"]: item for item in manifest["figures"]}
    records = []
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)
    for category, names in SAMPLES.items():
        width, height = 740, 475
        sheet = Image.new("RGB", (len(names) * width, 3 * height), "#e8edf0")
        for column, name in enumerate(names):
            item = entries[name]
            png = directory / item["files"]["png"]
            pdf = directory / item["files"]["pdf"]
            with Image.open(png) as opened:
                color = opened.convert("RGB")
            with fitz.open(pdf) as doc:
                pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                vector = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            for row, (kind, proof) in enumerate((("PNG", color), ("PDF render", vector), ("grayscale", ImageOps.grayscale(color).convert("RGB")))):
                proof.thumbnail((width - 12, height - 42))
                card = Image.new("RGB", (width, height), "white")
                card.paste(proof, ((width - proof.width) // 2, 38 + (height - 38 - proof.height) // 2))
                ImageDraw.Draw(card).text((10, 8), f"{name} | {kind}", font=font, fill="#252a2e")
                sheet.paste(card, (column * width, row * height))
            records.append({"name": name, "group": category, "registry_category": item["category"],
                            "implementation_level": item["implementation_level"],
                            "png_sha256": hashlib.sha256(png.read_bytes()).hexdigest(),
                            "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
                            "proof_sheet": f"{category}.png"})
        sheet.save(output / f"{category}.png")
    (output / "sample-manifest.json").write_text(json.dumps({"samples": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=Path("output/random-figure-previews"))
    parser.add_argument("--output", type=Path, default=Path("output/repair-round-3-visual-proofs"))
    args = parser.parse_args()
    print(f"Rendered {render(args.directory, args.output)} samples; rendering alone is not a visual review")
