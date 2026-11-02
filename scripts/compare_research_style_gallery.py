"""All-entry visual comparison and source/numerical regression evidence."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
from pathlib import Path

import fitz
import numpy as np
from PIL import Image, ImageDraw
from figure_comparison_invariants import core, verify_change


def differences(before, after, prefix=''):
    if isinstance(before, dict) and isinstance(after, dict):
        result = []
        for key in sorted(set(before)|set(after)):
            if key in {'xlim', 'ylim'}: continue  # Autoscaling is reported separately.
            if key not in before or key not in after:
                result.append(prefix+'.'+key+': field added/removed')
            else: result.extend(differences(before[key], after[key], prefix+'.'+key))
        return result
    if isinstance(before, list) and isinstance(after, list):
        if len(before) != len(after): return [prefix+': shape/artist count differs']
        result=[]
        for i, (a, b) in enumerate(zip(before, after)):
            result.extend(differences(a, b, prefix+f'[{i}]'))
            if len(result)>50: break
        return result
    if isinstance(before, (float, int)) and isinstance(after, (float, int)):
        return [] if np.isclose(before, after, rtol=1e-8, atol=1e-8, equal_nan=True) else [prefix+': numerical value differs']
    return [] if before == after else [prefix+': value differs']


def normalize_evidence(axes):
    """Equivalent polar angles and masked missing cells have one form."""
    if not isinstance(axes, list): return axes
    axes = core(axes)
    def clean(value):
        if isinstance(value, dict): return {k:clean(v) for k,v in value.items()}
        if isinstance(value, list): return [clean(v) for v in value]
        if isinstance(value, float) and not np.isfinite(value): return None
        return value
    return clean(axes)


def numerical_tree(value):
    if isinstance(value, dict):
        return {k: numerical_tree(v) for k,v in value.items()
                if k not in {'colors','palette','group_colors','positions','data_contract','font_size','input_data'}}
    if isinstance(value, list): return [numerical_tree(v) for v in value]
    if isinstance(value, (float, int, bool)) or value is None: return value
    return None


def build(before, gallery, output):
    output.mkdir(parents=True, exist_ok=True)
    records = json.loads((gallery/'manifest.json').read_text(encoding='utf-8'))
    old = {(r['name'],r['case']):r for r in json.loads((before/'manifest.json').read_text(encoding='utf-8'))}
    proof=fitz.open(); cards=[]; summaries=[]
    for record in records:
        key=(record['name'],record['case']); prior=old[key]
        current_path=gallery/record['case']/(record['name']+'.figure.json')
        current=json.loads(current_path.read_text(encoding='utf-8')) if 'error' not in record else None
        source=gallery/record['case']/(record['name']+'.data.json')
        source_hash=hashlib.sha256(source.read_bytes()).hexdigest()
        source_same=source_hash == prior.get('source_hash')
        delta=[]; scale_delta=[]; metadata_delta=[]
        if current is not None and 'error' not in prior:
            delta=differences(normalize_evidence(prior.get('artist_evidence')), normalize_evidence(current['numerical_regression']['artist_evidence']))
            scale_delta=differences([[a.get('xlim'),a.get('ylim')] for a in prior['artist_evidence']],
                                    [[a.get('xlim'),a.get('ylim')] for a in current['numerical_regression']['artist_evidence']])
            metadata_delta=differences(numerical_tree(prior.get('metadata')), numerical_tree(current.get('figure_metadata')))
        verification = {'status': 'FAIL' if current is None or not source_same else 'NEEDS_REVIEW',
                        'documented_change': None, 'invariant_checks': {'source_hash_match': source_same},
                        'verification_evidence': {'status': 'NOT_CHECKED', 'method': 'saved-input-and-plotted-artists'}}
        if current is not None and source_same and 'error' not in prior:
            try:
                verification = verify_change(record['name'], json.loads(source.read_text(encoding='utf-8')), prior, current)
                verification['invariant_checks']['source_hash_match'] = True
                verification['verification_evidence']['source_sha256'] = source_hash
                verification['verification_evidence']['checks_passed'] = sum(verification['invariant_checks'].values())
                verification['verification_evidence']['checks_required'] = len(verification['invariant_checks'])
                verifier = Path(__file__).with_name('figure_comparison_invariants.py')
                verification['verification_evidence']['verifier_code'] = {'path': str(verifier.resolve()),
                    'sha256': hashlib.sha256(verifier.read_bytes()).hexdigest()}
                capture = Path(__file__).with_name('figure_acceptance_evidence.py')
                verification['verification_evidence']['artist_capture_code'] = {'path': str(capture.resolve()),
                    'sha256': hashlib.sha256(capture.read_bytes()).hexdigest()}
                for field, value in (('artist_evidence', current['numerical_regression']['artist_evidence']),
                                     ('figure_metadata', current.get('figure_metadata'))):
                    verification['verification_evidence'][field+'_sha256'] = hashlib.sha256(
                        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest()
            except (KeyError, ValueError, TypeError, IndexError, ArithmeticError) as exc:
                verification = {'status': 'FAIL', 'documented_change': 'Invariant verification could not complete: '+str(exc),
                                'invariant_checks': {'verifier_completed': False, 'source_hash_match': True},
                                'verification_evidence': {'status': 'FAIL', 'method': 'saved-input-and-plotted-artists'}}
        status = verification['status']; note = verification['documented_change']
        summary={'name':record['name'],'case':record['case'],**verification,'source_hash_match':source_same,
                 'artist_differences':delta[:50], 'domain_differences':scale_delta[:20],
                 'numeric_metadata_differences':metadata_delta[:50], 'documented_change':note,
                 'baseline_error':prior.get('error'),
                 'comparison_normalization': 'polar angles modulo 2pi; angle undefined at radius <= 1e-9; masked missing cells normalized to null',
                 'comparison_code': {'path': str(Path(__file__).resolve()),
                                     'sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}}
        summaries.append(summary)
        if current:
            current['numerical_regression'].update(summary)
            current_path.write_text(json.dumps(current,ensure_ascii=False,indent=2),encoding='utf-8')
        stem=record['case']+'/'+record['name']
        board=Image.new('RGB',(1800,1100),'white'); draw=ImageDraw.Draw(board)
        draw.text((20,15),f'{record["name"]} / {record["case"]} / BEFORE -> AFTER',fill='black')
        for i, folder in enumerate((before,gallery)):
            image_path=folder/record['case']/(record['name']+'.png')
            if image_path.exists() and not (i==0 and 'error' in prior):
                with Image.open(image_path) as im: image=im.convert('RGB')
                image.thumbnail((860,1000)); board.paste(image,(i*900+(900-image.width)//2,65))
            else: draw.text((i*900+25,100), 'Prior implementation could not render this exact input.',fill='black')
        target=output/record['case']; target.mkdir(exist_ok=True)
        board.save(target/(record['name']+'.png'))
        page=proof.new_page(width=297/25.4*72,height=210/25.4*72)
        page.insert_image(fitz.Rect(15,15,page.rect.width-15,page.rect.height-15),filename=str(target/(record['name']+'.png')),keep_proportion=True)
        cards.append(f'<article><h2>{html.escape(stem)}</h2><img src="{stem}.png"><p>Numerical: {status}; source hash match: {source_same}</p><p>{html.escape(note or "")}</p></article>')
    proof.save(output/'all-entry-before-after.pdf',deflate=True); proof.close()
    (output/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>全图库改前改后</title><style>body{font:15px system-ui;margin:24px}article{border-bottom:1px solid #ddd}img{max-width:100%;width:1200px}</style><h1>全部164入口 × 三类输入的逐项对照</h1><p>全部对照使用相同保存输入；此前无法渲染的输入保留失败事实。合成数据仅验收图型，不代表赛事结果。</p>'+''.join(cards),encoding='utf-8')
    (output/'numerical-comparison.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2),encoding='utf-8')
    counts={s:sum(r['status']==s for r in summaries) for s in sorted(set(r['status'] for r in summaries))}
    print(json.dumps({'pairs':len(summaries),'status':counts,'source_hash_mismatches':sum(not r['source_hash_match'] for r in summaries)},ensure_ascii=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before',type=Path,required=True);parser.add_argument('--gallery',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();build(args.before.resolve(),args.gallery.resolve(),args.output.resolve())
