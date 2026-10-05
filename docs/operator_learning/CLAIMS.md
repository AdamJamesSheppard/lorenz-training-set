# Operator-learning claim registry

Classes: ESTABLISHED (derivation under stated assumptions), NUMERICAL (numerical
experiments), EMPIRICAL (observed data behaviour), HEURISTIC, CONJECTURE, OPEN,
REJECTED. Software tests alone never prove an unrestricted scientific statement.

| ID | Claim | Class | Evidence | Falsification / limitation |
|---|---|---|---|---|
| OL-C001 | Fixed-physics continuum FPE evolution is linear in p | ESTABLISHED | PROBLEM.md linear PDE/BC; OL-A01 | Requires well-posed linear evolution; numerical limiter may break identity |
| OL-C002 | Deterministic empirical-attractor generator produces application-representative learning laws | OPEN | G00; DISTRIBUTION_CONTRACT | Attractor geometry alone is insufficient; posterior concentration/conditioning may differ |
| OL-C003 | Six pilot laws generated accepted numerical targets and CUDA training completed | EMPIRICAL | evidence/PILOT_20261004T133438Z.json | Operational acceptance, not continuum accuracy or coverage |
| OL-C004 | Pilot model reduces density L1/L2 versus persistence on its six cases | EMPIRICAL | Historical evaluation.json | Four training cases, one validation, one inspected test; no population guarantee |
| OL-C005 | Current model is scientifically qualified for forecast replacement or DA | REJECTED | Historical statistical errors; pilot audit | Moments/marginals degrade; boundary/lobe errors; no qualification gates passed |
| OL-C006 | Current learning representation is sufficiently accurate | OPEN | G05 | Conservative mass does not bound full-density export loss |
| OL-C007 | FNO is superior to strong structured alternatives | OPEN | G08 | Nearest-target diagnostic weakens claim; linear/POD/CNN not fairly tested |
| OL-C008 | More epochs will solve the statistical failure | CONJECTURE | Best pilot loss at final epoch | Longer fitting may worsen scientific metrics; ablation needed |
| OL-C009 | Current proxies transfer to full posterior forecast inputs | OPEN | G16 | Requires accepted population and actual posterior tests |
| OL-C010 | Separate CPU checkpoint evaluation reproduces principal pilot errors | EMPIRICAL | evidence/PILOT_20261004T133438Z.json; clean audit source 7cb41a6 | Same implementation, no independent reviewer; small device differences retained |

A new decision updates evidence/classification explicitly; original historical
results remain unchanged. No entry implies any G00–G17 pass.

| ID | Claim | Class | Evidence | Falsification / limitation |
|---|---|---|---|---|
| OL-C011 | The current six occupation inputs do not closely reproduce the declared G00 conditioned examples | NUMERICAL | evidence/G00_ALIGNMENT_V2_20261005.json; nearest L1 .771–1.949 | Restricted generators/maps/scales, not universal application coverage |
| OL-C012 | Sampling sensitivity may contribute materially to apparent occupation-law diversity | HEURISTIC | G00 block L1 .493–.921 versus original between-law .215–1.141 | Two replicates/one block length cannot identify law variation; G02/G03 required |
| OL-C013 | The mixed population proposal is sufficient for all eventual posterior inputs | OPEN | G00 proposal pending owner review; G16 later | Sequential, observation-strength and parameter coverage untested |
