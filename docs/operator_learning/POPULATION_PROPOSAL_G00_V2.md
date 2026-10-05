# G00 scoped population proposal — predeclared 2026-10-05

Status: comparison evidence complete; proposal pending owner review. This document
does not accept any family for scientific training or promote G00.
Config: experiments/operator_learning/OL-G00_alignment_v2.json. Version1 draft
is preserved. The user authorized the small alignment study on 2026-10-05.

Results are now recorded in evidence/G00_ALIGNMENT_V2_20261005.md. The proposal
remains unapproved until explicit owner review of its actual population and roles.

## Intended application backwards constraint

Forecast consumes a complete uncertainty density and returns its forecast under
fixed Lorenz drift, D, box and T=.05. Eventual inputs can be observation-conditioned
and have unequal lobe weights, localized concentration, multimodality and tails.
The pilot's deterministic time-occupation laws are valid regularized probability
objects, while their ability to cover this input population remains unverified.

## Proposed roles and boundaries

Occupation laws: historical engineering fixtures and broad-support stress inputs.
Finite-time stochastic ensemble laws: unconditioned forecast-prior comparators,
from explicitly sampled piecewise-constant pilot voxel density, common D/T.
Single-observation conditioned laws: application-directed structural comparators;
explicit independent simulated truth, x/xz/full maps and observation variance
4 or16. They are Bayesian updates for a declared regularized voxel prior, not
certified sequential DA posteriors. No Gaussian/GMM state fitting occurs.
Old GMM laws retain historical FEM regression scope only.

The small comparison uses six source groups, two reconstruction/ensemble
replicates, 16,384 particles per ensemble. All examples are development data.
No number of examples in this study establishes coverage of the eventual filter.
No current generator obtains training/validation/final-evaluation permission.

## Frozen evidence and decision rules

Physical L1/marginal distances, lobe weights, means/covariance, inverse-L2
effective volume, transition/tail/boundary mass. Exact conservative trilinear
integration isolates reconstruction from FE projection; the remaining difference
is reported, rather than assumed zero. Moving-block resampling is a sensitivity
diagnostic with a fixed 50-sample block, not a G02 confidence interval.

Single-time ensembles use Euler--Maruyama without reflection. Every path exit
is rejected; this prevents silently substituting boundary clipping and does not
certify reflecting-versus-whole-space equivalence. Particle count, timestep,
histogram/smoothing and likelihood/voxel biases are explicit open limitations.

Mass tolerance 1e-10 and zero negative mass reuse numerical sanity expectations;
they do not qualify population alignment. Family-difference magnitudes are
descriptive, with no invented universal coverage threshold. Within-replicate
variation is compared with conditioning shifts as a heuristic only.

Technical evidence can complete without a scientific gate pass. After results,
the owner must approve the intended population, roles and exclusions. Approval
permits only G01 representation qualification; it does not permit a large dataset,
neural qualification, posterior transfer or operator-assisted DA.
