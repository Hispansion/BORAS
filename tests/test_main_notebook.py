from pathlib import Path

import nbformat
from nbclient import NotebookClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIN_NOTEBOOK = PROJECT_ROOT / "notebooks" / "TSP_SPP_v2.ipynb"


def test_main_notebook_runs_with_default_config():
    notebook = nbformat.read(MAIN_NOTEBOOK, as_version=4)
    executed = NotebookClient(
        notebook,
        timeout=120,
        kernel_name="python3",
        resources={"metadata": {"path": str(PROJECT_ROOT)}},
    ).execute()

    output_text = "".join(
        "".join(output.get("text", ""))
        for cell in executed.cells
        for output in cell.get("outputs", [])
        if output.get("output_type") == "stream"
    )
    assert "Best path found:" in output_text
