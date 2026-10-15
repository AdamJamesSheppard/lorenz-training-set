# What the validation tests check

These tests exercise small analytic benchmark problems for diffusion, advection–diffusion and a non-Gaussian initial distribution. They check mass conservation and non-negativity; the first two also use a broad L1 error bound of 0.8. This makes them useful for catching basic failures, but too limited to establish the accuracy of the full research pipeline. Passing them does not qualify the MFEM pilot, the neural operator or long-term forecasts. The test file shows the precise checks rather than implying a broader result.

[Implementation or detailed research record](../../tests/test_validation.py).
