# Integrity audit of operator-learning gates — 2026-10-06

Authority: ../../SCIENTIFIC_INTEGRITY.md; decision OL-D011.
Scope: reviewed all18 current gate definitions, state, distribution/data contracts,
generator register, preparation/governance checks, reconstruction helpers and
historical pilot output/evaluation helpers. This is a policy/control audit, not
an exhaustive forensic rerun of all code, past chats, FEM experiments or claims
about why previous Gaussian choices were made. No gate promoted or threshold
changed. Existing passed decisions retain their original limits.

## Findings

Existing controls preserve failed/superseded evidence, predeclare gates, separate
Gaussian likelihoods from state approximations, and require independent future
evaluation. GMM_REGRESSION is engineering-only and historical, not training
population. Current occupation reconstruction contains no Gaussian/GMM fitting.
This does not excuse historical misalignment; every substitution needs an
explicit scientific role and owner approval rather than agent convenience.

Gaps: generic gate pass wording alone did not distinguish reference validity
from surrogate failure or acceptance-conditioned claims. All-attempt denominator
and intervention/oracle rules were insufficiently explicit. G02 could be read
as requiring individual laws to converge to one shape or agreement across
chaotically diverged burn-in paths. The root policy closes those interpretation
gaps without rewriting past experiments.

Observed implementation: scripts/train_neural_pilot.py applies softplus and
normalization. operator_learning/numerics.py normalizes metric inputs, as do
alignment.distance/density_summary. Historical normalized shape metrics therefore
do not independently measure raw mass defects. Preserve those historical scores;
future qualification must pair raw mass/negativity with normalized shape scores
and report intervention factors. No evidence here establishes covert
target-informed output repair. This limited search is not proof of its absence
from every repository path.

## Gate-by-gate acceptance boundaries

Each entry states acceptable evidence and prohibited promotion. All inherit the
root policy's all-attempt accounting, scoped claims, frozen criteria and owner
authority. The audit is a normative supplement, not an executable experiment.

### OL-G00_PROBABILITY_DISTRIBUTION_ALIGNMENT
Acceptable: owner-approved named input population with gaps and exclusions.
Unacceptable: attractive Lorenz geometry as posterior coverage; convenient
Gaussian/GMM substitution; declaring an application different from the owner's.

### OL-G01_REPRESENTATION_CONTRACT
Acceptable: documented physical transformations, raw invariants and errors.
Unacceptable: normalization hiding mass loss, clipping hiding negative mass,
or conservative export being presented as full-density accuracy.

### OL-G02_RECONSTRUCTION_STABILITY
Acceptable: scoped procedure stability on representative/difficult cases;
separate same-law error, regularization choice and genuinely different paths.
Unacceptable: forcing all densities towards one template, eliminating legitimate
variation, treating every continuum law as tested, or inventing truth/budgets.

### OL-G03_INPUT_DIVERSITY
Acceptable: within-law reconstruction versus between-law structure evidence.
Unacceptable: counting seeds/noisy replicates as independent law coverage,
or extending windows until inputs collapse to one easy occupation density.

### OL-G04_REFERENCE_TARGET_APPLICABILITY
Acceptable: representative new-law accuracy/invariants and unresolved-case ledger.
Unacceptable: inheriting GMM certification wholesale or deleting costly/difficult
targets without recording selection and limits; unresolved targets are not truth.

### OL-G05_EXPORT_FIDELITY
Acceptable: measured shape/dtype/representation loss and physical error budget.
Unacceptable: coarsening or smoothing away discrepancies solely to improve scores.

### OL-G06_DATA_PROVENANCE
Acceptable: source-group splits, hashes, access/exclusion/retry records.
Unacceptable: test-driven preprocessing or related-law leakage; silent replacement
of failed evaluation examples with favourable ones.

### OL-G07_OPERATOR_STRUCTURE
Acceptable: independently propagated mixtures, measured limiter nonlinearity.
Unacceptable: assuming corrected evolution linear, or replacing propagated
mixture targets with linear combinations while claiming an independent test.

### OL-G08_BASELINE_QUALIFICATION
Acceptable: strong tested linear/POD/CNN/FNO alternatives, fair search budgets.
Unacceptable: persistence-only comparison or handicapping competitors to select FNO.

### OL-G09_FIT_FEASIBILITY
Acceptable: explicitly labelled fit/memorization and development ablations.
Unacceptable: training-set fit promoted to generalization, or selecting only easy laws.

### OL-G10_GENERALIZATION
Acceptable: untouched population, counts/uncertainty, failure rates and tails.
Unacceptable: inspected-test tuning, accuracy on accepted-only cases promoted
to unconditional reliability, or finite evidence claimed for every initial law.

### OL-G11_STRUCTURAL_GENERALIZATION
Acceptable: entire source/family holdouts with declared coverage gaps.
Unacceptable: near-duplicate families called unseen, or dropping failed structures.

### OL-G12_PROBABILITY_STRUCTURE
Acceptable: raw/final constraints, full-density/statistical metrics, frozen regions.
Unacceptable: mass/positivity as shape qualification, target-guided lobe/boundary
repair, or hiding false background by unreported masks.

### OL-G13_SEMIGROUP
Acceptable: composed predictions compared with independent2T reference.
Unacceptable: using the prediction as its own reference or correcting intermediate
states from FEM without labelling the method hybrid and counting the cost.

### OL-G14_ROLLOUT
Acceptable: complete trajectories, horizon errors, failures and intervention logs.
Unacceptable: reporting only surviving segments; undisclosed resets to truth.

### OL-G15_ACCURACY_COST
Acceptable: accuracy/cost frontier including corrections, transfer and failures.
Unacceptable: speedup from training timers, omitted FEM rescues or unmatched workloads.

### OL-G16_POSTERIOR_TRANSFER
Acceptable: actual full posterior laws and independently generated forecasts,
under explicit future authorization. Gaussian likelihood is separately specified.
Unacceptable: Gaussian/GMM refit substituted for the full posterior or present
occupation-law scope silently expanded into posterior/DA qualification.

### OL-G17_SEQUENTIAL_INTERFACE
Acceptable: full-density repeated interface, failures/fallbacks and explicit scope.
Unacceptable: hidden reference injections, Gaussian closure or an interface pass
advertised as complete DA success without a separate DA programme.

## Remaining accountability

Before each executable qualification config, specify population, all-attempt
ledger, exclusion categories, interventions, raw/final metrics, split access,
reference uncertainty and reviewer authority. Legacy missing diagnostics remain
missing; this audit does not retroactively certify them. Future implementation
must enforce these requirements for its own runner. Current automated checks
verify policy/audit coverage and authority links, not complete semantic honesty.
