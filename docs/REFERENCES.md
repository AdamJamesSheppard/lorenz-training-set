# References

## Numerical method

- Liu, Hu, Taitano, and Zhang (2025), "An optimization-based
  positivity-preserving limiter in semi-implicit discontinuous Galerkin schemes
  solving Fokker--Planck equations," DOI: 10.1016/j.camwa.2025.05.008. Basis for
  the two-stage conservative positivity construction; applicability is audited
  in `POSITIVITY_AUDIT.md`.
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
