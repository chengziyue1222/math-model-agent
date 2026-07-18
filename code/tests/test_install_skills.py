from pathlib import Path

from scripts.install_skills import install_skills


def test_install_skills_copies_selected_skill(tmp_path):
    source = Path(__file__).resolve().parents[2] / "skills"
    target = tmp_path / "installed"

    destinations = install_skills(source, target, ["select-model"])

    assert destinations == [target / "select-model"]
    assert (target / "select-model" / "SKILL.md").exists()
    assert (target / "select-model" / "agents" / "openai.yaml").exists()


def test_install_skills_dry_run_does_not_write(tmp_path):
    source = Path(__file__).resolve().parents[2] / "skills"
    target = tmp_path / "installed"

    destinations = install_skills(source, target, ["solve-model"], dry_run=True)

    assert destinations == [target / "solve-model"]
    assert not target.exists()
