"""Typed, deterministic research provenance graph; documentary links are not proof."""
import hashlib
import json
import re
from collections import deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = 'docs/research_audit/graph.json'
RELATIONS = {
    'informed_by', 'implemented_by', 'proposed_for', 'tested_by', 'generated',
    'recorded_in', 'documents', 'adjudicates', 'has_outcome', 'references',
    'depends_on', 'supports', 'contradicts', 'supersedes', 'required_for',
    'constrained_by',
}
INPUTS = [
    'docs/research_audit/methods.json', 'docs/research_audit/snapshot_20261006.json',
    'docs/operator_learning/gates.json', 'docs/operator_learning/state.json',
    'docs/operator_learning/CLAIMS.md', 'docs/CLAIMS.md',
    'docs/operator_learning/DECISIONS.md', 'docs/DECISIONS.md',
    'docs/operator_learning/assumptions.yaml', 'docs/assumptions.yaml',
    'docs/research_audit/gate_updates.json',
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def outcome_status(value, field=''):
    """Interpret only explicit classifications or gate-pass booleans."""
    if isinstance(value, bool) and re.search(r'(gate.*passed|gates_passed|gate_passed)$', field):
        return 'PASSED' if value else 'FAILED'
    if isinstance(value, str):
        if re.fullmatch(r'(PASSED|FAILED)(?:_[A-Z0-9]+)*', value):
            return value.split('_', 1)[0]
        if value in ('OPEN', 'LOCKED', 'CANCELLED', 'SUPERSEDED', 'INSUFFICIENT_EVIDENCE'):
            return value
        if value in ('COMPLETED', 'RUNNING', 'PREPARED_NOT_EXECUTED'):
            return 'TECHNICAL_'+value
    return 'RECORDED'


def build_graph(root=ROOT):
    root = Path(root)
    configs = sorted(str(p.relative_to(root)) for p in
                     (root / 'experiments/operator_learning').glob('*.json'))
    inputs = INPUTS + ['docs/research_audit/graph_sources.json',
                       'operator_learning/research_graph.py', 'scripts/research_graph.py'] + configs
    hashes = {p: sha((root / p).read_bytes()) for p in inputs}
    audit = json.loads((root / inputs[1]).read_text())
    methods = json.loads((root / inputs[0]).read_text())
    gates = json.loads((root / inputs[2]).read_text())
    state = json.loads((root / inputs[3]).read_text())
    nodes, edges = {}, {}

    def node(identifier, kind, label, **attrs):
        if identifier in nodes:
            if nodes[identifier]['kind'] != kind:
                raise ValueError(f'Conflicting node types: {identifier}')
            nodes[identifier].update(attrs)
        else:
            nodes[identifier] = dict(id=identifier, kind=kind, label=label, **attrs)
        return identifier

    def edge(source, relation, target, attribution, **attrs):
        identifier = 'edge:'+sha(json.dumps([source, relation, target, attribution],
                                          ensure_ascii=False).encode())[:24]
        edges[identifier] = dict(id=identifier, source=source, relation=relation,
                                target=target, attribution=attribution, **attrs)

    def artifact(path):
        kind = 'run' if path.startswith('runs/') and not Path(path).suffix else (
               'experiment' if path.startswith('experiments/') else 'artifact')
        return node(kind+':'+path, kind, path, path=path,
                    availability='IGNORED_LOCAL_NOT_REVERIFIED' if path.startswith('runs/') else 'REPOSITORY_POINTER')

    def references(identifier, text, attribution):
        for other in set(re.findall(r'OL-D\d{3}[A-Z]?|OL-G\d{2}_[A-Z_]+|OL-A\d{2}', text)):
            prefix = 'decision:' if other.startswith('OL-D') else (
                     'gate:' if other.startswith('OL-G') else 'assumption:')
            if prefix+other in nodes:
                edge(identifier, 'references', prefix+other, attribution)
        for path in set(re.findall(r'(?:docs/|experiments/|runs/|tests/|mfem/|scripts/)[\w./-]+', text)):
            edge(identifier, 'references', artifact(path.rstrip('.')), attribution)
        for path in set(re.findall(r'[\w./-]+\.(?:json|md|yaml|py)', text)):
            base = Path(nodes[identifier].get('path', '')).parent
            candidates = [Path(path), base / path]
            for candidate in candidates:
                if (root / candidate).is_file():
                    edge(identifier, 'references', artifact(str(candidate)), attribution)
                    break

    for source in audit['references']:
        node('source:'+source['id'], 'source', source['bibliographic_record'],
             status=source['provenance'], urls=source['urls'],
             verification=source['verification'])
    for source in methods['local_sources']:
        node('source:'+source['id'], 'source', source['description'], status='PROJECT_EVIDENCE')
    graph_sources = json.loads((root / 'docs/research_audit/graph_sources.json').read_text())
    for source in graph_sources['sources']:
        node('source:'+source['id'], 'source', source['title'], status=source['attribution'],
             urls=source['urls'], use=source['use'], verification=source['verification'])
    graph_method = graph_sources['method']
    node('method:'+graph_method['id'], 'method', graph_method['definition'],
         status='IMPLEMENTED_ENGINEERING_INDEX', limitations=graph_method['assumptions_and_limits'])
    for source in graph_sources['sources']:
        edge('method:'+graph_method['id'], 'informed_by', 'source:'+source['id'], source['attribution'])
    for path in graph_method['implementation']:
        edge('method:'+graph_method['id'], 'implemented_by', artifact(path), 'GRAPH_METHOD_RECORD')
    for method in methods['methods']:
        identifier = node('method:'+method['id'], 'method', method['method'],
                          status=method['stage_status'], limitations=method['limitations'])
        for source in method['source_ids']:
            edge(identifier, 'informed_by', 'source:'+source,
                 'AUDIT_CONTEXT_NOT_PROOF_OR_CERTIFIED_HISTORICAL_USE')
        for path in method['implementation_and_evidence']:
            edge(identifier, 'implemented_by' if Path(path).suffix in ('.py', '.cpp', '.hpp') else
                 'recorded_in', artifact(path), 'METHOD_REGISTER')

    # Parse flat project assumption registries without adding a YAML dependency.
    for relative in inputs[8:10]:
        text = (root / relative).read_text()
        for match in re.finditer(r'^((?:OL-)?A\d+):\n(.*?)(?=^(?:OL-)?A\d+:|\Z)', text, re.M | re.S):
            statement = re.search(r'^  statement: (.+)$', match[2], re.M)
            status = re.search(r'^  status: (.+)$', match[2], re.M)
            identifier = node('assumption:'+match[1], 'assumption',
                              statement[1] if statement else match[1],
                              status=status[1] if status else 'RECORDED', text=match[2].strip())
            edge(identifier, 'recorded_in', artifact(relative), 'ASSUMPTION_REGISTRY')

    sections = []
    for relative in inputs[6:8]:
        text = (root / relative).read_text()
        for match in re.finditer(r'^## ([^\n]+)\n(.*?)(?=^## |\Z)', text, re.M | re.S):
            sections.append(dict(path=relative, heading=match[1], text=match[2].strip()))
    sections.extend(s for s in audit['historical_decision_sections']
                    if s['path'] == 'METHOD_SELECTION_REPORT.md')
    for section in sections:
        found = re.search(r'\bOL-D\d{3}[A-Z]?\b', section['heading'])
        local_id = found[0] if found else sha((section['path']+'#'+section['heading']).encode())[:24]
        identifier = node('decision:'+local_id, 'decision', section['heading'],
                          status='RECORDED_DECISION', text=section['text'], path=section['path'])
        edge(identifier, 'recorded_in', artifact(section['path']), 'ORIGINAL_DECISION_SECTION')
        for source in audit['references']:
            if any(url in section['text'] for url in source['urls']):
                edge(identifier, 'references', 'source:'+source['id'], 'EXPLICIT_URL_IN_DECISION_TEXT')

    gate_rows = {g['id']: g for g in audit['gates']}
    for gate in gates:
        identifier = node('gate:'+gate['id'], 'gate', gate['question'],
                          status=gate['decision_status'], thresholds=gate['predeclared_thresholds'],
                          limitations=gate['claims_still_forbidden_after_pass'])
        edge(identifier, 'recorded_in', artifact('docs/operator_learning/gates.json'), 'CURRENT_CATALOGUE')
        for prerequisite in gate['prerequisites']:
            edge(identifier, 'depends_on', 'gate:'+prerequisite, 'CURRENT_CATALOGUE')
        for assumption in gate['relevant_assumptions']:
            edge(identifier, 'constrained_by', 'assumption:'+assumption, 'CURRENT_CATALOGUE')
        row = gate_rows[gate['id']]
        for method in row['method_ids']:
            if gate['decision_status'] == 'LOCKED':
                edge('method:'+method, 'proposed_for', identifier, row['attribution'])
            else:
                edge(identifier, 'references', 'method:'+method, row['attribution'])
        if gate['experiment_config'] != 'TO_BE_PREDECLARED_BEFORE_RUN':
            edge(identifier, 'tested_by', artifact(gate['experiment_config']), 'FROZEN_GATE_CONFIG')
            for method in row['method_ids']:
                edge('method:'+method, 'tested_by', artifact(gate['experiment_config']),
                     'AUDIT_CONTEXT_NOT_FULL_IMPLEMENTATION_EQUIVALENCE')
        if gate['evidence_run']:
            run = artifact(gate['evidence_run'])
            edge(artifact(gate['experiment_config']), 'generated', run, 'CATALOGUE_RUN_POINTER_NOT_RERUN')
            edge(run, 'recorded_in', identifier, 'CATALOGUE_EVIDENCE')
        for event in row['historical_events']:
            outcome = node('outcome:'+event['decision']+':'+event['outcome'], 'outcome',
                           event['outcome'], status=outcome_status(event['outcome']),
                           raw_status=event['outcome'], limitation=event['limitation'])
            # Special event labels are explicit decisions, never inferred from process completion.
            if event['outcome'].startswith('FAILED_'):
                nodes[outcome]['status'] = 'FAILED'
            if 'GATE_OPEN' in event['outcome'] or 'SCIENTIFIC_OPEN' in event['outcome']:
                nodes[outcome]['status'] = 'OPEN'
            decision = 'decision:'+event['decision']
            edge(decision, 'has_outcome', outcome, 'PRESERVED_GATE_EVENT')
            edge(decision, 'adjudicates', identifier, 'PRESERVED_GATE_EVENT')
            edge(outcome, 'recorded_in', artifact(event['evidence']), 'PRESERVED_GATE_EVENT')

    for relative in configs:
        config = json.loads((root / relative).read_text())
        experiment = artifact(relative)
        nodes[experiment].update(status=config.get('status', 'RECORDED'),
                                 experiment_id=config.get('id'), kind_of_run=config.get('kind'))
        gate = 'gate:'+config.get('gate_id', '')
        if gate in nodes:
            edge(gate, 'tested_by', experiment, 'CONFIG_GATE_ID')

    # Keep every positive/negative component outcome, without inferring an aggregate pass.
    records = [('fem', r['path'], r['recorded_fields'], r['recorded_sha256'])
               for r in audit['fem_recorded_decision_fields']]
    records.extend(('tracked', r['path'], r['fields'], r['sha256'])
                   for r in audit['current_tracked_report_decision_fields'])
    for origin, path, fields, digest in records:
        identifier = node('record:'+origin+':'+sha(path.encode())[:24], 'record', path,
                          status='HISTORICAL_METADATA', path=path, recorded_sha256=digest,
                          origin=origin)
        edge(identifier, 'recorded_in', artifact('docs/research_audit/snapshot_20261006.json'), 'AUDIT_SNAPSHOT')
        edge(identifier, 'documents', artifact(path), 'HISTORICAL_METADATA_NOT_NEW_ADJUDICATION')
        for field, value in fields.items():
            status = outcome_status(value, field)
            if status == 'RECORDED':
                continue
            outcome = node('outcome:'+origin+':'+sha((path+'#'+field).encode())[:24],
                           'outcome', path+' :: '+field, status=status,
                           field=field, value=value, path=path, scope='RECORDED_COMPONENT_ONLY')
            edge(identifier, 'has_outcome', outcome, 'VERBATIM_RECORDED_FIELD')

    for relative in inputs[4:6]:
        text = (root / relative).read_text()
        for line in text.splitlines():
            parts = [p.strip() for p in line.strip().strip('|').split('|')]
            if len(parts) >= 5 and re.fullmatch(r'(?:OL-C\d+|C-\d+)', parts[0]):
                identifier = node('claim:'+parts[0], 'claim', parts[1], status=parts[2],
                                  evidence=parts[3], limitations=parts[4], path=relative)
                edge(identifier, 'recorded_in', artifact(relative), 'CLAIM_REGISTRY')
        for match in re.finditer(r'^## (OL-C[\w-]+) — ([^\n]+)\n(.*?)(?=^## |\Z)', text, re.M | re.S):
            status = re.search(r'Class: ([A-Z]+)', match[3])
            identifier = node('claim:'+match[1], 'claim', match[2],
                              status=status[1] if status else 'RECORDED',
                              text=match[3].strip(), path=relative)
            edge(identifier, 'recorded_in', artifact(relative), 'CLAIM_REGISTRY')

    for authorization in ('operator_surrogate_authorized_for_da', 'operator_production_authorized'):
        identifier = node('authorization:'+authorization, 'authorization', authorization,
                          status='AUTHORIZED' if state[authorization] else 'NOT_AUTHORIZED',
                          value=state[authorization])
        edge(identifier, 'recorded_in', artifact('docs/operator_learning/state.json'), 'CANONICAL_AUTHORIZATION')
        for gate in gates:
            edge('gate:'+gate['id'], 'required_for', identifier,
                 'NECESSARY_NOT_SUFFICIENT_NO_AUTOMATIC_AUTHORIZATION')

    for identifier, item in list(nodes.items()):
        if item['kind'] in ('decision', 'claim', 'assumption'):
            references(identifier, json.dumps(item, ensure_ascii=False), 'EXPLICIT_IDENTIFIER_OR_PATH_MENTION')
    # Explicitly recorded relationships, not automatic chronological supersession.
    edge('decision:OL-D006', 'supersedes', 'decision:OL-D005',
         'OL-D006_PRESERVES_V1_FAILURE_AND_ADJUDICATES_V2_UNCHANGED_THRESHOLDS')
    edge('decision:OL-D006', 'supports', 'claim:OL-C-G01', 'SCOPED_G01_CLAIM_REGISTRY')
    edge('decision:OL-D002', 'contradicts', 'claim:OL-C005', 'PILOT_SCIENTIFIC_QUALIFICATION_REJECTED')
    updates = json.loads((root/'docs/research_audit/gate_updates.json').read_text())['updates']
    for update in updates:
        decision = 'decision:'+update['decision_id']
        edge(decision, 'adjudicates', 'gate:'+update['gate_id'], 'VERSIONED_GATE_RESEARCH_UPDATE')
        for key in ('evidence', 'method_record'):
            edge(decision, 'references', artifact(update[key]), 'EXPLICIT_GATE_METHOD_EVIDENCE')
        for index, component in enumerate(update['component_outcomes']):
            identifier = node(f'outcome:{update["decision_id"]}:component{index}', 'outcome',
                              component['label'], status=component['status'], cases=component['cases'],
                              evidence=update['evidence'], limitation='Recorded sufficient certification outcome; failed bound does not prove actual error exceeds tolerance')
            edge(decision, 'has_outcome', identifier, 'EXPLICIT_COMPONENT_ADJUDICATION')
    edge('decision:OL-D021', 'supports', 'claim:OL-C016', 'SCOPED_FINITE_CONTROL_NUMERICAL_CLAIM')
    return dict(schema_version=1, generated_from=hashes,
                relation_vocabulary=sorted(RELATIONS),
                limitation='Searchable documentary projection; not independent proof, raw-array revalidation or automatic scientific promotion.',
                nodes=sorted(nodes.values(), key=lambda n: n['id']),
                edges=sorted(edges.values(), key=lambda e: e['id']))


def validate_graph(graph):
    errors = []
    ids = [n['id'] for n in graph['nodes']]
    known = set(ids)
    if len(ids) != len(known):
        errors.append('duplicate graph node IDs')
    for edge in graph['edges']:
        if edge['source'] not in known or edge['target'] not in known:
            errors.append(f"dangling graph edge: {edge['id']}")
        if edge['relation'] not in RELATIONS or not edge.get('attribution'):
            errors.append(f"invalid/unattributed graph relation: {edge['id']}")
    if len({e['id'] for e in graph['edges']}) != len(graph['edges']):
        errors.append('duplicate graph edge IDs')
    return errors


def check_graph(root=ROOT):
    root = Path(root)
    path = root / GRAPH_PATH
    if not path.is_file():
        return ['missing research graph']
    graph = json.loads(path.read_text())
    errors = validate_graph(graph)
    if graph != build_graph(root):
        errors.append('stale research graph: regenerate after reviewing source changes')
    return errors


def search(graph, query='', kind=None, status=None):
    terms = query.casefold().split()
    return [n for n in graph['nodes']
            if (not kind or n['kind'] == kind) and (not status or n.get('status') == status)
            and all(t in json.dumps(n, ensure_ascii=False).casefold() for t in terms)]


def walk(graph, start, depth=1, direction='both', target=None, relations=None):
    """Bounded BFS; visits start once, terminates on cycles, optional shortest path."""
    known = {n['id'] for n in graph['nodes']}
    if start not in known or (target is not None and target not in known):
        raise ValueError('Unknown exact node ID')
    if depth < 0 or direction not in ('both', 'out', 'in'):
        raise ValueError('Nonnegative depth and both/out/in direction required')
    adjacent = {n: [] for n in known}
    for edge in graph['edges']:
        if relations and edge['relation'] not in relations:
            continue
        if direction in ('out', 'both'):
            adjacent[edge['source']].append((edge['target'], edge))
        if direction in ('in', 'both'):
            adjacent[edge['target']].append((edge['source'], edge))
    queue, paths = deque([(start, 0)]), {start: []}
    while queue:
        current, distance = queue.popleft()
        if current == target:
            return paths[current]
        if distance >= depth:
            continue
        for neighbor, edge in adjacent[current]:
            if neighbor not in paths:
                paths[neighbor] = paths[current]+[dict(from_node=current, to_node=neighbor, **edge)]
                queue.append((neighbor, distance+1))
    return None if target is not None else paths
