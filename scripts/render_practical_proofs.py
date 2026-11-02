"""Prepare vector, final-size and grayscale proofs for human visual inspection."""
from pathlib import Path
import argparse
import subprocess

import fitz
from PIL import Image, ImageDraw


def main(directory, browser=None):
    paths = sorted(directory.glob("*.pdf"))
    proofs = directory / "proofs"
    proofs.mkdir(exist_ok=True)
    rows = (len(paths)+2)//3
    sheets = {mode: Image.new("RGB", (1800, rows*600), "white") for mode in ("vector", "gray")}
    for i, path in enumerate(paths):
        with fitz.open(path) as doc:
            pixmap = doc[0].get_pixmap(dpi=120)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
        image.save(proofs / f"{path.stem}-vector.png")
        image.convert("L").convert("RGB").save(proofs / f"{path.stem}-gray.png")
        for mode, sheet in sheets.items():
            thumb = image.convert("L").convert("RGB") if mode == "gray" else image.copy()
            thumb.thumbnail((580, 560))
            x, y = (i % 3)*600, (i//3)*600
            sheet.paste(thumb, (x+(600-thumb.width)//2, y+35))
            ImageDraw.Draw(sheet).text((x+15, y+10), path.stem, fill="black")
    for mode, sheet in sheets.items():
        sheet.save(proofs / f"contact-{mode}.png")
    if browser:
        for extension in ("svg", "png"):
            cells = ''.join(f'<div><p>{p.stem}</p><img src="../{p.stem}.{extension}"></div>' for p in paths)
            html = proofs / f"contact-{extension}.html"
            html.write_text('<!doctype html><meta charset="utf-8"><style>body{margin:0;background:white;display:grid;grid-template-columns:repeat(3,600px);font:12px sans-serif}div{height:600px;text-align:center}p{text-align:left;margin:12px}img{width:150mm;max-height:550px;object-fit:contain}</style>'+cells, encoding="utf-8")
            target = (proofs / f"contact-{extension}.png").resolve()
            subprocess.run([str(browser), "--headless", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                            "--allow-file-access-from-files", "--hide-scrollbars", "--virtual-time-budget=3000",
                            "--user-data-dir="+str((proofs / "browser-profile").resolve()),
                            f"--window-size=1800,{rows*600+50}", "--screenshot="+str(target), html.resolve().as_uri()],
                           capture_output=True, timeout=45, check=True)
            if not target.is_file():
                raise RuntimeError("browser did not produce proof: " + str(target))
    print(f"Prepared {len(paths)} PDF vector proofs and grayscale proofs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--browser", type=Path, help="Optional Chromium executable for SVG/PNG final-size contact proofs")
    args = parser.parse_args()
    main(args.directory, args.browser)
