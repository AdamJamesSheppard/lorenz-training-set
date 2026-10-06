# G02 qualification proposal v2 — DRAFT, NOT EXECUTABLE PREDECLARATION

The accepted scientific object remains a regularized finite-window occupation
law from recorded simulated Lorenz states. Original ATTRACTOR_DENSITY_V1 and
all historical pairs remain unchanged. A replacement recipe needs its own ID
and representation verification; this proposal does not authorize substitution.

## Controlled next study

Candidate sampling: 5000 uniform-time points over the same ten-unit window,
burn-in20, RK4 dt=.001. Historical histogram45×54×54 and physical top-hat width
remain the starting regularization definition, not presumed converged choices.
Use six fresh development seeds71029–71034; they are qualification-development
cases, never advertised as untouched final model-evaluation inputs.

Separate three numerical questions:

1. Temporal sampling: compare5000,10000,20000 points on one fixed dt=.0005 path,
   with declared phases. Report L1/TV, marginals, mean/covariance and lobes.
2. ODE integration: compare dt=.001 and dt=.0005 at identical physical sample
   times and initial states. Accumulated path differences are finite-horizon
   integration sensitivity, not independent input-law diversity.
3. Reconstruction: compare histogram45×54×54,60×72×72,90×108×108 at the SAME
   physical smoothing width. Report lifting dependence explicitly. Evaluate on
   one declared conservative grid, and verify that grid does not hide measured
   differences using a finer comparison grid. This diagnostic does not pass G05.

Freeze a budget split between sampling, integration and reconstruction BEFORE
qualification, with total density TV tied to the intended surrogate-accuracy
goal. Triangle inequalities can bound the sum of measured discrepancies, but
finite reference differences alone do not bound continuum error without a
justified reference-tail estimate. Require contraction and report residual
reference uncertainty; do not identify a finite control with truth.

## Approval still required

Scientific density-TV budget: TO_BE_PREDECLARED_BEFORE_RUN.
Component/statistical tolerances: TO_BE_PREDECLARED_BEFORE_RUN.
Approved final histogram/physical regularization: UNRESOLVED.
Candidate5000 sampling is supported by characterization, not qualified.

Owner should approve an intended density-TV accuracy goal or explicitly
authorize a second characterization to estimate the finer-reference tail.
No numerical pass threshold is inferred from the observed FNO error. Once
approved, create immutable config, tests, phase-A commit, fresh run, and phase-B
adjudication. A draft has no dispatch authority and cannot unlock G03.
