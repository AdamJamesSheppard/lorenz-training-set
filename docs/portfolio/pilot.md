# How the simulation examples were produced

This script runs the historical six-case pilot. Each case starts from a distribution formed from sampled Lorenz trajectories, then uses the MFEM solver to forecast that distribution over 0.05 model-time units. The calculation uses 320 steps of 0.00015625 and a fixed diffusion tensor. Four cases are used for training, one for validation and one for evaluation. Positivity, mass and correction checks determine whether a pair can continue through this pilot. These checks help catch unusable outputs; wider reference accuracy still needs its own investigation. The launcher also contains paths specific to the original environment, so it needs configuration before another researcher can use it.

[Implementation or detailed research record](../../mfem/run_neural_pilot.py).
