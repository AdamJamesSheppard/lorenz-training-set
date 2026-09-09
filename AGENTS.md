# Agent entry point

## Purpose

Research code for reliable Lorenz-63 Fokker--Planck forecasts, Bayesian data
assimilation, and conservative dataset generation. DOLFINx is the current main
implementation, not a permanent restriction: well-justified challenger and
reference methods are part of the research scope.

## Read first

- `docs/PROJECT_STATE.md`
- `docs/MATH_PROTOCOL.md`
- `docs/MATHEMATICAL_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/RESEARCH_DIRECTIONS.md`
- `METHOD_SELECTION_REPORT.md` for the current numerical decision

Read deeper documentation only when it is relevant to the task.

## Standard commands

- Bootstrap/update environment: `./scripts/bootstrap`
- Compact context: `./scripts/context`
- Routine health: `./scripts/check`
- Scientific invariants: `./scripts/verify-math`
- Repository map: `./scripts/repo-map`
- Configured run: `./scripts/run-experiment experiments/<name>.yaml`

## Scientific rules

- Numerical evidence is not a proof or a production certification.
- State assumptions, domains, norms, discretization, and tolerances.
- Changes to boundary conditions, fluxes, polynomial degree, limiter,
  quadrature, observation model, parameterization, or even method family are
  welcome when scientifically motivated. Make them explicit, preserve a fair
  comparator, and update the relevant specification, assumption, test, and
  provenance records.
- Use the evidence labels in `docs/CLAIMS.md`.
- Cite assumption IDs from `docs/assumptions.yaml` when they matter.
- Do not claim novelty without a literature search.
- The current method status is `INSUFFICIENT_EVIDENCE`; do not generate a
  large training dataset unless the predeclared decision gates pass and the
  project state is explicitly updated.

## Living research policy

- Every version-controlled file in this repository, including this one, may be
  edited when the task or new evidence makes it stale. Future agents are
  explicitly invited to improve code, tests, documentation, experiments,
  architecture, assumptions, and method choices.
- Treat present restrictions as current safeguards or defaults, not timeless
  truths. The mathematical target, evidence standards, preservation of raw
  data, and honest provenance are durable; particular solvers, rankings,
  thresholds, layouts, and workflows are revisable.
- The Q1 DG/SIPG solver is an interim baseline and controlled comparator. Do
  not optimize only that path by default. Consider repaired high-order DG,
  local/convex positivity, adaptive Bernstein certification,
  Scharfetter--Gummel/complete-flux or FCDF methods where applicable,
  characteristic methods, goal-oriented refinement, spectral references,
  Monte Carlo density reconstruction, and hybrids.
- A priority ranking is a hypothesis about where to investigate next, not an
  instruction to ignore alternatives. Branch when assumptions or evidence
  favour another route.
- When changing a safeguard or decision threshold, record why and do so before
  evaluating the result whenever possible. Never relax a criterion merely
  because a completed run failed it.
- Supersede stale conclusions instead of silently deleting their history.
  Keep `docs/PROJECT_STATE.md` short and current, and move durable changes into
  `docs/CLAIMS.md`, `docs/DECISIONS.md`, and `docs/assumptions.yaml`.

## Modification rules

- Inspect `git status` and `git diff` before and after edits.
- Preserve raw data and immutable run records.
- Make the smallest change that satisfies the task.
- Do not treat existing code or folder boundaries as sacred. Refactors and new
  method modules are welcome when they improve correctness, comparison quality,
  or research agility and are validated proportionately.
- Add a regression test for numerical or software bug fixes when feasible.
- Run targeted checks during development and the relevant authoritative check
  before concluding.
- At the end of material work, check whether the project state, research
  directions, assumptions, claims, decisions, commands, or generated repository
  map became stale; update each affected file in the same change.

## Minimum change logging

- First determine whether each changed path is tracked, untracked, or ignored.
  Use `git status --short --ignored`, `git ls-files --error-unmatch -- <path>`,
  and `git check-ignore -v -- <path>` when the answer is unclear.
- For tracked files, Git is the change log. Do not create a duplicate diary.
  Ensure every task change appears in `git diff`, then commit it with a concise
  message that states the purpose. A working-tree edit is not logged until it
  is committed.
- `docs/assumptions.yaml`, `docs/CLAIMS.md`, `docs/DECISIONS.md`, and the other
  living documents are tracked. Their ordinary edits need only the Git commit.
  When an assumption change alters the model, applicability, interpretation,
  candidate ranking, or acceptance gates, also record the reason in
  `docs/DECISIONS.md` and update affected claims/project state. Do not add that
  extra semantic record for spelling or non-substantive clarification.
- Never leave a meaningful new file merely untracked. Either add and commit it,
  or intentionally ignore it and apply the appropriate rule below.
- Ignored caches, temporary files, and disposable local logs need no durable
  record when they are reproducible and are not used as scientific evidence.
- Ignored `runs/`, `results/`, `.npy`, `.npz`, HDF5/XDMF/BP data, or logs that
  are used as evidence must have a durable record without committing the large
  payload merely for logging. Prefer a new immutable timestamped run containing
  the exact config, Git commit and dirty state, command, environment/package
  versions, seeds, status, diagnostics, and hashes or immutable versions of
  external inputs. Add or update a compact tracked manifest, report, experiment
  specification, claim, or decision that points to the evidence and records
  the conclusion.
- Do not overwrite an ignored dataset or evidence run in place. Create a new
  version/run. When regenerating sample or training data, update the tracked
  schema/manifest/diagnostic summary with code revision, configuration, seeds,
  acceptance status, and content hashes where practical.
- External/local references such as `Fenics Book.pdf` and files under
  `../sources/` are not covered by this repository's Git history. Do not edit or
  replace them silently. If an agent changes or updates one, record its path,
  source/version or date, and checksum in a tracked reference or decision file.
- Before concluding, run `git status --short --ignored`; account for every
  task-created path, commit all tracked task changes, and report the commit plus
  any intentionally ignored evidence location. Preserve unrelated user changes.

## Output rule

For technical tasks report the result, evidence, validation run, and remaining
uncertainty.
