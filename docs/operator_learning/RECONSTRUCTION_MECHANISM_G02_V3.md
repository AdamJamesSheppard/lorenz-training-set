# G02 mechanism characterization v3 — predeclared diagnostic

Retain all original density recipes and arrays. G02 OPEN; no scientific budget
or qualification pass is introduced. Source: refinement_v2 sealed paths, six
development seeds71029–71034. The first saved dt=.0005 post-burn-in state is the
identical starting state for both new ten-unit trajectories. This isolates
additional forecast-window integration sensitivity from differing burn-in states;
it still does not eliminate chaotic amplification over the ten-unit window.

Compare dt=.001/.0005 at matched5000 physical sample times, reporting pointwise
path differences and density metrics. Then hold the20000-point fine path fixed
and compare histogram45/60/90/120 (y,z counts scaled1.2) at fixed physical widths
(4,40/9,40/9), on both60×72×72 and120×144×144 conservative grids.

Competing hypotheses: noncontraction can reflect histogram bin placement,
discretized convolution, vertex lifting or missing resolution. A labelled
alternative control integrates continuous piecewise-constant histograms
convolved with the SAME top-hat exactly onto voxels, without vertex lifting.
This control is not a replacement accepted input, new Gaussian fit or FPE target.
The rectangle-integral formula uses H(z)=max(z,0)^2/2. Its mass is measured before
any normalization; significant boundary loss causes a preserved technical failure.
Numerical cancellation floor is limited to transfer entries within1e-10 below
zero, tested by an analytic triangular-density fixture; no model output is repaired.
SciPy's historical convolution conventions:
https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.convolve1d.html.

132 comparisons: perseed/pergrid one integration, four architecture and six
adjacent-histogram comparisons. All attempted cases remain in evidence; technical
failure retains partial report and attempted/completed accounting. No exclusions
based on favourable metrics. Raw mass, negative mass, density L1/TV, marginal TVs,
means/covariance, lobes and boundary differences are recorded. Normalized shape
metrics cannot conceal raw defects because raw invariants are checked separately.
Finite histograms/grid references are controls, not continuum truth. No formal
order, universal initial-condition coverage, population change or gate promotion.

Commit config/source hashes before CPU-only execution; seal arrays/report and
record all attempts. Preserve v2 results: their96 comparisons completed, raw
mass defect8.88e-16, but histogram differences did not contract and burn-in
integration sensitivity was confounded with diverged numerical trajectories.
Any later scientific criterion needs a new justified predeclaration.
