"""Staged, dimension-preserving publication bundles and independent review state."""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
import platform
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from .figure_config import load_figure_config


def implementation_hashes():
    """Bind exports to the actual installed rendering code, including the registry."""
    root = Path(__file__).parent
    files = [root / name for name in
             ("sci_figures.py", "figure_config.py", "figure_templates.py", "figure_export.py")]
    files.extend(sorted((root / "figures").glob("*.py")))
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files}


def inspect_exports(paths, width_mm, height_mm, dpi):
    import fitz
    expected = np.array([width_mm, height_mm]) / 25.4 * dpi
    with Image.open(paths["png"]) as im:
        if im.format != "PNG" or im.mode != "RGB":
            raise ValueError("PNG must be RGB")
        if np.max(np.abs(np.array(im.size) - expected)) > 1.01:
            raise ValueError("PNG pixel dimensions differ from physical target")
        if any(abs(d - dpi) > .05 for d in im.info.get("dpi", (0, 0))):
            raise ValueError("PNG DPI differs from target")
        png = {"pixels": list(im.size), "mode": im.mode, "dpi": im.info["dpi"]}
    with fitz.open(paths["pdf"]) as doc:
        size = np.array([doc[0].rect.width, doc[0].rect.height]) / 72 * 25.4
        if len(doc) != 1 or np.max(np.abs(size - [width_mm, height_mm])) > .02:
            raise ValueError("PDF dimensions differ from target")
        fonts = [{"name": f[3], "embedded": bool(doc.extract_font(f[0])[3])}
                 for f in doc[0].get_fonts() if f[0]]
    root = ET.parse(paths["svg"]).getroot()
    svg_size = np.array([float(root.attrib[k].removesuffix("pt")) for k in ("width", "height")]) / 72 * 25.4
    if np.max(np.abs(svg_size - [width_mm, height_mm])) > .02:
        raise ValueError("SVG dimensions differ from target")
    return {"status": "PASS", "png": png, "pdf_fonts": fonts,
            "svg_text": "preserved; matching fonts must be installed on the viewing machine"}


def export_bundle(fig, output_stem, contract, *, dpi=None, strict=True,
                  close=False, config=None, source_root=None):
    from .sci_figures import audit_publication_figure
    cfg = load_figure_config(config if config is not None else getattr(fig, "_figure_config", None),
                             dpi=dpi, width_mm=contract.width_mm,
                             height_mm=contract.height_mm or fig.get_figheight()*25.4)
    dpi = cfg["dpi"]
    if dpi < cfg["minimum_dpi"]:
        raise ValueError(f"dpi must be at least {cfg['minimum_dpi']} for publication export")
    stem = Path(output_stem)
    if stem.suffix:
        raise ValueError("output_stem must not include a file extension")
    report = audit_publication_figure(fig, contract, config=cfg, source_root=source_root)
    if strict and not report.passed:
        raise ValueError("publication figure audit failed: " + "; ".join(report.errors))
    stem.parent.mkdir(parents=True, exist_ok=True)
    paths = {ext: str(stem.with_suffix('.'+ext)) for ext in ("pdf", "svg", "png")}
    paths["metadata"] = str(stem.with_suffix(".figure.json"))
    # Render and inspect the whole bundle before replacing any previous delivery.
    with tempfile.TemporaryDirectory(prefix=".figure-stage-", dir=stem.parent) as temp:
        staged = {key: Path(temp) / Path(value).name for key, value in paths.items()}
        with mpl.rc_context({"pdf.fonttype": 42, "svg.fonttype": "none",
                             "savefig.bbox": None, "savefig.transparent": False}):
            for extension in ("pdf", "svg", "png"):
                fig.savefig(staged[extension], format=extension, dpi=dpi,
                            bbox_inches=None, pad_inches=0, facecolor=cfg["background"],
                            transparent=False)
        with Image.open(staged["png"]) as im:
            rgb = im.convert("RGB")
        rgb.save(staged["png"], dpi=(dpi, dpi))
        width, height = fig.get_size_inches() * 25.4
        file_audit = inspect_exports(staged, width, height, dpi)
        # Backend-specific drawing can move display-space annotations. Restore
        # the canvas transform before saving numerical artist provenance.
        fig.canvas.draw()
        visual = {"status": "NOT_CHECKED", "png": "NOT_CHECKED", "vector": "NOT_CHECKED",
                  "physical_proof": "NOT_CHECKED", "grayscale": "NOT_CHECKED",
                  "source_values": "NOT_CHECKED"}
        payload = {
            "schema_version": 3, "contract": asdict(contract),
            "audit": report.to_dict(), "programmatic_audit": report.to_dict(),
            "visual_review": visual, "completion_status": "NEEDS_VISUAL_REVIEW" if report.passed else "FAIL",
            "configuration": cfg, "source_files": report.metrics["source_files"],
            "export": {"dpi": dpi, "formats": ["pdf", "svg", "png"], "bbox_inches": None},
            "file_audit": file_audit,
            "template": getattr(fig, "_template_metadata", None),
            "figure_metadata": getattr(fig, "_figure_metadata", None),
            "environment": {"python": platform.python_version(), "platform": platform.platform(),
                            "matplotlib": mpl.__version__, "numpy": np.__version__,
                            "backend": mpl.get_backend(),
                            "implementation_hashes": implementation_hashes()},
            "output_hashes": {key: hashlib.sha256(staged[key].read_bytes()).hexdigest()
                              for key in ("pdf", "svg", "png")},
        }
        staged["metadata"].write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        backups = {key: Path(path).read_bytes() if Path(path).exists() else None for key, path in paths.items()}
        replaced = []
        try:
            # Metadata is the completion marker and is committed last.
            for key, path in paths.items():
                staged[key].replace(path)
                replaced.append(key)
        except Exception:
            for key in reversed(replaced):
                path = Path(paths[key])
                if backups[key] is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(backups[key])
            raise
    if close:
        plt.close(fig)
    return paths


