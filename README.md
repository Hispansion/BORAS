# BORAS

BORAS stands for Basic Operation Rover Analysis Software.

This repository contains the main `BORAS_v1.py` library together with the `notebooks/TSP_SPP_v2.ipynb` workflow used to run the core rover path-planning experiments. Legacy scripts, utility generators, and supporting notebooks are organized into dedicated folders so the active code path stays easy to find.

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

## Repository Visibility

Keep the remote repository private for now. When you create it on GitHub, GitLab, or another host, set the visibility to `private` before the first push.

## Notes

- Large map files, CBOR illumination files, pickles, and generated outputs are intentionally ignored by Git.
- DEM and CBOR inputs are organized under `data/` for easier local access while remaining untracked in Git.

## First Push Checklist

1. Create the remote repository as `private`.
2. Install dependencies locally with `pip install -e .[dev]`.
3. Run `pytest`.
4. Review `git status` to confirm no large generated files are staged.
5. Push `main` and verify the CI workflow passes.
