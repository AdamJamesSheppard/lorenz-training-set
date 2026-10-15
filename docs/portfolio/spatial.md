# What spatial refinement changes

This experiment compares three meshes at a fixed forecast horizon of 0.05, using one Gaussian initial distribution. Reported covariance error falls from 0.0303308 to 0.00233991, while mean relative L1 positivity correction falls from 0.000576400 to 0.00000863921. Within this configuration, the forecast statistics move closer to the comparison reference and less correction is needed. The two measures still have different meanings, and three meshes with one initial distribution do not establish general convergence or accuracy across the intended population.

[Implementation or detailed research record](../../local_q2_spatial_refinement_report.json).