VISUAL_CHECKS = frozenset({"png", "vector", "physical_proof", "grayscale", "source_values"})


def _artifact_errors(path, payload, *, source_root=None):
    """Read-only integrity checks shared by recording and consuming a review."""
    errors = []
    hashes = payload.get("output_hashes", {})
    if not isinstance(hashes, dict) or set(hashes) != {"pdf", "svg", "png"}:
        errors.append("output_hashes must bind PDF, SVG and PNG")
        hashes = {}
    for ext, digest in hashes.items():
        artifact = path.with_name(path.name.removesuffix(".figure.json") + "." + ext)
        if not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest() != digest:
            errors.append("export changed since audit: " + str(artifact))
    sources = payload.get("source_files")
    if not isinstance(sources, list) or not sources:
        errors.append("source_files must bind the plotted sources")
        sources = []
    root = Path(source_root).resolve() if source_root is not None else Path.cwd()
    for source in sources:
        if not isinstance(source, dict) or not source.get("resolved_path", source.get("path")):
            errors.append("invalid source file record")
            continue
        artifact = Path(source.get("resolved_path") or source["path"])
        if not artifact.is_absolute():
            artifact = root / artifact
        if not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest() != source.get("sha256"):
            errors.append("source changed since audit: " + str(artifact))
    environment = payload.get("environment")
    saved = environment.get("implementation_hashes", {}) if isinstance(environment, dict) else {}
    current = implementation_hashes()
    if not isinstance(saved, dict) or set(saved) != set(current):
        errors.append("implementation changed since audit: module inventory differs or is missing")
        saved = saved if isinstance(saved, dict) else {}
    for name, digest in saved.items():
        if current.get(name) != digest:
            errors.append("implementation changed since audit: " + name)
    return errors


