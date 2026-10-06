# Full-density Bayesian assimilation contract

Owner direction recorded 2026-10-06, OL-D014. This is the eventual application
contract, not permission to begin assimilation or a claim of qualification.

## Forecast and observation update

Propagate the complete posterior density through the qualified FPE forecast
surrogate: p(k|k) → p(k+1|k). Apply the observation update explicitly to that
complete forecast density. For observation history Y(1:k), define the declared
likelihood ℓ_k(x) = p(y_k | x_k=x, Y(1:k-1)). Then

\[
p_{k|k}(x)=\frac{\ell_k(x)p_{k|k-1}(x)}{Z_k},\qquad
Z_k=\int_\Omega\ell_k(z)p_{k|k-1}(z)\,dz,
\quad 0<Z_k<\infty.
\]

Conditional observation independence, if adopted, must be declared before
replacing this likelihood by p(y_k|x_k). The density may retain multimodality,
non-Gaussian tails and cross-coordinate structure; means/covariances are
diagnostics and cannot replace the posterior. Bayes' rule and density updating:
[MIT probability course](https://ocw.mit.edu/courses/18-05-introduction-to-probability-and-statistics-spring-2022/mit18_05_s22_statistics.pdf).

## Prohibited substitutions

Kalman, EKF, UKF, EnKF, 3DVar and 4DVar are excluded as the adopted assimilation
procedure. Gaussian state closure, Gaussian-mixture state closure, moment-only
analysis and optimization-only point estimates cannot replace the full-density
Bayesian update. Historical implementations remain historical evidence.
Any comparator requires explicit scope/authorization; it cannot silently become
the project method. Gaussian observation noise or a Gaussian likelihood does
not impose a Gaussian posterior. No observation model is selected by this file.

## Assumptions and numerical accountability

The research objective is to avoid imposed state-density closure and qualify
an efficient full-density forecast. An assumption-free inference claim is
forbidden: dynamics, diffusion, domain/boundaries, prior, likelihood, observation
operator, reconstruction, discretization and surrogate approximation remain
explicit modelling/numerical commitments requiring evidence.

The neural operator approximates the forecast map. It does not remove Bayes'
rule, learn an undeclared likelihood or guarantee arbitrary posterior fidelity.
Record observation provenance, likelihood parameters, evidence integral,
quadrature/projection error, raw and accepted densities, mass, positivity,
statistical diagnostics and any corrective intervention. Zero/invalid evidence
or numerical underflow must be diagnosed, never repaired by inventing background
probability or changing observation uncertainty to obtain a favourable result.

## Reconstruction reservations

Smoothing is a declared change of probability law. Do not automatically smooth
the posterior after every update: that can widen uncertainty and erase acquired
information. A particle-to-density reconstruction needs its own stated kernel,
weights, bandwidth, boundary treatment and error evidence. An already resolved
FE posterior does not acquire an automatic smoothing step under this contract.
Occupation densities and conditional state uncertainty remain distinct objects.

## Authority

Current stage remains operator-learning qualification. G02 is OPEN; posterior
transfer (G16), sequential interface (G17), and a separately approved Bayesian
assimilation programme remain prerequisites. No DA run, new target campaign,
model retraining or historical evidence rewrite is authorized here.
