# How the neural model is evaluated

The training code learns a mapping from an initial density field to its forecast. The model combines spectral layers with local convolution paths and coordinate inputs, then constrains the output to be positive and normalised. Evaluation compares the predicted field with the numerical target and with persistence, using density error as well as mean and covariance errors. These measures answer different questions, which is why a better overall field score can still accompany worse statistics. The pilot keeps diffusion and forecast horizon fixed, so it does not demonstrate generalisation across either quantity.

[Implementation or detailed research record](../../scripts/train_neural_pilot.py).
