# Searchable research provenance graph

Owner request, 2026-10-06, OL-D018. Includes successful outcomes with the same
traceability as failures, open studies, insufficient evidence and superseded
decisions. Scientific state and authorization are unchanged.

## Scientific and engineering definition

Method PROVENANCE_GRAPH v1 is an engineering index: typed nodes/edges projected
deterministically from versioned audit/method registers, gate/state files,
decisions, claims, assumptions and experiment configs. Search uses AND-matching
text terms and exact type/status filters; traversal uses bounded breadth-first
search, including cycle handling. No database service or external dependency.

Research context: [W3C PROV overview](https://www.w3.org/TR/prov-overview/) and
[primer](https://www.w3.org/TR/prov-primer/). The project uses a custom schema,
with no claim of PROV conformance. Full method/source/assumption/test attribution:
graph_sources.json. Serious alternative: relational/SQLite or RDF indexing;
deferred because the current Git-backed register is small and direct queries
cover current needs. Interactive graph visualization is also deferred; the
searchable relationships do not depend on a layout or GUI.

## Files and authority

- `graph.json`: tracked generated graph, stable namespaced node IDs and typed,
  attributed edges. Never edits a source report or historical audit snapshot.
- `operator_learning/research_graph.py`: deterministic projection and queries.
- `scripts/research_graph.py`: local CLI for rebuild/check/search/traversal.
- `graph_sources.json`: versioned engineering method/research record.

Source hashes identify exact graph inputs. Governance CI rebuilds in memory and
fails on stale projections, dangling endpoints, invalid/unattributed relations
and duplicate IDs. A graph is an index of recorded evidence, not independent
verification of ignored arrays, a proof engine or automatic gate-promotion logic.

## Node and relationship meanings

Node types include source, method, assumption, experiment, run, artifact, record,
decision, outcome, gate, claim and authorization. IDs such as `source:OL-NUMPY`,
`method:REPRESENTATION`, `decision:OL-D006` and full gate IDs remain explicit.
Historical component outcomes have IDs derived from origin/path/field, so both
positive and negative results persist without creating an invented aggregate pass.

| Relation | Direction / meaning |
|---|---|
|informed_by|method → source; attribution may be contextual or retrospective; no proof implied|
|implemented_by|method → implementation artifact|
|proposed_for|method → locked gate; not evidence of implementation or a pass|
|tested_by|gate/method → recorded experiment; contextual scope disclosed|
|generated|experiment → recorded run pointer; not a new run or reproduced result|
|recorded_in / documents|record → source artifact, or metadata record → described artifact|
|adjudicates / has_outcome|decision → gate / decision or record → outcome|
|references|explicit documentary reference or recorded contextual association|
|depends_on / constrained_by|gate → prerequisite / declared assumption|
|supports / contradicts|explicitly documented scoped claim relationship; never created merely because a paper is cited|
|supersedes|explicit preserved supersession, e.g. G01v2 decision after v1 failure|
|required_for|gate → authorization; necessary prerequisite, never automatic permission|

Outcome `PASSED` or `FAILED` represents an explicit recorded classification or
individual gate-pass boolean. `TECHNICAL_COMPLETED` is process completion, not
scientific success. `OPEN`, `LOCKED`, evidence classes and literal historical
statuses remain distinguishable. Parent records with mixed fields retain
`HISTORICAL_METADATA`; successful components do not turn the parent into a pass.
Copies in the FEM snapshot and current tracked report can describe the same
experiment: search-result counts are index counts, not independent experiment
counts. Run availability is labelled local/ignored and not reverified by the graph.

## Commands

Run from repository root with `python3`:

```bash
python3 scripts/research_graph.py --search 'positivity'
python3 scripts/research_graph.py --kind outcome --status PASSED
python3 scripts/research_graph.py --kind outcome --status FAILED
python3 scripts/research_graph.py --kind gate --status OPEN
python3 scripts/research_graph.py --show method:QP
python3 scripts/research_graph.py --neighbors gate:OL-G01_REPRESENTATION_CONTRACT --depth 2 --limit 50
python3 scripts/research_graph.py --path source:OL-NUMPY outcome:OL-D006:PASSED_V2_UNCHANGED_THRESHOLDS --depth 5 --relation informed_by --relation tested_by --relation adjudicates --relation has_outcome
python3 scripts/research_graph.py --check
```

Traversal defaults to both directions so documentary chains can be explored.
Path output retains each edge's original direction, relation and attribution;
a traversable route is not a logical implication. Use `--direction out` or `in`
and repeated `--relation` filters for narrower questions. `--json` returns full
search/neighborhood data; `--limit` controls display and total matches are stated.
Unknown IDs fail explicitly; no path within a depth cap says nothing about paths
beyond that cap. Queries preserve successes and failures without re-ranking them.

## Maintenance

After reviewed source changes, run `python3 scripts/research_graph.py --build --check`,
inspect the Git diff and commit the projection with the source changes. This only
regenerates the current graph. Earlier research audit/run snapshots remain intact.
New curated scientific links need explicit recorded attribution, not inference
from chronological proximity or favourable outcomes. Extend evidence/research
records before adding unsupported graph relationships.
