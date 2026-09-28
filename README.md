# BORAS

BORAS stands for Basic Operation Rover Analysis Software.

For a normal run, you only need three project files:

1. [BORAS_v1.py](BORAS_v1.py) is the function library. You do not need to edit it.
2. [TSP_SPP_v2.ipynb](notebooks/TSP_SPP_v2.ipynb) is the main workflow. Run its cells from top to bottom.
3. [input_config.txt](configs/input_config.txt) is the input you edit to choose the map, waypoints, and mode.

The other notebooks, configs, and tools are kept as research examples. The `data/` folder holds the DEM and illumination inputs referenced by the configs.

## Run BORAS

From the repository root, create a Python 3.11 environment. On Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Then install and launch the notebook:

```bash
python -m pip install -e ".[notebook]"
python -m jupyterlab notebooks/TSP_SPP_v2.ipynb
```

Edit `configs/input_config.txt`, choose the environment's Python kernel in JupyterLab, and select **Run > Run All Cells**. The notebook reads `configs/input_config.txt` by default; to use another config, change only `CONFIG_FILE` in its first code cell. Config paths for `filename` and `illumination_filename` are relative to the repository root. The included default config uses tracked test data, so no external maps are needed for a first run.

In the config, `mode='Tour'` runs TSP and `mode='Single'` runs one path. For tours, `tsp_mode='OL'` is open and `tsp_mode='CL'` returns to the start. Waypoints use `(row, column)` coordinates. The default static Dijkstra tour runs quickly; time-dependent `TDD` runs need a CBOR illumination file and start-time range and can take much longer.

## License

Copyright (c) Carlos Aguilar Borasteros. The BORAS software is published by
Hispansion with the copyright holder's permission under the ESA Software
Community License - Type 3 - v1.1. Read [LICENSE](LICENSE) and the complete
license text in [LICENSE.pdf](LICENSE.pdf). This license grants rights within
ESA Member States, not throughout all of Europe, and does not imply ESA
ownership or endorsement. The input datasets under `data/` are not licensed
for reuse; see [NOTICE](NOTICE).

For commercial use or licensing questions, contact
[info@hispansion.io](mailto:info@hispansion.io).

## Project Layout

- `BORAS_v1.py`: main library used by the current workflow.
- `notebooks/`: experiment and validation notebooks, including `TSP_SPP_v2.ipynb`.
- `configs/`: input configuration files for selecting maps and runtime parameters.
- `data/`: DEM, illumination, and other local input assets used by the workflows.
- `scripts/legacy/`: older algorithm versions retained for reference.
- `scripts/tools/`: helper scripts for generating test cases and preprocessing data.
- `tests/`: initial automated checks for the core library.
- `.github/workflows/ci.yml`: continuous integration pipeline for pushes and pull requests.

## Tests

Install the development dependencies and run the automated checks:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

## Availability

Hispansion publishes this repository publicly. Public access does not expand
the software license beyond ESA Member States or grant rights to the bundled
input datasets.

## Notes

- Selected DEM and CBOR fixtures are tracked so clone-based tests and examples can run.
- Other large maps, CBOR inputs, pickles, and generated outputs remain ignored by Git.
- The tracked input datasets are not covered by the software license; see [NOTICE](NOTICE).
