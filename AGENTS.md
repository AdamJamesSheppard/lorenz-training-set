# Mandatory research context

REQ-RT-001 in RESEARCH_TRACEABILITY.md is mandatory for all project stages.
Read it before new method implementation, experiments or scientific decisions;
missing method/source/outcome traceability blocks qualification and promotion.

Before scientific implementation, analysis, plotting or adjudication, read
SCIENTIFIC_INTEGRITY.md, docs/PROJECT_STATE.md, docs/MATH_PROTOCOL.md and the
current programme's canonical state, claims and decisions. For operator learning
start with docs/operator_learning/README.md and its linked documents.
For assimilation-related work read docs/BAYESIAN_ASSIMILATION_CONTRACT.md.

Never manufacture apparent success, silently substitute Gaussian/GMM state
approximations, exclude difficult legitimate cases based on model outcomes,
relax completed gates retroactively, or use evaluation targets to repair outputs.
Preserve raw evidence, all failure categories and scoped uncertainty. Historical
fixtures do not define the current input population. Gate passes require frozen
criteria and recorded adjudication; documentation changes do not promote gates.

Run python3 scripts/check_operator_learning.py and relevant inexpensive tests.
For scientific gate work consult docs/research_audit/README.md and record the
method/source attribution and applicability gaps for each new outcome.
Use docs/research_audit/GRAPH.md and scripts/research_graph.py to retrieve related
methods, research and positive/negative outcomes; rebuild the graph after reviewed
source changes. Graph connectivity is not proof or new scientific authorization.
For a persistent job, confirm launch and hand back with a measured/provisional ETA;
do not keep a conversation waiting for a scientific run to finish.

## Mandatory ETA and cumulative-job handoff

Before launching computation, calculate and state a measured or provisional
ETA, including the basis and uncertainty. If any job is expected to exceed
one minute, launch persistently when authorized, verify launch, then hand the
chat back immediately with the ETA and when to return. Do not wait for completion.
Apply the same rule to the CUMULATIVE expected runtime of related jobs/checks
in one task: splitting work into many sub-minute jobs does not avoid handoff.
For example, thirty59-second jobs require handoff, not thirty inline waits.
If measured runtime grows beyond the estimate, hand back rather than extend
polling. Do not claim a launch or completion without evidence. When launch is
blocked, state the blocker and do not invent a completion ETA. Implementation
and reading time are separate from compute-job runtime estimates.
