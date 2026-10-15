# Comparing runtime and numerical correction

This comparison asks whether changing where the mesh spends its resolution can reduce the cost of a mature-density forecast. The uniform calculation takes about 69.4 minutes and the coarse graded calculation about 32.6 minutes, but their mean relative corrections remain close, at roughly 0.0831% and 0.0838%. The coarse graded branch fails its recorded correction criterion. The runtime saving is useful, although the correction result leaves its suitability unresolved. These timings apply to the recorded configurations and environment.

[Implementation or detailed research record](../../mature_graded_efficiency_report.json).
