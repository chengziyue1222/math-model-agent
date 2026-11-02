"""Compare installed Skills and every installer-bundled runtime helper."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from .install_skills import DEFAULT_SOURCE, RUNTIME_FILES, RUNTIME_SOURCE, default_target
    from .validate_skills import validate_skill
except ImportError:
    from install_skills import DEFAULT_SOURCE, RUNTIME_FILES, RUNTIME_SOURCE, default_target
    from validate_skills import validate_skill


def verify_installation(source: Path, target: Path, *, runtime_source: Path = RUNTIME_SOURCE):
    records = []
    for skill in sorted(p for p in source.iterdir() if p.is_dir()):
        installed = target / skill.name
        errors = validate_skill(installed, target.parent)
        hashes, differences = {}, []
        expected = {p.relative_to(skill).as_posix(): p for p in skill.rglob('*')
                    if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc', '.pyo'}}
        expected.update({'scripts/_runtime/' + name: runtime_source / name for name in RUNTIME_FILES})
        for relative, path in sorted(expected.items()):
            destination = installed / relative
            wanted = hashlib.sha256(path.read_bytes()).hexdigest()
            found = hashlib.sha256(destination.read_bytes()).hexdigest() if destination.is_file() else None
            hashes[relative] = {'expected': wanted, 'installed': found}
            if wanted != found:
                differences.append(relative)
        if not (installed / 'scripts/_runtime/__init__.py').is_file():
            differences.append('scripts/_runtime/__init__.py')
        records.append({'name': skill.name, 'path': str(installed.resolve()),
                        'status': 'FAIL' if errors or differences else 'PASS',
                        'errors': errors, 'differences': differences, 'files': hashes})
    return {'status': 'PASS' if records and all(r['status'] == 'PASS' for r in records) else 'FAIL',
            'runtime_files_checked_per_skill': list(RUNTIME_FILES), 'skills': records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=DEFAULT_SOURCE)
    parser.add_argument('--target', type=Path, default=default_target())
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    report = verify_installation(args.source, args.target)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'status': report['status'], 'skills': len(report['skills']),
                      'differences': {r['name']: r['differences'] for r in report['skills'] if r['differences']}}))
    return int(report['status'] != 'PASS')


if __name__ == '__main__':
    raise SystemExit(main())
