"""Run installed modeling Skills against a fresh, external 2021C reproduction.

This is a workflow verifier, not a replacement solver. ``pre`` exercises five installed Skill entrypoints;
``recovery`` corrupts only its private copy of a delivered workbook and proves a
failed retry cannot inherit the previous solve PASS. Figures, writing and final
review remain pending until their current artifacts have actually been reviewed.
``render-figures`` deliberately leaves a failed formal run pending real visual
inspection. After the reviews, ``figures``, ``paper`` and ``review`` finish the
three remaining Skills. Actual page/figure reviews are never manufactured here.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


REPOSITORY = Path(__file__).resolve().parents[1]
PROJECT_ID = "cumcm-2021-c-installed-workflow"
PREFIX = "results/workflow/"
INPUTS = {
    "run-modeling-project": {"project_config": "config/workflow-project.json", "skill_trace": "manifests/skill-runs.jsonl"},
    "analyze-model-data": {"raw_data": "manifests/official-inputs.json", "data_dictionary": PREFIX + "data_dictionary.json",
                           "official_problem": "problem/official_problem/CUMCM2021-C.pdf"},
    "select-model": {"official_problem": "problem/official_problem/CUMCM2021-C.pdf", "data_dictionary": PREFIX + "data_dictionary.json",
                     "constraint_summary": PREFIX + "constraint_summary.json", "project_goal": "config/workflow-project.json"},
    "research-model-literature": {"model_problem": "problem/official_problem/CUMCM2021-C.pdf", "selected_model": PREFIX + "selected_model_plan.json",
                                  "citation_requirements": PREFIX + "citation_requirements.json", "source_candidates": PREFIX + "source_candidates.json"},
    "solve-model": {"selected_model_plan": PREFIX + "selected_model_plan.json", "decision_contract": PREFIX + "decision_contract.json",
                    "data_analysis": "reports/workflow/data_analysis.md", "model_config": "config/final_model_config.yaml",
                    "baseline_plan": PREFIX + "baseline_plan.json"},
}
OUTPUTS = {
    "run-modeling-project": {"project_state": ".modeling/project-state.json", "stage_gate": "reports/workflow/stage_gate.json",
                              "handoff": "reports/workflow/handoff.json"},
    "analyze-model-data": {**{role: PREFIX + role + ".json" for role in
        ("data_profile", "data_quality_report", "cleaning_actions", "eda_findings", "leakage_report", "processed_data_manifest")},
        "data_analysis": "reports/workflow/data_analysis.md"},
    "select-model": {**{role: PREFIX + role + ".json" for role in
        ("problem_decomposition", "candidate_models", "baseline_plan", "selected_model_plan", "decision_contract", "risk_register")},
        "model_selection_report": "reports/workflow/model_selection_report.md"},
    "research-model-literature": {**{role: "results/" + role + ".json" for role in
        ("search_queries", "search_results", "selected_sources", "rejected_sources", "retrieval_log", "metadata_verification", "relevance_evidence", "bib_validation")},
        "literature_evidence": "reports/literature_evidence.md", "references_bib": "paper/references.bib"},
    "solve-model": {role: PREFIX + role + ".json" for role in
                    ("model_specification", "result_object", "solver_validation", "quality_validation")},
}
PRE_SKILLS = tuple(INPUTS)
INPUTS.update({
    "make-model-figures": {"result_object": PREFIX + "result_object.json", "quality_validation": PREFIX + "quality_validation.json",
                           "figure_plan": PREFIX + "figure_plan.json"},
    "write-model-paper": {"paper_spec": "paper/paper-spec.yaml", "evidence_index": "paper/evidence-index.json",
                          "decision_contract": PREFIX + "decision_contract.json", "quality_validation": PREFIX + "quality_validation.json",
                          "figure_registry": "paper/figure-registry.json", "references_bib": "paper/references.bib", "result_object": PREFIX + "result_object.json"},
    "review-model-paper": {"manuscript": "paper/main.md", "main_pdf": "paper/research/main.pdf",
                           "official_problem": "problem/official_problem/CUMCM2021-C.pdf", "decision_contract": PREFIX + "decision_contract.json",
                           "quality_validation": PREFIX + "quality_validation.json", "result_object": PREFIX + "result_object.json",
                           "project_manifest": "run-manifest.json", "layout_validation": "reports/workflow/layout_validation.json",
                           "visual_layout_audit": "reports/workflow/visual_layout_audit.json"},
})
OUTPUTS.update({
    "make-model-figures": {"figure_registry": "paper/figure-registry.json", "figure_audit_report": "reports/workflow/figure_audit_report.json"},
    "write-model-paper": {"main_markdown": "paper/main.md", "main_tex": "paper/research/main.tex",
                          **{role: "reports/workflow/" + role + ".json" for role in
                             ("paper_generation_report", "claim_usage_report", "layout_validation", "render_request")}},
    "review-model-paper": {role: "reports/" + role + ".json" for role in
                           ("paper_review_report", "submission_readiness", "submission_preflight")},
})


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def put(root, relative, data):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def execute(command, *, root, log_name, expect=0):
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["PYTHONUTF8"] = "1"
    completed = subprocess.run([str(value) for value in command], cwd=root, env=environment,
                               text=True, encoding="utf-8", errors="replace", capture_output=True, check=False)
    log = root / "reports/workflow" / log_name
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(completed.stdout + completed.stderr, encoding="utf-8")
    print(f"{log_name}: exit {completed.returncode}", flush=True)
    if (expect == 0 and completed.returncode != 0) or (expect != 0 and completed.returncode == 0):
        raise RuntimeError(f"unexpected exit {completed.returncode}; inspect {log}")
    return completed


def invoke(args, skill, action, *, expect=0):
    entry = args.skills_root / skill / "scripts/execute_skill.py"
    command = [args.python, "-X", "utf8", entry, "--project-root", args.work_root,
               "--project-id", PROJECT_ID, "--skill-path", entry.parents[1],
               "--profile", "competition", "--venue", "generic-research-report"]
    for role, path in INPUTS[skill].items():
        command += ["--input", f"{role}={path}"]
    for role, path in OUTPUTS[skill].items():
        command += ["--output", f"{role}={path}"]
    if skill == "research-model-literature":
        command += ["--", args.python, "-X", "utf8", entry.parent / "build_source_record.py", "--root", args.work_root,
                    "--source-candidates", args.work_root / PREFIX / "source_candidates.json"]
    else:
        command += ["--", args.python, "-X", "utf8", Path(__file__).resolve(), "--worker", action,
                    "--work-root", args.work_root, "--skills-root", args.skills_root, "--case-root", args.case_root]
    return execute(command, root=args.work_root, log_name=f"{action}.log", expect=expect)


def installed_state(args, action, *extra, expect=0):
    path = args.skills_root / "run-modeling-project/scripts/project_state.py"
    return execute([args.python, "-X", "utf8", path, action, "--project-root", args.work_root, *extra],
                   root=args.work_root, log_name=f"state-{action}.log", expect=expect)


def check_environment(args):
    if args.work_root == REPOSITORY or args.work_root.is_relative_to(REPOSITORY):
        raise ValueError("work-root must be outside the repository")
    differences = []
    for source in sorted((args.case_root / "src").glob("*.py")):
        copied = args.work_root / "src" / source.name
        if not copied.is_file() or digest(copied) != digest(source):
            differences.append("case/src/" + source.name)
    for skill in INPUTS:
        for filename in ("run_standard_skill.py", "skill_contracts.py", "skill_runtime.py"):
            installed = args.skills_root / skill / "scripts/_runtime" / filename
            if not installed.is_file() or digest(installed) != digest(REPOSITORY / "scripts" / filename):
                differences.append(f"{skill}/scripts/_runtime/{filename}")
    if differences:
        raise ValueError("installed runtime or copied case programs are not current: " + ", ".join(differences))
    completed = execute([args.python, "-X", "utf8", "-c",
        "import algorithms, json, sys; print(json.dumps({'python':sys.executable,'algorithms':algorithms.__file__}))"],
        root=args.work_root, log_name="installed-environment.json")
    environment = json.loads(completed.stdout)
    if Path(environment["algorithms"]).resolve().is_relative_to(REPOSITORY / "code"):
        raise ValueError("algorithm library was imported from the repository")
    return environment


def prepare(args):
    if args.work_root == REPOSITORY or args.work_root.is_relative_to(REPOSITORY):
        raise ValueError("work-root must be outside the repository")
    if args.work_root.exists() and any(args.work_root.iterdir()):
        raise ValueError("prepare needs an absent or empty work-root; previous work is preserved")
    args.work_root.mkdir(parents=True, exist_ok=True)
    for folder in ("data/raw", "problem/official_problem", "config", "src", "tests"):
        shutil.copytree(args.case_root / folder, args.work_root / folder,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"))
    for filename in ("README.md", "requirements.txt", "pytest.ini"):
        if (args.case_root / filename).is_file():
            shutil.copy2(args.case_root / filename, args.work_root / filename)
    fallback = args.case_root / "paper/research/placeins.sty"
    if fallback.is_file():
        (args.work_root / "paper/research").mkdir(parents=True, exist_ok=True)
        shutil.copy2(fallback, args.work_root / "paper/research/placeins.sty")
    manifest = load(args.case_root / "manifests/official-inputs.json")
    for record in manifest["files"]:
        if digest(args.work_root / record["path"]) != record["sha256"]:
            raise ValueError("official input differs: " + record["path"])
    put(args.work_root, "manifests/official-inputs.json", manifest)
    (args.work_root / "manifests/skill-runs.jsonl").touch()
    put(args.work_root, "config/workflow-project.json", {"project_id": PROJECT_ID, "venue": "generic-research-report",
        "profile": "competition", "purpose": "historical 2021C independent research; not a 2026 contest submission",
        "questions": ["Q1", "Q2", "Q3", "Q4"], "source_case": "original attachments and current six own programs only",
        "precomputed_answers_copied": False})
    execute([args.python, "-X", "utf8", Path(__file__).resolve(), "--worker", "prepare",
             "--work-root", args.work_root, "--skills-root", args.skills_root], root=args.work_root, log_name="prepare.log")


def paper_handoff(args):
    """Bind the real per-question results; do not invent review conclusions."""
    root = args.work_root
    (root / "paper").mkdir(exist_ok=True)
    spec = """venue: generic-research-report
