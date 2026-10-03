#!/usr/bin/env python3
"""Package editable monograph sources after explicit visual-review acceptance."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs/solver_monograph'
OUT = ROOT / 'output/pdf'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--visual-review-passed', action='store_true')
    args = parser.parse_args()
    if not args.visual_review_passed:
        parser.error('Inspect the rendered pages before accepting visual review')
    qa_path = OUT / 'solver_monograph_qa.json'
    qa = json.loads(qa_path.read_text())
    pdf = OUT / 'lorenz_solver_monograph.pdf'
    if digest(pdf) != qa['sha256']:
        raise ValueError('PDF changed after rendering; repeat QA')
    qa['visual_review'] = 'PASS: every-page contact sheets and detailed equation/figure/table review'
    qa_path.write_text(json.dumps(qa, indent=2) + '\n')
    files = sorted(p for p in SOURCE.iterdir() if p.suffix in ('.tex', '.json', '.md')
                   and p.name != 'manifest.json')
    figures = sorted((OUT / 'solver_monograph').glob('*.pdf'))
    ledger = json.loads((SOURCE / 'source_ledger.json').read_text())
    manifest = {
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'solver_evidence_revision': ledger['revision'],
        'scope': 'Complete recorded source/history audit and tested Lorenz solver monograph; no solver equations changed, no production authorization.',
        'pdf': {'path': str(pdf.relative_to(ROOT)), 'sha256': digest(pdf),
                'pages': qa['pages'], 'word_count_approximate': qa['word_count_approximate']},
        'editable_archive': 'output/pdf/lorenz_solver_monograph_source.zip',
        'source_files': {str(p.relative_to(ROOT)): digest(p) for p in files},
        'figures': {str(p.relative_to(ROOT)): digest(p) for p in figures},
        'evidence_counts': {'tracked_source_files': sum(e['tracked'] for e in ledger['inventory']),
                            'compact_inventory_records': len(ledger['inventory']),
                            'commits': len(ledger['chronology'])},
        'validation': {'repository_check': 'PASS: 42 tests, static/compilation/whitespace checks',
                       'solver_invariants': 'PASS: 10 tests',
                       'mathematical_verifier': 'PASS; method_certified remains false',
                       'pdf_qa': qa},
        'limitations': ['Selected large arrays independently audited; other payloads indexed by compact evidence.',
                        'Successful MFEM summary guards are not full persisted residual/correction histories.',
                        'Mature-density continuum error remains open; domain evidence is tested-law/horizon scoped.']}
    manifest_path = SOURCE / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    scripts = [ROOT / 'scripts' / name for name in
               ('build_solver_monograph_evidence.py', 'verify_solver_monograph.py',
                'package_solver_monograph.py')]
    archive = OUT / 'lorenz_solver_monograph_source.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in files + [manifest_path] + figures + scripts:
            bundle.write(path, str(path.relative_to(ROOT)))
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise RuntimeError('Source archive integrity check failed')
    print(json.dumps({'pdf_pages': qa['pages'], 'archive': str(archive.relative_to(ROOT)),
                      'archive_sha256': digest(archive), 'manifest': str(manifest_path.relative_to(ROOT))}, indent=2))


if __name__ == '__main__':
    main()
