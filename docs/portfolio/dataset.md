# Generating and storing the data

The data pipeline turns a configured numerical experiment into files that can be used for analysis and training. The important part is keeping the input distribution, forecast and configuration together so that a result can be traced back to the calculation that produced it. This module belongs to the repository’s general dataset implementation; the historical MFEM neural pilot has its own launcher. Reading this file alone does not reproduce that pilot or establish that every generated target is accurate.

[Implementation or detailed research record](../../lorenz_fpe/dataset.py).
