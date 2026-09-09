#!/usr/bin/env python3
"""MC timestep sensitivity from the same repaired native initial law."""

from pathlib import Path

from lorenz_fpe.core import write_json
from lorenz_fpe.validation import common_initial_law_mc_timestep_sensitivity


write_json(Path("mc_timestep_same_initial_law.json"),
           common_initial_law_mc_timestep_sensitivity())
