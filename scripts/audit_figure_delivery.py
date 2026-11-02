"""Audit generated bundles, compare actual PNG pixels, and package manifest files."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))

import fitz  # noqa: E402
from PIL import Image  # noqa: E402
from algorithms.figures import get_spec, list_figures  # noqa: E402


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(directory: Path, *, package=False):
    curated = (directory / "showcase_manifest.json").exists()
    manifest_path = directory / ("showcase_manifest.json" if curated else "preview_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entries = manifest["figures"]
    errors = [str(item) for item in manifest.get("errors", [])]
    if not curated and {item["name"] for item in entries} != set(list_figures()):
        errors.append("manifest must cover exactly the registry")
    hashes = defaultdict(list)
    warnings = {}
    approved_files = {manifest_path.name}
    formats = Counter()
    for item in entries:
        name = item["name"]
        try:
            files = item["files"]
            for field in ("png", "pdf", "svg", "metadata"):
                filename = files[field]
                if Path(filename).name != filename:
                    raise ValueError("manifest filenames must stay inside the bundle")
                path = directory / filename
                if not path.is_file() or path.stat().st_size == 0:
                    raise ValueError(f"missing or empty {field}")
                approved_files.add(filename)
                formats[field] += 1
            payload = json.loads((directory / files["metadata"]).read_text(encoding="utf-8"))
            if not payload["audit"]["passed"] or payload["file_audit"]["status"] != "PASS":
                raise ValueError("programmatic or file audit failed")
            notes = payload["audit"].get("warnings", [])
            if notes:
                warnings[name] = notes
            if any("glyph" in note.lower() or "font missing" in note.lower() for note in notes):
                raise ValueError("font audit reported missing glyphs")
            meta = payload["figure_metadata"]
            contract = meta.get("data_contract", {})
            for field in ("source", "simulated", "independent_unit", "units", "interval_kind"):
                if field not in contract:
                    raise ValueError(f"missing provenance field {field}")
            if contract["simulated"] is not True or meta.get("simulated") is not True:
                raise ValueError("preview must declare simulated=True")
            if contract["source"] != "synthetic":
                raise ValueError("preview source must be synthetic")
            if not contract["independent_unit"] or not isinstance(contract["units"], dict):
                raise ValueError("invalid independent_unit or units metadata")
            if meta.get("paper_suitable") is not False:
                raise ValueError("preview must not claim paper suitability")
            for field in ("png", "pdf", "svg"):
                if sha(directory / files[field]) != payload["output_hashes"][field]:
                    raise ValueError(f"{field} hash no longer matches metadata")
            with Image.open(directory / files["png"]) as image:
                rgb = image.convert("RGB")
                digest = hashlib.sha256(str(rgb.size).encode() + rgb.tobytes()).hexdigest()
                hashes[digest].append(name)
            with fitz.open(directory / files["pdf"]) as doc:
                if len(doc) != 1 or doc[0].rect.width <= 0:
                    raise ValueError("PDF must have a valid figure page")
            if not ET.parse(directory / files["svg"]).getroot().tag.endswith("svg"):
                raise ValueError("SVG has an invalid root")
        except (ValueError, KeyError, OSError, ET.ParseError) as exc:
            errors.append(f"{name}: {exc}")
    duplicates = [group for group in hashes.values() if len(group) > 1]
    illegal_duplicates = []
    for group in duplicates:
        canonical = {get_spec(name).to_dict().get("alias_of") or name for name in group} if not curated else set(group)
        if len(canonical) > 1:
            illegal_duplicates.append(group)
    errors.extend(f"non-alias identical pixels: {group}" for group in illegal_duplicates)
    result = {"directory": str(directory.resolve()), "status": "FAIL" if errors else "PASS",
              "registered": len(list_figures()), "figures": len(entries), "formats": dict(formats),
              "pixel_duplicate_groups": duplicates, "illegal_pixel_duplicate_groups": illegal_duplicates,
              "programmatic_warnings": warnings, "errors": errors,
              "visual_review": "NOT_CHECKED; see separate sample review, never inferred from programmatic PASS"}
    if package and not errors:
        extra_names = {"index.html", "qa-report.md", "README.md", "figure_catalog_zh.json",
                       "random_source_manifest.json", "synthetic_gallery_source.json", "contact_sheet.png"}
        approved_files.update(p.name for p in directory.iterdir() if p.is_file() and
                              (p.name in extra_names or p.name.startswith(("category_", "showcase_"))))
        archive = directory.with_suffix(".zip")
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
            for filename in sorted(approved_files):
                bundle.write(directory / filename, filename)
        result["zip"] = str(archive.resolve())
        result["zip_sha256"] = sha(archive)
        result["zip_files"] = len(approved_files)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", nargs="+", type=Path)
    parser.add_argument("--zip", action="store_true", dest="package")
    parser.add_argument("--report", type=Path, default=ROOT / "output/repair-round-3-delivery-audit.json")
    args = parser.parse_args()
    specs = [get_spec(name) for name in list_figures()]
    records = [audit(path, package=args.package) for path in args.directories]
    report = {"registry_count": len(specs), "implementation_levels": dict(Counter(s.implementation_level for s in specs)),
              "values_only": sum(s.required_fields == ("values",) for s in specs),
              "paper_suitable_true": sum(s.paper_suitable for s in specs),
              "figure_module_hashes": {str(p.relative_to(ROOT)): sha(p) for p in (ROOT / "code/algorithms/figures").glob("*.py")},
              "bundles": records}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps([{k: r[k] for k in ("directory", "status", "figures", "errors", "illegal_pixel_duplicate_groups")} for r in records], ensure_ascii=False))
    return int(any(r["status"] != "PASS" for r in records))


if __name__ == "__main__":
    raise SystemExit(main())
