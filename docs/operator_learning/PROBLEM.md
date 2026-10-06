# Scientific problem — version 1, 2026-10-05

Construct and qualify a computational surrogate for the fixed-horizon
Fokker–Planck forecast map over probability densities relevant to the eventual
Lorenz Bayesian-assimilation forecast problem.

## Current operator

For Ω = [-30,30] × [-40,40] × [-10,70], fixed Lorenz drift
f=(10(y-x), x(28-z)-y, xy-(8/3)z), fixed
D=[[1,.4,.2],[.4,1,.3],[.2,.3,1]], and T=.05:
∂t p = L* p = -div(fp) + div(D grad p), (fp-D grad p)·n=0.
D=BBᵀ/2. This bounded reflecting problem approximates a whole-space stochastic
model; boundary insensitivity must be checked, not assumed.

S_T: p0 ↦ pT, initially on a declared application-relevant subset of
{p∈L¹(Ω)∩L²(Ω): p≥0, ∫Ωp=1}. The initial restricted family is the owner-approved
attractor-derived population in ACCEPTED_POPULATION_V1.md. Its reconstruction
stability/diversity and relevance to actual DA posterior inputs remain unverified.
Well-posedness and regularity assumptions apply to any continuum claim.
Data targets are accepted discrete FE forecasts and conservative exports.

## Eventual application and stage boundaries

FEM/FPE reference development → operator-learning qualification →
surrogate forecast qualification/posterior transfer → operator-assisted DA.
Current stage is operator-learning qualification, with later stages LOCKED.
The eventual input is the COMPLETE posterior p(k|k), forecast to p(k+1|k).
A Gaussian likelihood does not require Gaussian or mixture state closure.
The [full-density Bayesian contract](../BAYESIAN_ASSIMILATION_CONTRACT.md)
requires explicit likelihood-times-prior updating; Kalman/variational and
Gaussian/GMM state-closure substitutions are excluded. Neural forecasting
retains explicit model and numerical assumptions; no assumption-free claim.

Lorenz-like state-space geometry alone is not evidence that a proposed input
law belongs to the application-relevant probability population.

## Operator structure

For fixed physics, the PDE is linear in p:
S_T(ap+bq)=aS_Tp+bS_Tq on its linear function-space domain; convex mixtures
remain probability densities. Nonlinear f(x) does not invalidate this identity.
Positivity correction makes the numerical pipeline potentially nonlinear.
G07 measures the mixture defect in a specified physical norm.

## Current non-claims

No complete DA performance, arbitrary-density coverage, parameterized D/T
generalization, recurrent stability, continuum surrogate accuracy, production
replacement of MFEM, or application-representative training-law coverage.
A neural fit to numerical targets cannot establish a smaller continuum error
than those targets' unresolved reference error. Mass/positivity alone are insufficient.
