"""Reproducible research traceability audit; no scientific gate promotion.

--write generates a dated snapshot. Default validates its coverage/links/state.
URL occurrence is recorded attribution, never proof that a theorem applies.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/research_audit'
URL = re.compile(r'https?://[^\s<>"{}\\]+')

EXTRA = [
    ('OL-NUMPY', 'NumPy finfo: machine limits', 'https://numpy.org/doc/stable/reference/generated/numpy.finfo.html', 'original_recorded', 'API description checked; archived runtime remains authoritative'),
    ('OL-SCIPY', 'SciPy convolve1d', 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.convolve1d.html', 'original_recorded', 'API description checked; no density-accuracy theorem'),
    ('OL-TIME', 'Shalizi: time-series lectures including dependence and resampling', 'https://stat.cmu.edu/~cshalizi/uADA/16/lectures/26.pdf', 'original_recorded', 'Primary course document retrieved; no project iid guarantee'),
    ('OL-KDE', 'Shalizi: kernel density estimation', 'https://www.stat.cmu.edu/~cshalizi/uADA/24/lectures/ch14.pdf', 'original_recorded', 'Historical citation preserved; full theorem audit pending'),
    ('OL-RESAMPLE', 'Shalizi: resampling over space and time', 'https://www.stat.cmu.edu/~cshalizi/dst/26/', 'original_recorded', 'Historical citation preserved; full applicability review pending'),
    ('OL-FILTER', 'Crisan and Míguez: Particle-kernel estimation of the filter density in state-space models, Bernoulli 20(4), 1879–1929 (2014); arXiv v8 erratum (2016)', 'https://arxiv.org/abs/1111.5866v8', 'original_recorded', 'Metadata/abstract and Theorem4.2 erratum notice checked; deterministic fixed-bandwidth occupation hypotheses unverified'),
    ('OL-BAYES', 'MIT 18.05: Bayesian density updating', 'https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/mit18_05_s22_statistics.pdf', 'original_recorded', 'Recorded primary course reference; does not qualify the project DA interface'),
    ('OL-FNO-GUIDE', 'Official neuraloperator user guide', 'https://neuraloperator.github.io/dev/user_guide/index.html', 'original_recorded', 'Recorded workflow reference; installed project implementation is authoritative'),
    ('OL-FNO-PAPER', 'Li et al.: Fourier Neural Operator for Parametric Partial Differential Equations, arXiv:2010.08895v3 (2021)', 'https://arxiv.org/abs/2010.08895v3', 'retrospective_addition_20261006', 'Primary metadata/abstract checked; no inherited Lorenz accuracy, boundary fidelity or speedup'),
    ('OL-REFORMS', 'REFORMS: Reporting Standards for Machine Learning Based Science', 'https://arxiv.org/abs/2308.07832', 'original_recorded', 'Primary bibliographic record checked; guidance, not pass evidence'),
    ('OL-LEAKAGE', 'Leakage and the Reproducibility Crisis in ML-based Science', 'https://arxiv.org/abs/2207.07048', 'original_recorded', 'Primary bibliographic record checked; guidance, not pass evidence'),
    ('OL-FAIR', 'FAIR4RS principles', 'https://doi.org/10.15497/RDA00068', 'original_recorded', 'Historical record preserved; detailed revalidation pending'),
    ('OL-DATASHEETS', 'Datasheets for Datasets', 'https://arxiv.org/abs/1803.09010', 'original_recorded', 'Historical record preserved; detailed revalidation pending'),
    ('OL-MODELCARDS', 'Model Cards for Model Reporting', 'https://arxiv.org/abs/1810.03993', 'original_recorded', 'Historical record preserved; detailed revalidation pending'),
    ('CHAT-ANISOTROPIC', 'User-provided historical anisotropic-DG reference; title/attribution unresolved', 'https://www.sciencedirect.com/science/article/pii/S037704272300571X', 'user_provided_historical_context', 'Unverified bibliographic record; no theorem import'),
    ('CHAT-SUBCELL', 'User-provided historical subcell/invariant-domain reference; title/attribution unresolved', 'https://www.sciencedirect.com/science/article/pii/S0045782521002139', 'user_provided_historical_context', 'Unverified bibliographic record; hyperbolic-to-FPE transfer unproved'),
    ('CHAT-ADAPTIVE', 'User-provided historical adaptive-DG reference; title/attribution unresolved', 'https://www.sciencedirect.com/science/article/abs/pii/S0021999120300954', 'user_provided_historical_context', 'Unverified bibliographic record; no adopted theorem'),
    ('CHAT-ADAPTIVE-REVIEW', 'User-provided historical adaptive/high-order DG review; title/attribution unresolved', 'https://www.sciencedirect.com/science/article/pii/S0065215624000012', 'user_provided_historical_context', 'Unverified bibliographic record; no adopted theorem'),
    ('CHAT-HP', 'User-provided historical hp-adaptive reference; title/attribution unresolved', 'https://epubs.siam.org/doi/10.1137/16M1079944', 'user_provided_historical_context', 'Unverified bibliographic record; no p-adaptive branch qualification'),
]


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args]).decode()


def urls(text):
    # Preserve full parentheses within DOI strings; remove only unmatched closers.
    result = []
    for value in URL.findall(text):
        value = value.rstrip('.,;`')
        while value.endswith(')') and value.count(')') > value.count('('):
            value = value[:-1]
        result.append(value)
    return result


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    tracked = sorted(git('ls-files', '-z').split('\0')[:-1])
    references = []
    report = ROOT / 'METHOD_SELECTION_REPORT.md'
    for match in re.finditer(r'^\[\^(\d+)\]: (.+)$', report.read_text(), re.M):
        references.append(dict(id=f'FEM-R{int(match[1]):02d}', bibliographic_record=match[2],
            urls=urls(match[2]), provenance='original_recorded', recorded_in=str(report.relative_to(ROOT)),
            verification='Historical record preserved; no automatic imported-theorem applicability. Full-text revalidation not claimed.'))
    bibliography = ROOT / 'docs/solver_monograph/bibliography.tex'
    for match in re.finditer(r'^\\bibitem\{([^}]+)\} (.+)$', bibliography.read_text(), re.M):
        references.append(dict(id='MONO-'+match[1], bibliographic_record=match[2],
            urls=urls(match[2]), provenance='original_recorded', recorded_in=str(bibliography.relative_to(ROOT)),
            verification='Original monograph record preserved; not a fresh full-text audit.'))
    references.extend(dict(id=i, bibliographic_record=t, urls=[u], provenance=p,
        verification=v, recorded_in='docs/operator_learning/ and project contracts; FNO paper explicitly retrospective')
        for i, t, u, p, v in EXTRA)
    occurrences, scanned, skipped = [], [], []
    for name in tracked:
        if name.startswith('docs/research_audit/') or name == 'scripts/audit_research_sources.py':
            continue
        path = ROOT / name
        try:
            data = path.read_bytes()
            text = data.decode('utf-8')
            if '\0' in text:
                raise UnicodeError()
        except (UnicodeError, OSError):
            skipped.append(name)
            continue
        scanned.append(dict(path=name, sha256=hashlib.sha256(data).hexdigest()))
        for number, line in enumerate(text.splitlines(), 1):
            for url in urls(line):
                occurrences.append(dict(url=url, path=name, line=number, context=line))
    history = []
    patch = git('log', '--all', '--format=AUDIT_COMMIT:%H', '--no-ext-diff',
                '--unified=0', '-p', '-Ghttps?://', '--', '.', ':!docs/research_audit',
                ':!scripts/audit_research_sources.py')
    commit, path = '', ''
    for line in patch.splitlines():
        if line.startswith('AUDIT_COMMIT:'):
            commit = line.split(':', 1)[1]
        elif line.startswith('diff --git '):
            path = line.split(' b/', 1)[-1].strip('"')
        elif line[:1] in ('+', '-') and not line.startswith(('+++', '---')):
            for url in urls(line[1:]):
                history.append(dict(commit=commit, path=path, change=line[0], url=url, context=line[1:]))
    methods = json.loads((BASE / 'methods.json').read_text())['methods']
    selected = {
        0: ['OCCUPATION', 'BAYES', 'GOVERNANCE'], 1: ['REPRESENTATION'],
        2: ['OCCUPATION', 'DEPENDENCE', 'BOX', 'BOUND'], 3: ['DEPENDENCE'],
        4: ['DG', 'QP', 'REFERENCE', 'AMR'], 5: ['REPRESENTATION'],
        6: ['GOVERNANCE'], 7: ['FPE', 'QP'], 8: ['BASELINES', 'FNO'],
        9: ['FNO', 'BASELINES'], 10: ['GOVERNANCE', 'BASELINES'],
        11: ['GOVERNANCE', 'BASELINES'], 12: ['FNO', 'REFERENCE'],
        13: ['FPE'], 14: ['FPE'], 15: ['BASELINES', 'MEMORY'],
        16: ['BAYES', 'BOX'], 17: ['BAYES', 'REPRESENTATION'],
    }
    gates = json.loads((ROOT / 'docs/operator_learning/gates.json').read_text())
    gate_rows = []
    events = {
        0: [('OL-D003A', 'PREDECLARED', 'experiments/operator_learning/OL-G00_alignment_v2.json'),
            ('OL-D003B', 'TECHNICAL_COMPLETE_SCIENTIFIC_OPEN', 'docs/operator_learning/evidence/G00_ALIGNMENT_V2_20261005.md'),
            ('OL-D004', 'PASSED_SCOPED_OWNER_SELECTED_POPULATION', 'docs/operator_learning/ACCEPTED_POPULATION_V1.md')],
        1: [('OL-D005', 'FAILED_V1_BITWISE_RECONSTRUCTION', 'docs/operator_learning/evidence/G01_REPRESENTATION_V1_FAILED_20261005.json'),
            ('OL-D006', 'PASSED_V2_UNCHANGED_THRESHOLDS', 'docs/operator_learning/evidence/G01_REPRESENTATION_V2_20261005.md')],
        2: [('OL-D009', 'CHARACTERIZATION_V1_COMPLETE_GATE_OPEN', 'docs/operator_learning/evidence/G02_CHARACTERIZATION_20261006.md'),
            ('OL-D012', 'REFINEMENT_V2_COMPLETE_GATE_OPEN', 'experiments/operator_learning/OL-G02_reconstruction_refinement_v2.json'),
            ('OL-D013', 'MECHANISM_V3_COMPLETE_GATE_OPEN', 'docs/operator_learning/evidence/G02_MECHANISM_V3_20261006.md'),
            ('OL-D015', 'EMPIRICAL_V4_COMPLETE_GATE_OPEN', 'docs/operator_learning/evidence/G02_EMPIRICAL_V4_20261006.md'),
            ('OL-D014', 'CANDIDATE_APPROVED_WITH_RESERVATIONS_NOT_GATE_PASS', 'docs/operator_learning/RECONSTRUCTION_CANDIDATE_APPROVAL_V2.md')],
    }
    for index, gate in enumerate(gates):
        ids = selected[index]
        source_ids = sorted({s for m in methods if m['id'] in ids for s in m['source_ids']})
        gate_rows.append(dict(id=gate['id'], status=gate['decision_status'], question=gate['question'],
            method_ids=ids, research_source_ids=source_ids,
            attribution='Recorded methodological context; no external paper replaces project evidence' if gate['decision_status'] != 'LOCKED' else
                        'Prospective method/context mapping only: gate LOCKED, no adjudication or historical research-use claim',
            evidence_run=gate['evidence_run'], experiment_config=gate['experiment_config'],
            thresholds=gate['predeclared_thresholds'], adjudication=gate['adjudication'],
            historical_events=[dict(decision=d, outcome=s, evidence=p,
                research_source_ids=source_ids, method_ids=ids,
                limitation='Contextual method mapping; original recorded research attribution must be read in cited evidence/decision. No retrospective theorem validation.')
                for d, s, p in events.get(index, [])]))
    prior = json.loads((ROOT / 'docs/solver_monograph/source_ledger.json').read_text())
    fem_records = [dict(path=x['path'], recorded_sha256=x['sha256'],
                        recorded_fields=x['decision_fields'],
                        research_attribution='Historical metadata; method/source links are contextual unless explicitly cited in decision text')
                   for x in prior['inventory'] if x.get('decision_fields')]
    def decision_fields(value, prefix=''):
        found = {}
        if isinstance(value, dict):
            for key, item in value.items():
                path = f'{prefix}.{key}' if prefix else key
                if isinstance(item, (dict, list)):
                    found.update(decision_fields(item, path))
                elif re.search(r'gate|status|decision|certif|passed|fallback|failure', path, re.I):
                    found[path] = item
        elif isinstance(value, list):
            for i, item in enumerate(value):
                found.update(decision_fields(item, f'{prefix}[{i}]'))
        return found
    current_reports = []
    for name in tracked:
        if name.endswith('_report.json') and '/' not in name:
            path = ROOT / name
            current_reports.append(dict(path=name, sha256=digest(path),
                fields=decision_fields(json.loads(path.read_text())),
                methodological_context=['DG', 'QP', 'TIME', 'REFERENCE'],
                limitation='Verbatim classification fields, not new adjudication or claim every method applies to every report.'))
    sections = []
    for name in ['docs/DECISIONS.md', 'docs/operator_learning/DECISIONS.md', 'METHOD_SELECTION_REPORT.md']:
        text = (ROOT / name).read_text()
        for match in re.finditer(r'^## ([^\n]+)\n(.*?)(?=^## |\Z)', text, re.M | re.S):
            sections.append(dict(path=name, heading=match[1], text=match[2].strip(),
                                 directly_recorded_urls=urls(match[2]),
                                 attribution='Only directly recorded citations establish documentary association; uncited reasoning remains project evidence.'))
    snapshot = dict(schema_version=1, date='2026-10-06', source_revision=git('rev-parse', 'HEAD').strip(),
        git_status_at_generation=git('status', '--porcelain'),
        generation_command=['python3', 'scripts/audit_research_sources.py', '--write'],
        scope='All tracked decodable text URLs; reachable Git URL additions/removals; all18 current OL gates; complete decision sections; prior883-record FEM ledger decision fields. Excludes inaccessible chat/uploads and unaudited large ignored arrays.',
        references=references, current_url_occurrences=occurrences, history_url_changes=history,
        scanned_files=scanned, skipped_nontext_or_unavailable=skipped, gates=gate_rows,
        historical_decision_sections=sections, fem_recorded_decision_fields=fem_records,
        current_tracked_report_decision_fields=current_reports,
        original_fem_ledger_revision=prior['revision'],
        original_fem_ledger_sha256=digest(ROOT / 'docs/solver_monograph/source_ledger.json'))
    return snapshot


def validate(root=ROOT):
    root = Path(root)
    base = root / 'docs/research_audit'
    audit = json.loads((base / 'snapshot_20261006.json').read_text())
    methods = json.loads((base / 'methods.json').read_text())
    source_ids = {r['id'] for r in audit['references']} | {r['id'] for r in methods['local_sources']}
    method_ids = {m['id'] for m in methods['methods']}
    errors = []
    for method in methods['methods']:
        if not method['limitations']:
            errors.append(f"missing limitation: {method['id']}")
        for source in method['source_ids']:
            if source not in source_ids:
                errors.append(f'unknown research source: {source}')
        for path in method['implementation_and_evidence']:
            if not (root / path).is_file():
                errors.append(f'missing method evidence: {path}')
    canonical = json.loads((root / 'docs/operator_learning/gates.json').read_text())
    if [g['id'] for g in audit['gates']] != [g['id'] for g in canonical]:
        errors.append('research audit gate coverage stale')
    for actual, frozen in zip(canonical, audit['gates']):
        if actual['decision_status'] != frozen['status'] or actual['adjudication'] != frozen['adjudication']:
            errors.append(f"research audit gate decision stale: {actual['id']}")
        if actual['decision_status'] in ('PASSED', 'FAILED') and not frozen['historical_events']:
            errors.append(f"adjudicated gate missing outcome/research history: {actual['id']}")
        if set(frozen['method_ids']) - method_ids or set(frozen['research_source_ids']) - source_ids:
            errors.append('unresolved gate method/source link')
        for event in frozen['historical_events']:
            if not (root / event['evidence']).is_file():
                errors.append(f"missing historical event evidence: {event['evidence']}")
    for path in ['docs/operator_learning/evidence/G01_REPRESENTATION_V1_FAILED_20261005.json',
                 'docs/operator_learning/evidence/G01_REPRESENTATION_V2_20261005.json']:
        if path not in {f['path'] for f in audit['scanned_files']}:
            errors.append('historical G01 outcome omitted')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        data = build()
        (BASE / 'snapshot_20261006.json').write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n')
        print('Audit snapshot:', len(data['references']), 'references,', len(data['current_url_occurrences']),
              'current URL occurrences,', len(data['history_url_changes']), 'Git changes,',
              len(data['fem_recorded_decision_fields']), 'historical decision-field records')
    errors = validate()
    print('\n'.join(errors) if errors else 'RESEARCH TRACEABILITY: PASS (no scientific gate promotion)')
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
