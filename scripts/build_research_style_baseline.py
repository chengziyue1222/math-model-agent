"""Render the preserved pre-change code with the exact current saved inputs."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from figure_acceptance_evidence import artist_evidence


def build(snapshot, gallery, out):
    os.chdir(snapshot)
    sys.path.insert(0, str(snapshot / "code"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from algorithms.figures import get_figure, DataContract
    records = []
    out.mkdir(parents=True, exist_ok=True)
    for source in sorted(gallery.glob("*/*.data.json")):
        folder = out / source.parent.name
        folder.mkdir(exist_ok=True)
        name = source.name.removesuffix(".data.json")
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
            data["contract"] = DataContract(**data["contract"])
            fig = get_figure(name)(data=data, mode="preview")
            fig.savefig(folder / (name + ".png"), dpi=180)
            fig.savefig(folder / (name + ".pdf"))
            record = {"name": name, "case": source.parent.name,
                      "physical_mm": (fig.get_size_inches()*25.4).tolist(),
                      "metadata": fig._figure_metadata,
                      "lines": [[line.get_xydata().tolist() for line in ax.lines] for ax in fig.axes],
                      "scales": [[ax.get_xscale(), ax.get_yscale()] for ax in fig.axes],
                      "artist_evidence": artist_evidence(fig),
                      "source_hash": hashlib.sha256(source.read_bytes()).hexdigest()}
            plt.close(fig)
        except Exception as exc:
            record = {"name": name, "case": source.parent.name, "error": f"{type(exc).__name__}: {exc}",
                      "source_hash": hashlib.sha256(source.read_bytes()).hexdigest()}
            plt.close("all")
        records.append(record)
    (out / "manifest.json").write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"baseline_rendered": sum("error" not in r for r in records), "errors": [r for r in records if "error" in r][:5]}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--gallery", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.snapshot.resolve(), args.gallery.resolve(), args.output.resolve())
