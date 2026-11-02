"""Derive the all-entry report from current per-figure evidence, never a second ledger."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'code'))

from algorithms.figure_export import validate_figure_review
from algorithms.figures import display_name, get_spec, list_figures
from figure_comparison_invariants import core, equal

CASES = ('standard', 'long_labels', 'dense')


def audit(directory):
    records = json.loads((directory / 'manifest.json').read_text(encoding='utf-8'))
    expected = {(name, case) for name in list_figures() for case in CASES}
    actual = [(row['name'], row['case']) for row in records]
    inventory_errors = []
    if set(actual) != expected or len(actual) != len(expected):
        inventory_errors.append('manifest must contain exactly every registered entry and all three cases')
    payloads, rows = {}, []
    for name, case in sorted(expected):
        path = directory / case / (name + '.figure.json')
        errors = validate_figure_review(path, source_root=ROOT)
        try:
            payload = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            payload = {}
        payloads[name, case] = payload
        pending = payload.get('completion_status') in {'NEEDS_REVIEW', 'NEEDS_VISUAL_REVIEW'}
        failed = payload.get('completion_status') == 'FAIL'
        state = 'PASS' if not errors else 'FAIL' if failed or not pending else 'INCOMPLETE'
        rows.append({'name': name, 'case': case, 'status': state, 'errors': errors,
                     'metadata': str(path.relative_to(directory)),
                     'visual_review': payload.get('visual_review', {}),
                     'numerical_status': payload.get('numerical_regression', {}).get('status', 'NOT_CHECKED')})
    aliases = []
    for name in list_figures():
        target = get_spec(name).to_dict().get('alias_of')
        if not target:
            continue
        for case in CASES:
            first, second = payloads[name, case], payloads[target, case]
            checks = {
                'identical_saved_input': hashlib.sha256((directory / case / (name + '.data.json')).read_bytes()).digest()
                                         == hashlib.sha256((directory / case / (target + '.data.json')).read_bytes()).digest(),
                'identical_numeric_artists': equal(core(first.get('numerical_regression', {}).get('artist_evidence', [])),
                                                  core(second.get('numerical_regression', {}).get('artist_evidence', []))),
                'same_configuration': first.get('configuration') == second.get('configuration'),
            }
            aliases.append({'alias': name, 'target': target, 'case': case, 'checks': checks,
                            'status': 'PASS' if all(checks.values()) else 'FAIL'})
    chinese = {name: get_spec(name) is get_spec(display_name(name)) for name in list_figures()}
    counts = Counter(row['status'] for row in rows)
    complete = not inventory_errors and counts['PASS'] == len(expected) and all(r['status'] == 'PASS' for r in aliases) and all(chinese.values())
    return {'status': 'PASS' if complete else 'INCOMPLETE', 'registered_entries': len(list_figures()),
            'case_count': len(expected), 'status_counts': dict(counts), 'inventory_errors': inventory_errors,
            'alias_checks': aliases, 'chinese_entry_identity': chinese, 'figures': rows,
            'authority': 'per-entry .figure.json plus current source/output/implementation bindings; this report is derived'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gallery', type=Path, required=True)
    args = parser.parse_args()
    directory = args.gallery.resolve()
    report = audit(directory)
    (directory / 'acceptance-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    mapping = {(r['name'], r['case']): r for r in report['figures']}
    lines = ['# 全图库逐项验收', '', f"总体：**{report['status']}**；{report['registered_entries']} 个入口，{report['case_count']} 组案例。",
             '', '本报告从当前逐图证据生成；缺少检查、数值差异未解释或哈希过期均不能通过。', '',
             '| 入口 | 普通 | 长中文 | 密集 |', '|---|---|---|---|']
    for name in list_figures():
        cells = [f"[{mapping[name, case]['status']}]({case}/{name}.figure.json)" for case in CASES]
        lines.append(f"| {display_name(name)} / {name} | " + ' | '.join(cells) + ' |')
    lines += ['', '## 未完成或失败项目', '']
    for row in report['figures']:
        if row['status'] != 'PASS':
            lines.append(f"- {row['case']}/{row['name']}: " + '; '.join(row['errors']))
    (directory / 'acceptance-report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({key: report[key] for key in ('status', 'registered_entries', 'case_count', 'status_counts', 'inventory_errors')}))
    return int(report['status'] != 'PASS')


if __name__ == '__main__':
    raise SystemExit(main())
