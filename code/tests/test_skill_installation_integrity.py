from pathlib import Path

from scripts.install_skills import install_skills
from scripts.verify_skill_installation import verify_installation

ROOT = Path(__file__).resolve().parents[2]


def test_installer_runtime_drift_is_detected_even_when_skill_files_match(tmp_path):
    source = tmp_path / 'source'
    # Limit this behavior check to one real Skill; the final installation checks all eight.
    import shutil
    shutil.copytree(ROOT / 'skills/solve-model', source / 'solve-model')
    installed = tmp_path / 'installed'
    install_skills(source, installed)
    assert verify_installation(source, installed)['status'] == 'PASS'
    helper = installed / 'solve-model/scripts/_runtime/skill_runtime.py'
    helper.write_text(helper.read_text(encoding='utf-8') + '\n# outdated helper\n', encoding='utf-8')
    report = verify_installation(source, installed)
    assert report['status'] == 'FAIL'
    assert report['skills'][0]['differences'] == ['scripts/_runtime/skill_runtime.py']
