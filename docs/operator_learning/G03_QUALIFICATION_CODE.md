# G03 prospective evaluator: proposed rule, no adjudication

The owner approved law-diversity scope in OL-D030. This implementation does
not freeze an experiment, approve thresholds or promote existing evidence.

`operator_learning/diversity_qualification.py` evaluates explicit attempted-law
records and every unordered pair. Each law must have valid finite reconstruction
controls, raw mass, measured negative mass and a declared source identifier.
Missing attempts, missing pairs and failed controls block eligibility. Duplicate
laws and ambiguous pairs remain in the report without exclusion.

The proposed engineering acceptance rule requires each retained law to have
at least one resolved cross-source witness, after subtracting both finite-control
TV bounds and mass allowances. This establishes non-collapse under those controls.
It does not count independent laws, prove diversity sufficient for learning,
establish optimum coverage or certify continuum accuracy. Many repeated laws plus
one different law can satisfy this narrow rule; report ambiguity alongside it.
Source labels identify generation provenance, not independent attractors.

Threshold values are mandatory caller inputs and must be committed with the
population, seed list, exact reconstruction, runtime and provenance before any
new qualification run. The function always returns gate_status OPEN. Eligibility
requires subsequent scientific review; it never authorizes training or targets.
Historical v1/v2/v3 data remain characterization and diagnostic evidence.

Method attribution: project-designed operational non-collapse rule; TV triangle
inequality motivates subtraction of reconstruction controls. Mathematical context:
https://ccanonne.github.io/files/compx270-chap11.pdf . No independent-sample rate,
continuum error certificate or statistical independence result is imported for
correlated Lorenz occupation samples. The existing coupling controls retain their
limitations recorded in WINDOW_LOCAL_CONTROL_G03_V3.md. Outcome: implementation
only; scientific qualification OPEN. Tests exercise missing evidence, duplicates,
failed controls, invalid metrics and source dependence using synthetic fixtures.

Continuation2026-10-09: G03_QUALIFICATION_V4.md prospectively freezes this rule
for fresh evidence under OL-D031, with full Git access restored. The evaluator
itself still supplies no provenance verification or automatic gate promotion.

Read-only command: `python -m operator_learning.diversity_qualification evidence.json`.
The JSON contains `laws`, `pairs`, `expected_ids`, and `thresholds` with
`reconstruction_tv_max` and `mass_error_max`. The module docstring specifies row
fields. Output goes to stdout; archived evidence is never rewritten. This CLI
evaluates supplied metrics; it does not verify hashes or freeze an experiment.
Only the subsequent provenance-checked dispatch/review may establish those facts.
