"""Create actual browser SVG proofs and format-comparison contact sheets."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright


def contacts(folder, records, case, suffix, caption):
    rows = [r for r in records if r['case'] == case and 'error' not in r]
    for start in range(0, len(rows), 6):
        board = Image.new('RGB', (1800, 1950), 'white')
        draw = ImageDraw.Draw(board)
        for i, record in enumerate(rows[start:start+6]):
            with Image.open(folder / case / (record['name'] + suffix + '.png')) as source:
                im = source.convert('RGB')
            im.thumbnail((875, 605))
            x, y = i%2*900, i//2*650
            board.paste(im, (x+(875-im.width)//2, y+30))
            draw.text((x+12, y+7), f'{start+i+1}. {record["name"]} / {caption}', fill='black')
        board.save(folder / f'contact-{case}-{caption}-{start//6+1:02d}.png')


def build(folder):
    records = json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path='C:/Program Files/Google/Chrome/Application/chrome.exe', headless=True)
        page = browser.new_page(viewport={'width': 1300, 'height': 1900}, device_scale_factor=2)
        for record in records:
            if 'error' in record: continue
            svg = folder / record['case'] / (record['name']+'.svg')
            page.goto(svg.resolve().as_uri(), wait_until='load')
            page.locator('svg').screenshot(path=str(svg.with_name(svg.stem+'_svg.png')))
        browser.close()
    for case in ('standard', 'long_labels', 'dense'):
        for suffix, caption in (('', 'png'), ('_vector', 'pdf'), ('_svg', 'svg'), ('_gray', 'gray')):
            contacts(folder, records, case, suffix, caption)
    sheet_count = 4*sum((sum(r['case'] == case and 'error' not in r for r in records)+5)//6
                        for case in ('standard', 'long_labels', 'dense'))
    print(json.dumps({'browser_svg_proofs': sum('error' not in r for r in records), 'format_contact_sheets': sheet_count}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gallery', type=Path, required=True)
    args = parser.parse_args()
    build(args.gallery.resolve())
