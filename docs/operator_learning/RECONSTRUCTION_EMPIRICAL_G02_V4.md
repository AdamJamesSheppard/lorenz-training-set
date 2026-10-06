# G02 empirical-box control v4 — predeclared characterization

No accepted law, historical input or output changes. No FPE target or neural
training is generated. G02 remains OPEN; qualification error budget is pending.

On the six saved mechanism_v3 fine paths define the labelled diagnostic law

    μ_N = (1/N) Σ δ_Xi,
    p_N(x) = (1/N) Σ Π_d [1{|x_d-Xid|≤w_d/2}/w_d],

with fixed widths(4,40/9,40/9). The exact voxel average is the sum of the
individual box/voxel overlap volumes divided by N, kernel volume and voxel
volume. This control has no histogram intermediate, vertex lifting, Gaussian
fitting, shape template, empirical bandwidth tuning or normalization. Boundary
loss is measured raw; a significant defect stops the technical run with preserved
partial evidence rather than being hidden by renormalization. It regularizes the
same finite samples, but is a DIFFERENT construction from the accepted
ATTRACTOR_DENSITY_V1 recipe; no automatic adoption is authorized.

Freeze source20000 samples perseed71029–71034 from mechanism_v3, two conservative
comparison grids60×72×72 and120×144×144. Compare5000 and10000 endpoint-phase
subsamples to20000 direct-box control. Compare historical and exact continuous
histogram-box constructions at histograms45/60/90/120 (y/z1.2 factor) directly
against that control on identical samples. This localizes histogram quantization
versus discretized filter/lifting. All120 comparisons and all six source groups
are retained. No outcome-based exclusions or gate promotion.

Metrics: raw mass/negative mass, density L1/TV, marginal TVs, means/covariance,
lobe/boundary discrepancies. Positive analytic overlap has no clipping/floor.
Existing histogram-box transfer retains its disclosed roundoff floor. Probability
summaries normalize only after raw invariants independently pass. Sample/grid
controls concern specified finite regularized laws; no continuum accuracy,
invariant-law proof, family diversity or universal generalization claim follows.

Competing hypotheses: coarse histogram quantization may dominate; historical
filter/lifting may dominate; both may remain important. The finite empirical
control does not resolve unsampled trajectory variation or justify a bandwidth.
Even favourable contraction cannot qualify its own observations. Results should
inform a precise recipe/budget proposal for owner approval, not another indefinite
sequence of increasingly fine controls. Any production recipe change needs new
generator/representation/reference applicability evidence.

Reference for the empirical kernel-density construction (not scientific pass
evidence): https://www.stat.cmu.edu/~cshalizi/uADA/24/lectures/ch14.pdf.