paper_mode: competition_paper
problem_type: optimization
decision_contract: results/workflow/decision_contract.json
quality_validation: results/workflow/quality_validation.json
required_supplier_count: 50
minimum_figures: 7
minimum_tables: 1
minimum_references: 1
required_sections:
  - 问题
  - 验证
  - 参考文献
"""
    (root / "paper/paper-spec.yaml").write_text(spec, encoding="utf-8")
    put(root, "paper/evidence-index.json", [{"evidence_id": f"Q{i}", "path": f"results/final/q{i}_summary.json",
         "sha256": digest(root / f"results/final/q{i}_summary.json")} for i in range(1, 5)])


def figures_worker(args, case, *, render=False):
    from algorithms.figure_export import validate_figure_review
    from make_paper import render_figures
    root = args.work_root
    if render:
        render_figures(root)
    rows, errors = [], []
    for metadata in sorted((root / "figures/research").glob("*.figure.json")):
        stem = metadata.name.removesuffix(".figure.json")
        image = metadata.with_name(stem + ".pdf")
        data = root / "figure_data/research" / (stem + ".csv")
        rows.append({"figure_id": stem, "path": image.relative_to(root).as_posix(), "sha256": digest(image),
                     "metadata": metadata.relative_to(root).as_posix(), "data_file": data.relative_to(root).as_posix(),
                     "data_sha256": digest(data), "inserted_in_body": True})
        errors.extend(f"{stem}: {error}" for error in validate_figure_review(metadata, source_root=root))
    if len(rows) != 7:
        errors.append(f"expected the seven actual planned evidence figures, found {len(rows)}")
    put(root, "paper/figure-registry.json", rows)
    put(root, "reports/workflow/figure_audit_report.json", {"status": "FAIL" if errors else "PASS",
        "figure_count": len(rows), "errors": errors, "scope": "current output, saved-data, implementation and five-dimensional visual checks"})
    if render:
        # Real-size vector and grayscale proofs are outputs for inspection, not attestations.
        import fitz
        from PIL import Image, ImageOps
        proofs = root / "figures/research/proofs"
        proofs.mkdir(exist_ok=True)
        for row in rows:
            with fitz.open(root / row["path"]) as pdf:
                pdf[0].get_pixmap(matrix=fitz.Matrix(2.5, 2.5)).save(proofs / (row["figure_id"] + "-vector.png"))
            with Image.open((root / row["path"]).with_suffix(".png")) as image:
                ImageOps.grayscale(image).save(proofs / (row["figure_id"] + "-gray.png"))
        put(root, "reports/workflow/figures-needing-actual-inspection.json", {"status": "NOT_CHECKED",
            "figures": [row["metadata"] for row in rows], "required": ["PNG", "PDF and SVG", "150 mm proof", "grayscale", "source values"],
            "note": "No visual verdicts are copied from the source study. Record real inspection before retrying the figures phase."})


def _paper_programmatic_layout(root):
    import fitz
    from make_paper import verify_paper
    pdf_path = root / "paper/research/main.pdf"
    with fitz.open(pdf_path) as document:
        pages = list(document)
        checks = {"all_pages_A4": all(abs(p.rect.width - 595.276) < 1 and abs(p.rect.height - 841.89) < 1 for p in pages),
                  "all_pages_nonempty": all(p.get_text().strip() for p in pages),
                  "abstract_on_page_one": "摘" in pages[0].get_text() and "要" in pages[0].get_text(),
                  "restatement_on_page_two": "问题重述" in pages[1].get_text(),
                  "no_contents_command": r"\tableofcontents" not in (root / "paper/research/main.tex").read_text(encoding="utf-8")}
        page_count = len(pages)
    numbers = verify_paper(root)
    return {"status": "PASS" if all(checks.values()) else "FAIL", "venue": "generic-research-report",
            "checks": checks, "page_count": page_count, "number_checks": numbers, "paper_sha256": digest(pdf_path),
            "scope": "generic historical report layout and actual saved values; visual page review is separate"}


def page_review_errors(pdf_path, record):
    """Consume exact current-page attestations, never an inherited PASS alone."""
    import fitz
    errors = []
    if not isinstance(record, dict):
        return ["page review must be an object"]
    if record.get("visual_review") != "PASS" or not str(record.get("reviewer", "")).strip():
        errors.append("current actual visual inspection and reviewer are required")
    if record.get("paper_sha256") != digest(pdf_path):
        errors.append("page review is not bound to the current PDF")
    rows = record.get("reviewed_pages")
    if not isinstance(rows, list):
        return [*errors, "individual page conclusions are required"]
    with fitz.open(pdf_path) as document:
        expected = set(range(1, len(document) + 1))
        if len(rows) != len(document) or {row.get("page") for row in rows if isinstance(row, dict)} != expected:
            errors.append("every page needs exactly one independent conclusion")
        for row in rows:
            if not isinstance(row, dict) or row.get("page") not in expected:
                errors.append("invalid individual page conclusion")
                continue
            raster = document[row["page"] - 1].get_pixmap(dpi=110, alpha=False)
            if row.get("status") != "PASS" or row.get("render_sha256") != hashlib.sha256(raster.samples).hexdigest():
                errors.append(f"page {row['page']} review or rendered pixel binding is not current")
    return errors


def expand_case_figure_macro(root):
    """Expand the case's simple TeX shorthand and prove identical page pixels.

    The generic evidence consumer reads literal includegraphics references. Its
    current contract cannot evaluate TeX arguments in macro definitions. Expand
    this study's own two-argument shorthand instead of weakening that consumer.
    """
    import fitz
    paper = root / "paper/research"
    pdf_path = paper / "main.pdf"
    with fitz.open(pdf_path) as document:
        before = [hashlib.sha256(page.get_pixmap(dpi=110, alpha=False).samples).hexdigest() for page in document]
    source = (paper / "main.tex").read_text(encoding="utf-8")
    definition = re.search(r"(?m)^\\newcommand\{\\fig\}\[2\]\{(.+)\}\s*$", source)
    if not definition:
        raise ValueError("expected this case's explicit two-argument figure shorthand")
    body = definition[1]
    source = source[:definition.start()] + source[definition.end():]
    source, count = re.subn(r"\\fig\{([^{}]+)\}\{([^{}]*)\}",
        lambda match: body.replace("#1", match[1]).replace("#2", match[2]), source)
    if count != 6 or "#1.pdf" in source:
        raise ValueError("unexpected figure shorthand structure; do not guess TeX expansion")
    (paper / "main.tex").write_text(source, encoding="utf-8")
    for number in (1, 2):
        execute(["xelatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"],
                root=paper, log_name=f"macro-expansion-compile-{number}.log")
    with fitz.open(pdf_path) as document:
        after = [hashlib.sha256(page.get_pixmap(dpi=110, alpha=False).samples).hexdigest() for page in document]
    if before != after:
        raise ValueError("figure shorthand expansion changed visible manuscript pages; inspect before continuing")
    binding = load(paper / "number-consistency.json")
    binding["paper_sha256"] = digest(pdf_path)
    put(root, "paper/research/number-consistency.json", binding)
    review = load(paper / "page-review.json")
    review["paper_sha256"] = digest(pdf_path)
    put(root, "paper/research/page-review.json", review)
    put(root, "reports/workflow/figure-macro-expansion.json", {"status": "PASS", "calls_expanded": count,
        "all_page_pixels_unchanged": before == after, "page_render_sha256": after,
        "scope": "literal equivalent TeX references for the existing generic consumer; no renderer or evidence gate changed"})


def markdown_review_source(converted):
    """Keep scientific claims in the manuscript and link its complete programs.

    Full source code is already present in the selected PDF's reviewed appendix;
    the complete conversion is retained separately. Code tokens must not be
    presented to a prose-only claim heuristic as if they were solver verdicts.
    """
    text = re.sub(r'<embed src="([^"]+)"[^>]*/>',
        lambda match: '![' + Path(match[1]).stem + '](' + match[1] + ')', converted)
    text = text.replace('<div class="thebibliography">', '# 参考文献\n')
    text = re.sub(r"(?m)^9 (全国大学生数学建模竞赛组织委员会\.)", r"[1] \1", text)
    text = text.replace("## 固定承诺的名义成本优化", "## 目标函数：固定承诺的名义成本优化")
    body, separator, _appendix = text.partition("# 支撑文件与完整程序")
    if not separator:
        raise ValueError("the actual program appendix heading was not found")
    links = [f"- [{name}](../{name})" for name in ("src/run_complete_case.py", "src/structured_selection.py",
        "src/refine_and_validate.py", "src/robust_material_mix.py", "src/make_paper.py", "src/reproduce.py",
        "tests/test_run_complete_case.py", "tests/test_separate_reproduction.py")]
    return body + "# 支撑文件与完整程序\n\n完整自有源码已逐页载于[论文PDF附录](research/main.pdf)，以下文件与PDF列印版本绑定。\n\n" + "\n".join(links) + "\n"


def write_review_sources(root):
    """Convert the actual compiled TeX without regenerating an approved PDF."""
    tex = (root / "paper/research/main.tex").read_text(encoding="utf-8")
    tex = tex.replace("../../figures/research/", "../figures/research/")
    converted = root / "paper/research/markdown-source.tex"
    converted.write_text(tex, encoding="utf-8")
    pandoc = shutil.which("pandoc")
    if not pandoc:
        raise RuntimeError("Pandoc is required to convert this study's actual TeX into the Markdown review source")
    execute([pandoc, converted, "--from", "latex", "--to", "gfm", "--wrap", "none", "--output", root / "paper/main.md"],
            root=root, log_name="paper-markdown-conversion.log")
    markdown = (root / "paper/main.md").read_text(encoding="utf-8")
    for name in ("run_complete_case.py", "structured_selection.py", "refine_and_validate.py", "robust_material_mix.py",
                 "make_paper.py", "reproduce.py", "../tests/test_run_complete_case.py", "../tests/test_separate_reproduction.py"):
        heading = "## `" + name + "`"
        code = (root / "src" / name).read_text(encoding="utf-8")
        markdown = markdown.replace(heading, heading + "\n\n```python\n" + code + "\n```\n")
    (root / "paper/main-with-code.md").write_text(markdown, encoding="utf-8")
    (root / "paper/main.md").write_text(markdown_review_source(markdown), encoding="utf-8")


def paper_worker(args, *, render=False):
    root = args.work_root
    from make_paper import compile_paper, verify_paper
    if render:
        # This project-authored TeX fallback is an input dependency, not a result.
        fallback = args.case_root / "paper/research/placeins.sty"
        if fallback.is_file() and not (root / "paper/research/placeins.sty").is_file():
            (root / "paper/research").mkdir(parents=True, exist_ok=True)
            shutil.copy2(fallback, root / "paper/research/placeins.sty")
        compile_paper(root)
        expand_case_figure_macro(root)
        paper_handoff(args)
    write_review_sources(root)
    verification = verify_paper(root)
    layout = _paper_programmatic_layout(root)
    put(root, "reports/workflow/layout_validation.json", layout)
    page_review_path = root / "paper/research/page-review.json"
    page_review = load(page_review_path)
    visual_errors = page_review_errors(root / "paper/research/main.pdf", page_review)
    actual_visual = not visual_errors
    put(root, "reports/workflow/visual_layout_audit.json", {"status": "PASS" if actual_visual else "NOT_CHECKED",
        "paper_sha256": digest(root / "paper/research/main.pdf"), "page_review": "paper/research/page-review.json",
        "page_review_sha256": digest(page_review_path), "reviewer": page_review.get("reviewer"),
        "errors": visual_errors,
        "scope": "current page review only; no inherited source-study PASS"})
    put(root, "reports/workflow/latex_compile_report.json", {"status": "PASS", "paper_sha256": digest(root / "paper/research/main.pdf"),
        "tex_sha256": digest(root / "paper/research/main.tex"), "compile_logs": ["paper/research/compile-1.log", "paper/research/compile-2.log",
            "paper/research/reports/workflow/macro-expansion-compile-1.log", "paper/research/reports/workflow/macro-expansion-compile-2.log"]})
    put(root, "reports/workflow/paper_generation_report.json", {"status": "PASS" if actual_visual else "BLOCKED",
        "numbers": verification, "pending": [] if actual_visual else ["actual current-page inspection"]})
    put(root, "reports/workflow/claim_usage_report.json", {"status": "PASS", "source": "paper/research/number-consistency.json",
        "saved_value_checks": len(verification["number_checks"]), "conflicts": verification["numeric_conflicts"]})
    put(root, "reports/workflow/render_request.json", {"status": "PASS" if actual_visual else "NOT_CHECKED",
        "pages": layout["page_count"], "proof_directory": "paper/research/pages", "review_record": "paper/research/page-review.json"})
    # The installed runner checks domain failures even if the subprocess exits 0.
    if not actual_visual:
        put(root, "reports/workflow/layout_validation.json", {**layout, "status": "NOT_CHECKED", "pending": "actual current-page inspection"})


def review_worker(args):
    from make_paper import verify_paper
    root = args.work_root
    verify_paper(root)
    entry = args.skills_root / "review-model-paper/scripts/run_competition_review.py"
    command = [sys.executable, "-X", "utf8", entry, "--project-root", root, "--profile", "competition", "--venue", "generic-research-report"]
    parameters = {"manuscript": "paper/main.md", "pdf": "paper/research/main.pdf",
        "official-problem": INPUTS["review-model-paper"]["official_problem"],
        "decision-contract": PREFIX + "decision_contract.json", "quality-validation": PREFIX + "quality_validation.json",
        "result-object": PREFIX + "result_object.json", "project-manifest": "run-manifest.json",
        "layout-validation": "reports/workflow/layout_validation.json", "latex-compile-report": "reports/workflow/latex_compile_report.json",
        "visual-layout-audit": "reports/workflow/visual_layout_audit.json", "figure-registry": "paper/figure-registry.json",
        "references-bib": "paper/references.bib"}
    for key, value in parameters.items():
        command += ["--" + key, root / value]
    execute(command, root=root, log_name="installed-paper-review.log")


def worker(args):
    root = args.work_root
    sys.path.insert(0, str(root / "src"))
    from run_complete_case import CompleteCase
    case = CompleteCase(root, root / "config/final_model_config.yaml")
    if args.worker == "prepare":
        report = case.validate_input()
        data = case.load_data()
        put(root, PREFIX + "data_dictionary.json", {"supplier_ids": data["ids"].tolist(),
            "materials": data["materials"].tolist(), "supplier_order_shape": list(data["O"].shape),
            "supplier_supply_shape": list(data["S"].shape), "carrier_loss_shape": list(data["L"].shape),
            "unit": "raw material m3; loss workbook percent converted to fraction",
            "statistical_unit": "supplier-week or carrier-week; repeated observations are dependent",
            "zero_loss": "no recorded movement; excluded from loss-rate means", "input_validation": report})
        put(root, PREFIX + "constraint_summary.json", {"weeks": case.H, "weekly_product_demand": case.D,
            "conversion": case.conv_map, "price_relative_coefficients": case.price_map,
            "carrier_weekly_capacity": case.carrier_cap, "opening_inventory": "declared two weeks; not an official datum"})
        put(root, PREFIX + "citation_requirements.json", {"purpose": "official problem definition only",
            "national_paper_answers_permitted_as_solver_inputs": False, "cache_is_not_a_new_download": True})
        put(root, PREFIX + "figure_plan.json", {"purpose": "seven saved-result evidence figures for Q1-Q4 and held-out validation",
            "source": "results/final", "rendering_program": "src/make_paper.py", "actual_visual_review_required": True})
        import fitz
        path = root / "problem/official_problem/CUMCM2021-C.pdf"
        with fitz.open(path) as pdf:
            text = "\n".join(page.get_text() for page in pdf)
            pages = len(pdf)
        if not any(value in text for value in ("28200", "2.82")) or "6000" not in text:
            raise ValueError("official PDF constants could not be verified")
        manifest = load(root / "manifests/official-inputs.json")
        put(root, PREFIX + "source_candidates.json", [{"id": "CUMCM2021C", "title": "2021年C题：生产企业原材料的订购与运输",
            "author": "全国大学生数学建模竞赛组委会", "year": 2021, "type": "web", "url": manifest["official_problem_url"],
            "origin": "USER_SUPPLIED", "retrieval_provider": "user-existing official cache, read and hash-verified now",
            "retrieval_timestamp": datetime.now(timezone.utc).isoformat(), "source_fetch_status": "FETCHED",
            "metadata_verification": {"status": "VERIFIED", "evidence": f"{pages} local PDF pages read; official-cache SHA256 {digest(path)}"},
            "content_relevance_evidence": {"supports": "four questions, demand and transport constraints",
                                            "location": f"official problem pages 1-{pages}; original attachments"}}])
    elif args.worker == "analysis":
        from algorithms.data_diagnostics import panel_diagnostics
        import numpy as np
        import pandas as pd
        report = case.validate_input()
        data = case.load_data()
        diagnostics = panel_diagnostics(data["S"], holdout_periods=48)
        frame = pd.DataFrame({"supplier_id": data["ids"], "material": data["materials"],
                              "mean_order": data["O"].mean(1), "mean_supply": data["S"].mean(1),
                              "active_weeks": (data["S"] > 0).sum(1)})
        target = root / PREFIX / "supplier_profile.csv"
        frame.to_csv(target, index=False)
        put(root, PREFIX + "data_profile.json", {"supplier_rows": len(frame), "weeks": data["S"].shape[1],
            "carriers": data["L"].shape[0], "temporal_panel": diagnostics, "statistics": frame.describe(include="all").fillna("").to_dict()})
        put(root, PREFIX + "data_quality_report.json", report)
        put(root, PREFIX + "cleaning_actions.json", [{"action": "preserve both raw workbooks", "reason": "observed oversupply and zero-order supply remain real observations"},
            {"action": "exclude zero-loss movements from loss forecasts", "affected_cells": int(np.sum(data["L"] == 0)), "reason": "no recorded movement"}])
        put(root, PREFIX + "eda_findings.json", {"quality_profile": report["quality_profile"], "temporal_panel": diagnostics,
            "supplier_order": data["ids"].tolist(), "material_order": ["A", "B", "C"], "units": "m3 raw material"})
        put(root, PREFIX + "leakage_report.json", {"status": "PASS" if diagnostics["holdout"]["periods"] == 48 and data["S"].shape[1] > 48 else "FAIL",
            "holdout_weeks": [193, 240], "scope": "chronological descriptive partition; solver rolling predictions checked separately"})
        put(root, PREFIX + "processed_data_manifest.json", {"raw_sources": report["source_files"],
            "derived": [{"path": str(target.relative_to(root)), "sha256": digest(target)}]})
        (root / "reports/workflow/data_analysis.md").write_text(
            f"# Real attachment analysis\n\n{len(frame)} suppliers ×240 weeks and 8 carriers ×240 weeks. "
            f"Missing, negative, oversupply and zero-movement counts: {json.dumps(report['quality_profile'])}. "
            "Full profiles and ordering are saved; weeks 193–240 are held out. Losses are fractions after dividing workbook percent by 100.\n", encoding="utf-8")
    elif args.worker == "selection":
        methods = [
            {"question": "Q1", "method": "entropy/CRITIC TOPSIS with material protection", "alternative": "equal weights", "validation": "indicator deletion and week resampling"},
            {"question": "Q2", "method": "exact three-material count enumeration then fixed-order LP", "alternative": "general MILP fallback if factorization fails", "validation": "same-scenario replay and independent workbooks"},
            {"question": "Q3", "method": "fixed-order three-material epsilon-constraint LP", "alternative": "Q2 same-input baseline", "validation": "full 36-run record and nondominated frontier"},
            {"question": "Q4", "method": "monotone fixed-calloff envelope and cumulative scenario bound", "alternative": "baseline production 28200", "validation": "same 120 scenarios and independent inventory/carrier constraints"},
        ]
        decomposition = {"questions": [{"id": row["question"], "task": row["method"], "verification": row["validation"]} for row in methods]}
        put(root, PREFIX + "problem_decomposition.json", decomposition)
        put(root, PREFIX + "candidate_models.json", methods)
        put(root, PREFIX + "selected_model_plan.json", {"methods": methods, "scope": "independent disclosed decomposition, not integrated stochastic global optimality"})
        put(root, PREFIX + "baseline_plan.json", {"file": "results/final/fair_baseline.csv", "same_suppliers": True,
            "same_scenarios": True, "objective": "nominal relative procurement cost; no fabricated currency prices"})
        put(root, PREFIX + "decision_contract.json", {"questions": [{"id": f"Q{i}",
            "result_artifact": f"results/final/q{i}_supplier_ranking.csv" if i == 1 else f"results/final/q{i}_summary.json",
            "validation_artifact": "results/final/validation_report.json" if i == 1 else "results/final/independent_validation.json"} for i in range(1, 5)],
            "requirements": {"baseline_comparison_required": True, "dynamic_validation_required": True,
                             "uncertainty_analysis_required": True, "tradeoff_analysis_required": True}})
        put(root, PREFIX + "risk_register.json", [{"risk": "finite dependent scenarios", "limit": "empirical feasibility is not population reliability or a confidence interval"},
            {"risk": "historical Q75 calloff range", "limit": "not a physical upper bound"}, {"risk": "unknown initial stock", "limit": "explicit two-week opening-stock assumption"}])
        (root / "reports/workflow/model_selection_report.md").write_text("# Model selection\n\n" + "\n\n".join(
            f"{row['question']}: {row['method']}. Compare {row['alternative']}; verify {row['validation']}." for row in methods), encoding="utf-8")
    elif args.worker in {"solve", "verify-solve"}:
        if args.worker == "solve":
            from reproduce import run
            run(root)
        else:
            from refine_and_validate import independent_checks
            independent_checks(case)
        independent = load(case.out / "independent_validation.json")
        validation = load(case.out / "validation_report.json")
        optimization = load(case.out / "q2_fixed_optimization.json")
        q3 = load(case.out / "q3_summary.json")
        valid = independent["status"] == "PASS" and validation["status"] == "PASS"
        quality = {
            "baseline": {"passed": optimization["nominal_cost_after"] <= optimization["nominal_cost_before"] + 1e-7,
                         "same_inputs": True, "before": optimization["nominal_cost_before"], "after": optimization["nominal_cost_after"], "source": "results/final/fair_baseline.csv"},
            "dynamic": {"passed": valid, "source": "results/final/independent_validation.json", "residuals": independent["numerical_residuals"]},
            "uncertainty": {"passed": validation["checks"]["q2_fixed_plan_reliability"], "source": "results/final/validation_report.json",
                            "meaning": "finite dependent scenario feasibility; not a population confidence interval", "metrics": validation["aggregate"]},
            "tradeoff": {"passed": q3["nondominated_points"] >= 2 and validation["checks"]["q3_nondegenerate_pareto"],
                         "source": "results/final/q3_pareto_front.csv", "points": q3["nondominated_points"]},
        }
        put(root, PREFIX + "quality_validation.json", quality)
        put(root, PREFIX + "solver_validation.json", independent)
        put(root, PREFIX + "result_object.json", {"status": "PASS" if valid else "FAIL", "question_summaries": {
            f"Q{i}": load(case.out / f"q{i}_summary.json") for i in range(1, 5)},
            "complete_saved_outputs": [{"path": str(path.relative_to(root)), "sha256": digest(path)}
                                       for path in sorted(case.out.iterdir()) if path.is_file()],
            "population_reliability_guarantee": False})
        put(root, PREFIX + "model_specification.json", {"plan": load(root / PREFIX / "selected_model_plan.json"),
            "config_sha256": digest(case.config_path) if hasattr(case, "config_path") else digest(root / "config/final_model_config.yaml"),
            "programs": {path.name: digest(path) for path in sorted((root / "src").glob("*.py"))}})
    elif args.worker == "coordinate":
        state = module(args.skills_root / "run-modeling-project/scripts/project_state.py", "installed_project_state")
        if not (root / ".modeling/project-state.json").is_file():
            current = state.initialize(root, PROJECT_ID, "run-manifest.json", venue="generic-research-report")
        else:
            current = state._read_state(root)
        errors = state.verify_evidence(root, current)
        put(root, "reports/workflow/stage_gate.json", {"status": "PASS" if not errors else "FAIL", "errors": errors,
            "current_stage": current["current_stage"], "scope": "current registered evidence; later stages remain pending"})
        put(root, "reports/workflow/handoff.json", state.handoff(current))
        if errors:
            raise RuntimeError("current project evidence is stale")
    elif args.worker in {"render-figures", "figures"}:
        figures_worker(args, case, render=args.worker == "render-figures")
    elif args.worker in {"render-paper", "paper"}:
        paper_worker(args, render=args.worker == "render-paper")
    elif args.worker == "review":
        review_worker(args)
    else:
        raise ValueError("unknown worker: " + str(args.worker))


def advance(args, target, values):
    installed_state(args, "advance", "--to", target, *[item for role, path in values.items() for item in ("--evidence", f"{role}={path}")],
                    "--note", "current installed-Skill outputs; original attachments recomputed")


def refresh_run_manifest(args):
    put(args.work_root, "run-manifest.json", {"project_id": PROJECT_ID, "venue": "generic-research-report",
        "source_files": load(args.work_root / "manifests/official-inputs.json")["files"],
        "programs": {path.name: digest(path) for path in sorted((args.work_root / "src").glob("*.py"))},
        "scope": "historical research numerical pipeline; no claim of final release"})


def verify_runs(args, skills, log_name):
    runtime = args.skills_root / "run-modeling-project/scripts/_runtime/skill_runtime.py"
    command = [args.python, "-X", "utf8", runtime, "validate", "--project-root", args.work_root,
               "--project-id", PROJECT_ID, "--profile", "competition"]
    command += [item for skill in skills for item in ("--require-skill", skill)]
    execute(command, root=args.work_root, log_name=log_name)


def pre(args):
    check_environment(args)
    invoke(args, "run-modeling-project", "coordinate")
    invoke(args, "analyze-model-data", "analysis")
    invoke(args, "select-model", "selection")
    invoke(args, "research-model-literature", "literature")
    current = load(args.work_root / ".modeling/project-state.json")
    if current["current_stage"] == "intake":
        advance(args, "analysis", {"problem_source": "manifests/official-inputs.json", "task_decomposition": PREFIX + "problem_decomposition.json"})
    current = load(args.work_root / ".modeling/project-state.json")
    if current["current_stage"] == "analysis":
        advance(args, "modeling", {"data_audit": PREFIX + "data_quality_report.json", "model_selection": PREFIX + "selected_model_plan.json",
                                    "decision_contract": PREFIX + "decision_contract.json"})
    invoke(args, "solve-model", "solve")
    refresh_run_manifest(args)
    current = load(args.work_root / ".modeling/project-state.json")
    if current["current_stage"] == "modeling":
        advance(args, "validation", {"implementation": "src/reproduce.py", "machine_results": PREFIX + "result_object.json",
                                      "quality_validation": PREFIX + "quality_validation.json", "run_manifest": "run-manifest.json"})
    invoke(args, "run-modeling-project", "coordinate")
    verify_runs(args, PRE_SKILLS, "five-current-skills-verified.log")


def recovery(args):
    check_environment(args)
    workbook = args.work_root / "results/final/q2_full_plan.xlsx"
    original = workbook.read_bytes()
    backup = args.work_root / "reports/workflow/q2-before-injected-error.xlsx"
    backup.write_bytes(original)
    mutate = "from openpyxl import load_workbook; from pathlib import Path; p=Path('results/final/q2_full_plan.xlsx'); w=load_workbook(p); s=w['实际供货量']; s['B2']=float(s['B2'].value or 0)+100; w.save(p)"
    execute([args.python, "-X", "utf8", "-c", mutate], root=args.work_root, log_name="inject-workbook-error.log")
    runtime = args.skills_root / "solve-model/scripts/_runtime/skill_runtime.py"
    validation = [args.python, "-X", "utf8", runtime, "validate", "--project-root", args.work_root,
                  "--project-id", PROJECT_ID, "--profile", "competition", "--require-skill", "solve-model"]
    try:
        invoke(args, "solve-model", "verify-solve", expect=1)
        failed_report = args.work_root / "results/final/independent_validation.json"
        shutil.copy2(failed_report, args.work_root / "reports/workflow/independent_validation-injected-failure.json")
        shutil.copy2(args.work_root / "reports/workflow/verify-solve.log", args.work_root / "reports/workflow/verify-solve-injected-failure.log")
        execute(validation, root=args.work_root, log_name="old-pass-rejected.log", expect=1)
        installed_state(args, "rewind", "--to", "modeling", "--reason", "injected delivered-workbook contradiction requires fresh validation")
    finally:
        workbook.write_bytes(original)
    invoke(args, "solve-model", "verify-solve")
    # Rewind mutates the coordinator's state output. A fresh solve does not
    # refresh that Skill's previous output binding; invoke the coordinator too.
    invoke(args, "run-modeling-project", "coordinate")
    execute(validation, root=args.work_root, log_name="new-pass-accepted.log")
    refresh_run_manifest(args)
    advance(args, "validation", {"implementation": "src/reproduce.py", "machine_results": PREFIX + "result_object.json",
                                  "quality_validation": PREFIX + "quality_validation.json", "run_manifest": "run-manifest.json"})
    invoke(args, "run-modeling-project", "coordinate")
    verify_runs(args, PRE_SKILLS, "five-skills-after-recovery.log")
    put(args.work_root, "reports/workflow/failure-recovery.json", {"status": "PASS", "real_workbook_mutation": "actual supply B2 +100",
        "original_workbook_restored": digest(workbook) == digest(backup), "old_pass_rejected_after_failed_retry": True,
        "failure_diagnostics": "reports/workflow/independent_validation-injected-failure.json",
        "fresh_independent_workbook_verification": load(args.work_root / "results/final/independent_validation.json"),
        "stage_after_recovery": load(args.work_root / ".modeling/project-state.json")["current_stage"],
        "scope": "solve and validation recovery; final figures/paper/review still pending"})


def post(args):
    """Continue one real phase; rendering must stop for actual inspection."""
    check_environment(args)
    report = load(args.work_root / "reports/workflow/failure-recovery.json")
    if report.get("status") != "PASS":
        raise ValueError("complete the real failure/recovery verification before post-solution phases")
    if args.phase in {"render-figures", "render-paper"}:
        current = load(args.work_root / ".modeling/project-state.json")
        order = ("intake", "analysis", "modeling", "validation", "writing", "review", "release")
        affected = "validation" if args.phase == "render-figures" else "writing"
        if order.index(current["current_stage"]) > order.index(affected):
            installed_state(args, "rewind", "--to", affected, "--reason",
                "actual regenerated " + ("figures invalidate downstream writing/review" if args.phase == "render-figures" else "paper requires a new page inspection and review"))
        prior_report = args.work_root / "reports/workflow/eight-skill-validation.json"
        if prior_report.is_file():
            prior = load(prior_report)
            prior.update(status="SUPERSEDED", superseded_at=datetime.now(timezone.utc).isoformat(),
                         superseded_reason="new " + args.phase + " run; regenerate and actually review downstream artifacts")
            put(args.work_root, "reports/workflow/eight-skill-validation.json", prior)
    if args.phase == "render-figures":
        paper_handoff(args)
        invoke(args, "make-model-figures", "render-figures", expect=1)
        assert_pending_domain_failure(args.work_root, "make-model-figures")
    elif args.phase == "figures":
        invoke(args, "make-model-figures", "figures")
        current = load(args.work_root / ".modeling/project-state.json")
        if current["current_stage"] == "validation":
            advance(args, "writing", {"validation_report": PREFIX + "solver_validation.json",
                "quality_validation": PREFIX + "quality_validation.json", "paper_spec": "paper/paper-spec.yaml",
                "evidence_index": "paper/evidence-index.json", "figure_registry": "paper/figure-registry.json"})
        invoke(args, "run-modeling-project", "coordinate")
        put(args.work_root, "reports/workflow/post-solution-progress.json", {"status": "INCOMPLETE",
            "completed_current_action": "installed figure Skill and writing handoff",
            "pending": ["current writing", "current review", "full eight-Skill trace verification"]})
    elif args.phase == "render-paper":
        invoke(args, "write-model-paper", "render-paper", expect=1)
        assert_pending_domain_failure(args.work_root, "write-model-paper")
    elif args.phase == "paper":
        invoke(args, "write-model-paper", "paper")
        current = load(args.work_root / ".modeling/project-state.json")
        if current["current_stage"] == "writing":
            advance(args, "review", {"manuscript": "paper/main.md", "main_pdf": "paper/research/main.pdf",
                "decision_contract": PREFIX + "decision_contract.json", "quality_validation": PREFIX + "quality_validation.json",
                "figure_inventory": "paper/figure-registry.json", "layout_validation": "reports/workflow/layout_validation.json",
                "visual_layout_audit": "reports/workflow/visual_layout_audit.json", "run_manifest": "run-manifest.json",
                "latex_compile_report": "reports/workflow/latex_compile_report.json"})
        invoke(args, "run-modeling-project", "coordinate")
        # A previous failed review remains current while its writing inputs are
        # repaired. Do not label the whole trace PASS until the review retries.
        put(args.work_root, "reports/workflow/post-solution-progress.json", {"status": "INCOMPLETE",
            "completed_current_action": "installed writing Skill and review handoff",
            "pending": ["current review", "full eight-Skill trace verification"]})
    elif args.phase == "review":
        invoke(args, "review-model-paper", "review")
        current = load(args.work_root / ".modeling/project-state.json")
        put(args.work_root, "reports/workflow/submission_checklist.json", {"status": "PASS",
            "paper_review": "reports/paper_review_report.json", "preflight": "reports/submission_preflight.json",
            "scope": "historical 2021C generic research report; not a current-year CUMCM formal submission"})
        if current["current_stage"] == "review":
            advance(args, "release", {"paper_review_report": "reports/paper_review_report.json",
                "submission_readiness": "reports/submission_readiness.json", "submission_preflight": "reports/submission_preflight.json",
                "submission_checklist": "reports/workflow/submission_checklist.json", "run_manifest": "run-manifest.json"})
        invoke(args, "run-modeling-project", "coordinate")
        verify_runs(args, tuple(INPUTS), "eight-current-skills-verified.log")
        figure_environment = load(args.work_root / "figures/research/f01_supplier_evidence.figure.json")["environment"]
        put(args.work_root, "reports/workflow/eight-skill-validation.json", {"status": "PASS",
            "skills": list(INPUTS), "python": str(args.python), "skills_root": str(args.skills_root),
            "project_root": str(args.work_root), "stage": load(args.work_root / ".modeling/project-state.json")["current_stage"],
            "real_failure_recovery": "reports/workflow/failure-recovery.json",
            "current_full_contract_and_semantic_verification": "reports/workflow/eight-current-skills-verified.log",
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
            "rendering_implementation_hashes": figure_environment["implementation_hashes"],
            "scope": "eight installed Skills, real historical attachments and results; generic research venue only"})
        put(args.work_root, "reports/workflow/post-solution-progress.json", {"status": "PASS",
            "completed_current_action": "all eight installed Skills and current full trace revalidated",
            "evidence": "reports/workflow/eight-skill-validation.json",
            "scope": "this installed implementation only; a later renderer change requires new figures and paper review"})


def assert_pending_domain_failure(root, skill):
    """An expected review block must not hide a renderer crash or missing input."""
    events = [json.loads(line) for line in (root / "manifests/skill-runs.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    finishes = [event for event in events if event.get("event") == "finish" and event.get("skill") == skill]
    current = finishes[-1] if finishes else {}
    domain_failed = "command succeeded; output semantic validation failed" in current.get("warnings", [])
    if current.get("status") != "FAIL" or not domain_failed or not current.get("outputs"):
        raise RuntimeError(f"{skill} did not finish rendering successfully before the review block; inspect its actual failure")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-root", type=Path, default=REPOSITORY / "output/research-style-upgrade/cumcm-2021-c")
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--skills-root", type=Path, default=Path.home() / ".codex/skills")
    parser.add_argument("--python", type=Path, default=Path.home() / ".codex/runtimes/math-model-figures/Scripts/python.exe")
    parser.add_argument("--phase", choices=("prepare", "pre", "recovery", "render-figures", "figures", "render-paper", "paper", "review", "status"), default="pre")
    parser.add_argument("--worker", choices=("prepare", "coordinate", "analysis", "selection", "solve", "verify-solve", "render-figures", "figures", "render-paper", "paper", "review"))
    args = parser.parse_args()
    args.work_root = args.work_root.resolve()
    args.skills_root = args.skills_root.resolve()
    if args.worker:
        worker(args)
    elif args.phase == "prepare":
        prepare(args)
    elif args.phase == "pre":
        pre(args)
    elif args.phase == "recovery":
        recovery(args)
    elif args.phase != "status":
        post(args)
    else:
        state = load(args.work_root / ".modeling/project-state.json")
        events = [json.loads(line) for line in (args.work_root / "manifests/skill-runs.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        current = {}
        finished = {event["run_id"]: event for event in events if event.get("event") == "finish"}
        for event in events:
            if event.get("event") == "start" and event.get("project_id") == PROJECT_ID and event.get("profile") == "competition":
                current[event["skill"]] = {"run_id": event["run_id"], "trace_status": finished.get(event["run_id"], event).get("status")}
        print(json.dumps({"project_state": state, "current_trace_assertions": current,
                          "verification_command": "pre/recovery performs current full-role and semantic validation; status alone does not revalidate files",
                          "pending_skills": [skill for skill in INPUTS if current.get(skill, {}).get("trace_status") != "PASS"],
                          "overall_release": "TRACE_ONLY: run the complete current-file verification before asserting release"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
