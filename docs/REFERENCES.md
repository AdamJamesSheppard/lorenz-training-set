# References

## Numerical method

- Liu, Hu, Taitano, and Zhang (2025), "An optimization-based
  positivity-preserving limiter in semi-implicit discontinuous Galerkin schemes
  solving Fokker--Planck equations," DOI: 10.1016/j.camwa.2025.05.008. Basis for
  the two-stage conservative positivity construction; applicability is audited
  in `POSITIVITY_AUDIT.md`.
- Liu and Yu (2014), maximum-principle DG for potential-driven Fokker--Planck;
  Srinivasan, Poggie, and Zhang (2018), positivity-preserving LDG for
  convection--diffusion; Kuzmin and collaborators, multidimensional AFC/FCT;
  Quenjel (2022), positive Scharfetter--Gummel DDFV; Fok, Guo, and Tang (2002),
  Hermite Fokker--Planck approximation. Exact links and theorem-applicability
  limits are recorded in `METHOD_SELECTION_REPORT.md`.
- Itkin's Diagonal Frog, FCDF, and DF-ADI works (arXiv:2606.23980,
  arXiv:2607.20415, and arXiv:2608.22703) are treated as recent preprints. Their
  lower-dimensional validation and mixed-diffusion qualifications are recorded
  in `METHOD_SELECTION_REPORT.md` rather than promoted to production evidence.
- Boudaoud, Caruso, and Roy, together with Leroy's subdivision analysis, define
  strict Bernstein positivity certificates; Sloth
  (arXiv:1710.05735), a non-negative counterexample without a subdivision
  certificate, define the scope of adaptive Bernstein diagnosis.
- `../Fenics Book.pdf` (local, intentionally not tracked): background and
  implementation reference for DOLFINx/FEM and DG advection--diffusion.

## Workspace design sources

- `../sources/Agent_Legible_Math_Data_Science_Linux_Guide.pdf`: primary setup
  guide for numerical simulation, mathematical invariants, experiment records,
  and compact summaries.
- `../sources/Agent_Legible_Mathematical_Research_Linux_Guide_v2.pdf`: claim and
  assumption discipline for mathematical research.
- `../sources/Agent_Legible_Software_Development_Linux_Guide.pdf`: supporting
  repository, validation, and environment practices.

## Historical project conversation

- `../sources/Chat Response/Check FPE Lorenz File.md`: exported development and
  review history. It records why validation was repaired, why Q1 is only a
  comparator, why the current Q2 result is inconclusive, and which challenger
  families remain open. The conversation is evidence context, not canonical
  state; current conclusions belong in the living documents above.
# External visualization utility

- `../sources/animate_fokker_planck_runs.py` (2026-09-13): local utility for
  reconstructing side-by-side MP4s from immutable per-timestep coefficient
  archives and terminal PNG summaries from completed run exports. The script
  records the distinction between pre-correction histories and terminal
  corrected arrays in its generated `inventory.json`. A deterministic Lorenz
  orbit is drawn as explicitly labelled geometric context because the archived
  forecasts last only `0.05` time units and do not traverse the attractor.
  SHA-256: `973ef411f078629ad166e52912e481609e242a04b3a32164be7b61c53f8a0636`.
