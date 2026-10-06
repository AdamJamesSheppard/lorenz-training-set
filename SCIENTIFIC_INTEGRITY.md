# Scientific integrity: evidence must be allowed to contradict the project

Effective 2026-10-06; owner instruction recorded as OL-D011. Applies to the
whole repository: FEM/FPE, data generation, operator learning, plots and future
assimilation. Scientific success is an outcome to investigate, never an output
the implementation must manufacture. This policy supplements mathematical and
gate protocols; it grants no run, population-change or production authority.

## Preserve the scientific object

Current accepted operator-learning inputs are regularized finite-window
state-space occupation densities of recorded simulated Lorenz trajectories.
They are full densities, not point states. Calling samples "observed" does not
establish noisy measurement conditioning or real-world observations.

No silent Gaussian/GMM substitution is permitted. Historical Gaussian and
mixture tests remain available as explicitly labelled regression experiments;
they cannot become the principal population by convenience or by inheriting
old certification. Gaussian observation noise/likelihood does not imply a
Gaussian state approximation. A proposed family change needs owner approval,
new generator metadata/version, predeclaration and appropriately scoped gates.

No silent population narrowing is permitted. A scoped study may legitimately
exclude inputs under physical/representation criteria fixed independently of
model results, but must state exclusions, reasons and the resulting claim scope.
Neither an agent nor a model score may redefine the owner's scientific goal.

## Variation and G02

G02 qualifies a reconstruction procedure over a specified scope, not every
conceivable density. Preserve scientific variation in windows, initial states,
lobe occupancy, concentration, filaments, multimodality and tails. Distinguish
that variation from reconstructing the SAME recorded law with different
sampling/histogram/integration choices. Smoothing is part of the declared
regularized law; changing its width can change the law itself.

Representative and difficult cases test the procedure. A finite study supports
only its stated population/conditions, unless a justified uniform mathematical
bound extends the claim. It does not guarantee prediction for every initial
condition. Fresh seeds alone do not establish distinct laws or independence.
Long occupation windows can reduce input diversity; G03 must measure this.

Separately integrated chaotic burn-in paths can yield different numerical
occupation laws. Their disagreement alone does not disqualify either fixed
recorded-law input. Fidelity to one specified continuum trajectory is a stronger
claim needing integration evidence. Finite controls are not automatic truth.

## Acceptance, exclusions and failure accounting

Gate qualification, sample/reference validity and model accuracy are distinct.
Declare each criterion, denominator, scientific rationale and claim before its
qualification run. Characterization may inform a later threshold; it cannot
retroactively qualify its own observations. Retain superseded criteria/results.

Do not silently discard legitimate difficult inputs or failed predictions.
An unresolved/invalid FEM target must not masquerade as accurate ground truth:
retain its attempted sample ID, reasons, diagnostics, costs and unresolved role.
Distinguish out-of-scope samples, corrupt inputs, unresolved references, resource
failures and surrogate failures. Report all attempted/accepted/excluded/failed
counts, exclusions by family/difficulty, retries and conditional performance.
Acceptance-conditioned scores must not be advertised as population-wide scores.
For an unresolvable reference, report missing accuracy evidence, not invented
model error. A budget-limited refinement stops with an explicit limitation.

## Interventions and unaltered evidence

Admissibility mechanisms are legitimate if specified and tested. They include
FEM local-QP projection and neural positivity/normalization layers. They do not
establish shape accuracy by enforcing mass or positivity alone.

Future qualified runs must retain raw/pre-intervention and final diagnostics,
correction magnitude, probability affected, residuals and failures where defined.
For neural models distinguish unconstrained logits/residuals, candidate physical
densities and final outputs; logits need not themselves be densities. Report
normalization factors and intervention ablations where applicable. Frozen
historical metrics retain their original semantics; missing raw diagnostics
are recorded as unavailable, never reconstructed fiction.

No target-informed repair is permitted during final evaluation. Target access
for supervised training is legitimate; using the evaluation target to fit,
smooth, rescale, select a checkpoint, mask support, repair lobes or choose a
prediction converts the experiment to an explicitly labelled oracle diagnostic.
Independent target generation must not use the surrogate prediction as truth.
Physical constraints and training-derived corrections must be frozen before
evaluation and disclosed as part of the method, with their error/cost measured.

## Honest evaluation and presentation

Report full density, moments, marginals, lobes, tails, boundary mass, positivity
and mass. No favourable metric replaces a failed required metric. Freeze regions,
units and tolerances. Include strong linear/POD alternatives; FNO has no preferred
outcome. Preserve failures across methods, hyperparameters, seeds and restarts.

Keep related source groups together in splits; record final-test access. Once
test diagnostics drive a method choice, that set is development evidence for
subsequent claims. A new untouched evaluation population is required. Label
training-fit, validation, stress, diagnostic and final-evaluation roles.

Plots must use identified computed fields, labelled times, physical coordinates,
declared normalization, common scales and masks where comparisons require them.
Never replace a missing density with an attractive synthetic orbit, Gaussian,
reference geometry or auxiliary field. An auxiliary source must be labelled.
For animation verify actual saved-field evolution, not just camera motion.

## Accountability and controls

Preserve immutable runs, input/output/config/source hashes and ignored-evidence
pointers. Phase A predeclares; phase B adjudicates. Failed thresholds remain
failed; an improved experiment gets a new ID and a justification. OPEN and
FAILED are valid outcomes. No gate pass silently unlocks DA or production.

At each adjudication record reviewer, independence, authority, scope, all
required outcomes, exclusions, interventions, counterevidence and limitations.
Audit details: docs/operator_learning/INTEGRITY_GATE_AUDIT_20261006.md.
Fast checks protect document coverage/links and state consistency; they cannot
prove honesty, diagnose every scientific error or certify all execution paths.
Agents must read this policy at task entry; chat history is not its authority.

Reporting/leakage rationale (external guidance, not project gate evidence):
[REFORMS](https://arxiv.org/abs/2308.07832) and
[Leakage in ML-based science](https://arxiv.org/abs/2207.07048).
