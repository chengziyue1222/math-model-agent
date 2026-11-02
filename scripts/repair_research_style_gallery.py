"""Regenerate selected entries and preserve unrelated per-entry evidence."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

import fitz
from build_research_style_acceptance import build, contacts, index


def repair(folder, names):
    previous = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    generated = build(folder, names=names)
    mapping = {(r['name'], r['case']): r for r in generated}
    merged = [mapping.get((r['name'], r['case']), r) for r in previous]
    (folder/'manifest.json').write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding='utf-8')
    contacts(folder, merged)
    index(folder, merged)
    proof = fitz.open()
    for record in merged:
        if 'error' in record: continue
        with fitz.open(folder/record['case']/(record['name']+'.pdf')) as source:
            page = proof.new_page(width=210/25.4*72, height=297/25.4*72)
            page.insert_text((20/25.4*72, 30), f'{record["name"]} / {record["case"]} / natural physical size', fontsize=9)
            page.show_pdf_page(fitz.Rect(20/25.4*72, 45, 20/25.4*72+source[0].rect.width, 45+source[0].rect.height), source, 0)
    proof.save(folder/'physical-proofs.pdf', deflate=True)
    proof.close()
    print(json.dumps({'repaired': names, 'errors': [r for r in merged if 'error' in r]}, ensure_ascii=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gallery', type=Path, required=True)
    parser.add_argument('--names', nargs='+', required=True)
    args = parser.parse_args()
    repair(args.gallery.resolve(), args.names)
