# Solver monograph

Editable, multi-file LaTeX source for **Conserving Probability in a Chaotic
State Space**. The evidence snapshot is solver commit `1781b40`, with completed
local run artifacts through 3 October 2026. The document was prepared across
3-4 October 2026. It does not change the solver mathematics or authorize a
production dataset.

## Contents and provenance

- `book.tex`: entry point, notation, contents and typography.
- `foundations.tex`: probability, Lorenz, SDE, forward PDE and analysis.
- `discretisation.tex`: FV/DG/SIPG/CN, Bernstein and local QP derivations.
- `development.tex`: baseline audits and successful/failed research history.
- `implementation.tex`: final specification, diagnostics and reproduction.
- `technical_appendices.tex`: algebra, proofs, gates, assumptions and exercises.
- `history_appendix.tex`: all 69 available commits before documentation.
- `ledger_appendix.tex`: human-readable source/run index.
- `source_ledger.json`: 215 tracked files plus compact evidence, hashes,
  selected decision fields and direct density-array checks. Large diagnostic
  histories are indexed, not duplicated; omissions are counted.
- `manifest.json`: delivered artifact hashes, scope and validation.

## Build

The source archive includes the figure PDFs, so rebuilding the book itself
does not require the large numerical arrays. From `docs/solver_monograph/`:

```bash
pdflatex -interaction=nonstopmode -halt-on-error \
  -jobname=lorenz_solver_monograph -output-directory=../../output/pdf book.tex
pdflatex -interaction=nonstopmode -halt-on-error \
  -jobname=lorenz_solver_monograph -output-directory=../../output/pdf book.tex
```

Run an additional pass if contents/page references change. Required packages
include standard LaTeX/AMS tools, Latin Modern, microtype, xurl, hyperref,
fancyhdr, listings and TikZ. TeX Live 2023/Debian compiled the delivered file.

Regenerating figures or the evidence snapshot requires original local run
arrays and NumPy/Matplotlib. Use the project environment:

```bash
./scripts/run-in-env python scripts/build_solver_monograph_evidence.py
./scripts/run-in-env python scripts/verify_solver_monograph.py
```

Regeneration intentionally creates a new ledger snapshot. To adjust appendix
layout without changing the archived hashes, use `--render-index-only`.
The PDF QA script renders every page, checks unresolved references and text
bounds, and creates contact sheets; its output still requires visual review.

Generated outputs reside under ignored `output/pdf/`. Local scratch renderings
are under ignored `tmp/pdfs/`. Neither source bundle nor PDF contains the large
solver/MC arrays. The monograph records precisely why those external inputs
remain necessary for full numerical reproduction.
