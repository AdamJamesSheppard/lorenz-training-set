# Probability and distribution contract — version 1

Integrity authority: ../../SCIENTIFIC_INTEGRITY.md. G02 qualifies the declared
reconstruction procedure within scope; it does not suppress genuine variation
or require every input law to approach one attractor-density template. Scope,
physical regularization and owner approval govern any population change.

Owner-selected current family: [ATTRACTOR_DENSITY_V1](ACCEPTED_POPULATION_V1.md).
Its concrete law-to-tensor transformations and numerical verification scope are
specified in [representation contract v1](REPRESENTATION_CONTRACT_V1.md).
Acceptance of this restricted population leaves actual posterior relevance open.

## Representation chain

- μ: underlying probability measure, defined by process, time and conditioning.
- μ_N = N⁻¹ Σ δ_Xi: empirical particle measure; no automatic volume density.
- Temporal occupation measure: time-averaged state occupancy over a specified
  window; correlated trajectory samples approximate this object.
- Finite-time ensemble law: distribution of X(t) from a specified initial
  ensemble under declared deterministic/stochastic dynamics, at ONE time.
- p: Lebesgue density if it exists, or explicitly regularized density Rμ_N.
- p_h: accepted FE approximation after projection/admissibility treatment.
- P_V p_h: voxel AVERAGES |V|⁻¹ ∫V p_h, not point values or voxel probabilities.
- u: actual algorithm tensor, e.g. float32(384000 P_V p_h) in the historical pilot.
  Record axes, volumes, scaling and dtype; inverse scaling recovers density.

Stochastic state law describes the SDE state random variable. A Bayesian prior
is BEFORE specified observations; a posterior is conditioned on them via a
declared likelihood and normalization evidence. Neither label denotes a
particular shape. A Gaussian likelihood/observation noise model differs from
a Gaussian STATE approximation. Gaussian-mixture STATE approximations also
change the represented law. Eventual intent is full-density transfer without
imposed Gaussian or mixture state refitting.

FE and voxel representations approximate a law; coefficients/arrays are not
interchangeable without a documented conservative mapping. Export can lose
subvoxel information and need not define an invertible FE representation.
Consequently a unique universal voxel-input forecast cannot be assumed absent
a declared lifting/representation class.

## Mandatory generator metadata

Every generator record must contain GENERATOR_ID, probability_interpretation,
underlying_process_or_random_variable, sampling_procedure, conditioning_procedure,
density_reconstruction, regularization, parameters, known_bias,
intended_scientific_role, allowed_for_engineering_tests, allowed_for_training,
allowed_for_validation, allowed_for_final_evaluation, representativeness_status.
Parameters include seeds, horizon/window, ensemble initialization, noise,
observation model where present, sample dependence and reconstruction settings.
Explicit "none" or "unverified" is preferable to silently omitted information.

## Initial generator register (generators.json)

OCCUPATION_PILOT_V1: deterministic RK4 trajectory, 20-unit burn-in, ten-unit
occupation window, 1000 correlated samples at .01 interval; histogram 45×54×54,
three-cell compact smoothing, positive trilinear reconstruction, FE projection.
No Gaussian fit; no old 16-component GMM. Occupation-to-posterior relevance,
stationarity, effective sample size and reconstruction stability are unverified.
Allowed only for historical reproduction and development diagnostics; broader
scientific training/validation/final evaluation await G00 and later gates.

STOCHASTIC_ENSEMBLE_PROPOSAL and POSTERIOR_PROPOSAL: proposed comparison families,
not generated datasets. Define initial law/process/time or prior/likelihood/
conditioning before use. G00 may inspect small examples without initiating DA.

GMM_REGRESSION: retain old explicitly configured mixture laws for FEM regression
and historical comparisons. They do not silently define the new population.

## G00 comparison implementations (2026-10-05)

The proposal IDs above remain proposals, not blanket accepted families.
`STOCHASTIC_ENSEMBLE_G00_V2` and `CONDITIONED_VOXEL_G00_V2` are implemented
small comparison versions, registered with actual sampling/conditioning metadata.
See evidence/G00_ALIGNMENT_V2_20261005.md. They have engineering permission only;
application alignment and scientific dataset roles await owner review.
Their voxel arrays remain full state-space densities, including after likelihood
conditioning. None is a Gaussian/GMM state approximation or a sequential DA result.
