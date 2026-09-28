# BORAS

BORAS stands for Basic Operation Rover Analysis Software.

This repository contains the main `BORAS_v1.py` library together with the `notebooks/TSP_SPP_v2.ipynb` workflow used to run the core rover path-planning experiments. Legacy scripts, utility generators, and supporting notebooks are organized into dedicated folders so the active code path stays easy to find.

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

## Quick Start

1. Create and activate a virtual environment.
2. Install the project in editable mode with dev dependencies:

```bash
pip install -e .[dev]
```

3. Run the test suite:

```bash
pytest
```

## Availability

Hispansion publishes this repository publicly. Public access does not expand
the software license beyond ESA Member States or grant rights to the bundled
input datasets.

## Notes

- Selected DEM and CBOR fixtures are tracked so clone-based tests and examples can run.
- Other large maps, CBOR inputs, pickles, and generated outputs remain ignored by Git.
- The tracked input datasets are not covered by the software license; see [NOTICE](NOTICE).
