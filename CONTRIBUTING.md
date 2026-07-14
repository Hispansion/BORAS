# Contributing to BORAS

## Development Workflow

1. Create a virtual environment for the project.
2. Install the package and development dependencies:

```bash
pip install -e .[dev]
```

3. Run the test suite before opening a pull request:

```bash
pytest
```

## Repository Conventions

- Keep `BORAS_v1.py` as the main library entry point until the codebase is intentionally refactored into a package structure.
- Keep experiment notebooks in `notebooks/`.
- Keep configuration files in `configs/`.
- Keep legacy/reference scripts in `scripts/legacy/`.
- Keep one-off utilities and generators in `scripts/tools/`.
- Do not commit large generated `.tif`, `.cbor`, or `.pickle` outputs unless there is a deliberate decision to version them.

## Pull Requests

- Open pull requests against `main`.
- Prefer small, focused changes.
- Include a short note describing the scenario tested and whether results depend on local datasets that are not tracked in Git.

## Visibility

The remote repository should remain private until  explicitly decide to publish or share it more broadly.

