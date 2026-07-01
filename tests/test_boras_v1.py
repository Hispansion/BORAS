from pathlib import Path

import BORAS_v1


def test_generate_time_range_includes_endpoints():
    assert BORAS_v1.generate_time_range(1.0, 1.2, 0.1) == [1.0, 1.1, 1.2]


def test_parse_input_file_reads_literals_and_strings(tmp_path):
    config = tmp_path / "sample_config.txt"
    config.write_text(
        "mode='Single'\n"
        "pop_size=16\n"
        "time_dependent=False\n"
        "filename='plateau_slope.tif'\n",
        encoding="utf-8",
    )

    parsed = BORAS_v1.parse_input_file(config)

    assert parsed["mode"] == "Single"
    assert parsed["pop_size"] == 16
    assert parsed["time_dependent"] is False
    assert parsed["filename"] == "plateau_slope.tif"


def test_move_position_handles_diagonal_moves():
    moved = BORAS_v1.move_position((5, 5), (2, 2), "DR", (4, 4))
    assert moved == (3, 3)