def validate_figure_review(metadata_path, *, source_root=None):
    """Return current review/integrity errors without changing any evidence.

    ``source_root`` resolves portable source paths independently of the caller's
    working directory. Legacy metadata stays readable but cannot establish a
    completed formal review without its five explicit checks and bindings.
    """
    path = Path(metadata_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        return [f"figure metadata unreadable: {path}: {exc}"]
    if not isinstance(payload, dict):
        return [f"figure metadata must be an object: {path}"]
    errors = _artifact_errors(path, payload, source_root=source_root)
    audit = payload.get("audit")
    programmatic = payload.get("programmatic_audit", audit)
    if not isinstance(audit, dict) or audit.get("passed") is not True:
        errors.append("figure programmatic audit did not pass")
    if not isinstance(programmatic, dict) or programmatic.get("passed") is not True:
        errors.append("figure programmatic_audit did not pass")
    if not isinstance(payload.get("file_audit"), dict) or payload["file_audit"].get("status") != "PASS":
        errors.append("figure file audit did not pass")
    review = payload.get("visual_review")
    if not isinstance(review, dict):
        review = {}
    for key in sorted(VISUAL_CHECKS):
        if review.get(key) != "PASS":
            errors.append(f"figure visual check {key} is not PASS: {review.get(key, 'NOT_CHECKED')}")
    if review.get("status") != "PASS" or payload.get("completion_status") != "PASS":
        errors.append("figure completion and visual review must both be PASS")
    if not review.get("reviewer") or review.get("output_hashes") != payload.get("output_hashes"):
        errors.append("figure review is not bound to the current exported outputs")
    regression = payload.get("numerical_regression")
    if regression is not None:
        accepted = {"PASS", "DOCUMENTED_LAYOUT_CHANGE", "DOCUMENTED_DISPLAY_CHANGE",
                    "DOCUMENTED_SEMANTIC_REPAIR", "DOCUMENTED_METADATA_CHANGE"}
        if not isinstance(regression, dict) or regression.get("status") not in accepted:
            errors.append("figure numerical comparison is not accepted")
        else:
            checks = regression.get("invariant_checks")
            evidence = regression.get("verification_evidence")
            if (not isinstance(checks, dict) or not checks or any(v is not True for v in checks.values())
                    or not isinstance(evidence, dict) or evidence.get("status") != "PASS"):
                errors.append("figure numerical comparison has no passing invariant evidence")
            elif isinstance(evidence, dict):
                source_hashes = {s.get("sha256") for s in payload.get("source_files", []) if isinstance(s, dict)}
                if evidence.get("source_sha256") not in source_hashes:
                    errors.append("figure numerical comparison does not bind the saved input")
                for field, value in (("artist_evidence", regression.get("artist_evidence")),
                                     ("figure_metadata", payload.get("figure_metadata"))):
                    digest = hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                                       separators=(",", ":")).encode("utf-8")).hexdigest()
                    if evidence.get(field + "_sha256") != digest:
                        errors.append("figure numerical comparison is stale: " + field)
                for label, binding in (("comparison_code", regression.get("comparison_code")),
                                       ("verifier_code", evidence.get("verifier_code")),
                                       ("artist_capture_code", evidence.get("artist_capture_code"))):
                    if not isinstance(binding, dict) or not binding.get("path"):
                        errors.append("figure numerical comparison lacks " + label)
                        continue
                    code_path = Path(binding["path"])
                    if not code_path.is_absolute():
                        code_path = (Path(source_root) if source_root is not None else Path.cwd()) / code_path
                    if not code_path.is_file() or hashlib.sha256(code_path.read_bytes()).hexdigest() != binding.get("sha256"):
                        errors.append("figure numerical comparison code changed: " + label)
    return errors


def record_visual_review(metadata_path, *, reviewer, checks, notes, source_root=None):
    """Record checks actually performed, binding the review to exported file hashes."""
    path = Path(metadata_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors = _artifact_errors(path, payload, source_root=source_root)
    if errors:
        raise ValueError("; ".join(errors))
    required = VISUAL_CHECKS
    if set(checks) != required or any(v not in {"PASS", "WARN", "FAIL", "NOT_CHECKED"} for v in checks.values()):
        raise ValueError("provide all five visual checks with explicit states")
    status = "FAIL" if "FAIL" in checks.values() else ("PASS" if all(v == "PASS" for v in checks.values()) else "NEEDS_REVIEW")
    payload["visual_review"] = {"status": status, **checks, "reviewer": reviewer, "notes": notes,
                                "output_hashes": payload["output_hashes"]}
    payload["completion_status"] = ("FAIL" if status == "FAIL" or not payload["audit"]["passed"] else
                                    "PASS" if status == "PASS" else "NEEDS_REVIEW")
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
