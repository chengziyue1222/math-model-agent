"""Run the installed skill in an independent temporary directory, without PYTHONPATH."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import tempfile
import hashlib
import importlib.metadata
import platform


def verify(skill, report_path, wheel=None, fixtures=None):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["PYTHONIOENCODING"] = "utf-8"
    with tempfile.TemporaryDirectory(prefix="figure-independent-") as directory:
        probe = subprocess.run([sys.executable, "-c", "import json; import algorithms.figures as f; from algorithms.figure_templates import render_template; from algorithms.sci_figures import FigureContract; print(json.dumps({'registered': len(f.list_figures()), 'module_path': f.__file__}))"],
                               cwd=directory, env=env, text=True, encoding="utf-8", capture_output=True)
        if probe.returncode:
            raise RuntimeError(probe.stderr)
        installed = json.loads(probe.stdout)
        from algorithms.figures import list_figures
        if installed["registered"] != len(list_figures()):
            raise ValueError("installed wheel registry differs from the calling environment")
        catalog = None
        if fixtures is not None:
            code = '''import json, sys
from pathlib import Path
import matplotlib.pyplot as plt
from algorithms.figures import DataContract, get_figure, list_figures
entries=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
assert set(entries)==set(list_figures())
for name,data in entries.items():
    data["contract"]=DataContract(**data["contract"])
    fig=get_figure(name)(data=data,mode="formal")
    fig.canvas.draw()
    assert fig._figure_metadata["paper_suitable"] is False
    plt.close(fig)
print(json.dumps({"formal_called":len(entries),"status":"PASS"}))
'''
            run = subprocess.run([sys.executable, '-c', code, str(fixtures.resolve())],
                                 cwd=directory, env=env, text=True, encoding='utf-8', capture_output=True)
            if run.returncode: raise RuntimeError(run.stdout + run.stderr)
            catalog = json.loads(run.stdout)
        command = [sys.executable, str(skill.resolve() / "scripts/minimal_example.py"),
                   "--output", "figures", "--suite"]
        result = subprocess.run(command, cwd=directory, env=env, text=True, encoding="utf-8", capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        files = list((Path(directory) / "figures").glob("*.figure.json"))
        records = [json.loads(p.read_text(encoding="utf-8")) for p in files]
        assert len(records) == 6
        assert all(d["configuration"]["sources"] == ["builtin:algorithms.figure_config.DEFAULTS"] for d in records)
        assert all(d["audit"]["passed"] and d["file_audit"]["status"] == "PASS" for d in records)
        assert all(d["configuration"]["width_mm"] == 150 for d in records)
        assert all(d["visual_review"]["status"] == "NOT_CHECKED" for d in records)
        from algorithms.sci_figures import resolve_cjk_font
        from matplotlib import font_manager
        import matplotlib
        font = resolve_cjk_font()
        report = {"status": "PASS", "command": command, "working_directory": directory,
                  "registered": installed["registered"], "module_path": installed["module_path"],
                  "catalog": catalog,
                  "python": sys.version, "platform": platform.platform(), "executable": sys.executable,
                  "dependencies": {name: importlib.metadata.version(name) for name in
                     ["math-model-agent", "numpy", "scipy", "matplotlib", "pandas", "scikit-learn", "networkx", "Pillow", "PyYAML", "PyMuPDF", "rarfile"]},
                  "matplotlib_backend": matplotlib.get_backend(), "font_name": font,
                  "font_path": font_manager.findfont(font) if font else None,
                  "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest() if wheel else None,
                  "repository_config_used": False, "figure_count": len(records),
                  "config_sources": records[0]["configuration"]["sources"],
                  "stdout": result.stdout, "stderr": result.stderr,
                  "visual_review": "NOT_CHECKED for temporary outputs; repository gallery reviewed separately"}
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Independent installed skill: six bundles PASS; builtin defaults; no PYTHONPATH")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill", type=Path, default=Path.home() / ".codex/skills/make-model-figures")
    parser.add_argument("--report", type=Path, default=Path("output/figure-upgrade/independent-install-validation.json"))
    parser.add_argument("--wheel", type=Path)
    parser.add_argument('--fixtures', type=Path, help='JSON inputs for every registered formal route')
    args = parser.parse_args()
    verify(args.skill, args.report, args.wheel, args.fixtures)
