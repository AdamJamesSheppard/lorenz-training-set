# Owner-controlled scientific objective — bootstrap candidate

Qualify a computational surrogate for the fixed-horizon Fokker–Planck forecast
map S_T:p_0→p_T, initially at fixed Lorenz drift, full-SPD diffusion, reflecting
domain and horizon, over the owner-selected full-density population.

The eventual application is full-density Bayesian assimilation:
p_{k|k}→S_Tp_{k|k}=p_{k+1|k}, followed by an explicitly specified likelihood-based
Bayesian update. No Kalman/variational method or Gaussian/GMM state closure may
silently substitute for the full-density problem. Prior, likelihood, stochastic
model, discretization and approximation assumptions remain explicit.

Regularized deterministic finite-window occupation laws are the current accepted
restricted population. They are not automatically stochastic ensemble laws or
Bayesian posteriors. Their successful prediction cannot conclude posterior
transfer or sequential DA qualification. Broad population coverage remains open.

Every experiment must state demonstrated proposition, forbidden/unestablished
proposition, and why its result advances this objective. Scope changes require
specific owner approval binding the new goal/specification digest; permission
to investigate does not approve a result. This file requires CODEOWNER review
and external signed specification binding. Until separate credentials/trust roots
are provisioned its protection remains incomplete; this text cannot secure itself.
