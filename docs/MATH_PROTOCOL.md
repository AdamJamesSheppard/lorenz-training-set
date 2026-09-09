# Mathematical reasoning protocol

1. Normalize the target statement and define every space, domain, norm,
   boundary condition, parameter, and quantifier that affects it.
2. List active assumptions and the dependencies of non-universal constants.
3. Distinguish rigorous derivation, imported established results, numerical
   evidence, empirical observations, heuristics, conjectures, and open points.
4. Do not infer truth from failure to find a counterexample.
5. Treat symbolic and numerical computation as falsification or consistency
   evidence unless it is itself part of a justified proof.
6. Do not exchange limits, integrals, derivatives, expectations, sums, or
   unbounded operators without checking the necessary conditions.
7. For every imported theorem, record the exact formulation and audit each
   hypothesis against a project fact.
8. For numerical PDE claims, record the mesh, polynomial degree, flux,
   timestepper, timestep, quadrature, limiter, domain, tolerances, and reference.
9. State `PROOF GAP` or `OPEN` when a step cannot be justified; never bridge it
   with plausible prose.
10. Promote durable conclusions into `docs/CLAIMS.md`, `docs/DECISIONS.md`, or
    `docs/PROJECT_STATE.md`; chat history is not canonical state.
11. Maintain at least one serious competing hypothesis during method selection.
    Try to falsify the preferred route and compare methods on identical physical
    problems rather than improving only the incumbent.
12. Treat method rankings, tolerances, and implementation choices as dated,
    revisable conclusions. Preserve the evidence that supported an old choice,
    mark it superseded when necessary, and update the current summary.
13. Before finishing material work, search the living documents for statements
    made stale by the change. A correct new result with stale canonical context
    is an incomplete research update.
