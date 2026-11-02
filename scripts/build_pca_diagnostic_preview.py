"""Exercise dense PCA layouts with 80 variables from one fitted synthetic model."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


def build(output):
    import matplotlib as mpl
    import numpy as np
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "code"))
    from algorithms.figures import DataContract, get_figure
    from algorithms.sci_figures import FigureContract, export_publication_figure, publication_rc_params
    output.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20261009)
    groups = np.repeat(["类别甲", "类别乙", "类别丙"], 40)
    latent = rng.normal(0, .65, (120, 3))
    latent[:40] += [-2, 0, 1]; latent[40:80] += [2, -1, 0]; latent[80:] += [0, 2, -1]
    matrix = latent @ rng.normal(size=(3, 80)) + rng.normal(0, .35, (120, 80))
    standardized = StandardScaler().fit_transform(matrix)
    model = PCA().fit(standardized)
    scores = model.transform(standardized)[:, :2]
    loadings = model.components_[:2].T
    labels = [f"变量{i + 1:02d}" for i in range(80)]
    source = output / "pca_source.json"
    source.write_text(json.dumps({"source": "synthetic", "simulated": True, "seed": 20261009,
                                  "matrix": matrix.tolist(), "scores": scores.tolist(),
                                  "loadings": loadings.tolist(), "feature_labels": labels,
                                  "explained_variance": model.explained_variance_ratio_.tolist(),
                                  "groups": groups.tolist(), "transformations": ["standardize columns", "sklearn PCA"]},
                                 ensure_ascii=False, indent=2), encoding="utf-8")
    contract = DataContract(source="synthetic", simulated=True, independent_unit="synthetic scenario",
                            units={"scores": "standardized component", "loadings": "dimensionless"})
    cases = [("pca_biplot", {"scores": scores, "loadings": loadings,
              "explained_variance": model.explained_variance_ratio_[:2], "feature_labels": labels}, 100),
             ("pca_loadings", {"loadings": loadings, "labels": labels}, 190),
             ("cluster_scatter", {"embedding": scores, "groups": groups}, 100)]
    records = []
    with mpl.rc_context(publication_rc_params(language="zh")):
        for name, data, height in cases:
            fig = get_figure(name)(data={**data, "contract": contract}, mode="preview")
            fig.set_size_inches(150 / 25.4, height / 25.4)
            export_contract = FigureContract(claim="检查密集 PCA 标注、完整载荷及类别编码", evidence=("80 variables; one fitted synthetic PCA",),
                source_paths=(str(source.resolve()),), plotting_code=(str(Path(__file__).resolve()),),
                units="standardized", n_definition="120 synthetic scenarios; 80 variables",
                statistic="PCA scores and component coefficients", uncertainty="descriptive 2SD ellipses only",
                randomness="seed 20261009", width_mm=150, height_mm=height, claim_status="uncertain")
            files = export_publication_figure(fig, output / name, export_contract, close=True, strict=True)
            records.append({"name": name, "files": {k: Path(v).name for k, v in files.items()}})
    (output / "manifest.json").write_text(json.dumps({"figures": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    cards = ''.join(f'<article><h2>{r["name"]}</h2><a href="{r["files"]["pdf"]}"><img src="{r["files"]["png"]}"></a></article>' for r in records)
    (output / "index.html").write_text('<!doctype html><meta charset="utf-8"><title>PCA 密集数据修复预览</title>'
        '<style>body{font:15px system-ui;max-width:1400px;margin:auto;padding:24px}img{width:100%}article{margin:30px 0}</style>'
        '<h1>PCA 密集数据修复预览</h1><p>120 个模拟样本、80 个变量，共用同一组标准化数据和 PCA。双标图保留全部箭头，标注前12项；载荷图完整分面显示80项。椭圆为2SD数据轮廓。</p>'+cards, encoding="utf-8")
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/pca-repair-preview"))
    print(json.dumps(build(parser.parse_args().output), ensure_ascii=False))
