from pathlib import Path

import itertools
import numpy as np

import BORAS_v1


def _always_lit_roots(shape):
    return {
        str(node_id): {"sunrises": [0.0], "sunsets": [10.0]}
        for node_id in range(shape[0] * shape[1])
    }


def _best_static_tsp_route(waypoints, slope_dem, tsp_mode):
    best_order = None
    best_cost = float("inf")
    best_segments = None

    for order in itertools.permutations(range(len(waypoints))):
        segment_pairs = (
            [(order[i], order[i + 1]) for i in range(len(order) - 1)]
            if tsp_mode == "OL"
            else [(order[i - 1], order[i]) for i in range(len(order))]
        )

        total_cost = 0.0
        segment_paths = []
        for start_idx, end_idx in segment_pairs:
            traverse_time, path = BORAS_v1.djikistras(
                waypoints[start_idx], waypoints[end_idx], slope_dem
            )
            total_cost += traverse_time
            segment_paths.append(path)

        if total_cost < best_cost:
            best_cost = total_cost
            best_order = order
            best_segments = segment_paths

    return best_order, best_cost, best_segments


def _best_tdd_tsp_route(waypoints, slope_dem, tsp_mode):
    roots = _always_lit_roots(slope_dem.shape)
    best_order = None
    best_cost = float("inf")
    best_segments = None
    best_departures = None

    for order in itertools.permutations(range(len(waypoints))):
        segment_pairs = (
            [(order[i], order[i + 1]) for i in range(len(order) - 1)]
            if tsp_mode == "OL"
            else [(order[i - 1], order[i]) for i in range(len(order))]
        )

        total_cost = 0.0
        start_times = BORAS_v1.generate_time_range(0.0, 0.1, 0.05)
        departures = []
        segment_paths = []

        for start_idx, end_idx in segment_pairs:
            departure_time, path, traverse_time, _ = BORAS_v1.TDD_expanded(
                waypoints[start_idx],
                waypoints[end_idx],
                slope_dem,
                roots,
                start_times,
            )
            departures.append(departure_time)
            segment_paths.append(path)
            total_cost += traverse_time
            next_start = departure_time + traverse_time
            start_times = BORAS_v1.generate_time_range(next_start, 0.1, 0.05)

        if total_cost < best_cost:
            best_cost = total_cost
            best_order = order
            best_segments = segment_paths
            best_departures = departures

    return best_order, best_cost, best_segments, best_departures


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


def test_static_spp_smoke_on_simplified_dem():
    # The thesis validates BORAS first on simplified maps before larger lunar cases.
    slope_dem = np.zeros((3, 3), dtype=float)

    traverse_time, path = BORAS_v1.djikistras((0, 0), (2, 2), slope_dem)

    assert traverse_time > 0
    assert path[0] == (0, 0)
    assert path[-1] == (2, 2)
    assert len(path) >= 2


def test_time_dependent_spp_smoke_with_always_lit_nodes():
    slope_dem = np.zeros((2, 2), dtype=float)
    roots = _always_lit_roots(slope_dem.shape)
    start_times = BORAS_v1.generate_time_range(0.0, 0.1, 0.05)

    departure_time, path, traverse_time, path_times = BORAS_v1.TDD_expanded(
        (0, 0), (1, 1), slope_dem, roots, start_times
    )

    assert departure_time in start_times
    assert traverse_time > 0
    assert path[0] == (0, 0)
    assert path[-1] == (1, 1)
    assert path_times


def test_tsp_open_static_smoke():
    slope_dem = np.zeros((3, 3), dtype=float)
    waypoints = [(0, 0), (0, 2), (2, 2)]

    best_order, best_cost, segment_paths = _best_static_tsp_route(
        waypoints, slope_dem, "OL"
    )

    assert sorted(best_order) == [0, 1, 2]
    assert best_cost > 0
    assert len(segment_paths) == len(waypoints) - 1
    assert segment_paths[0][0] == waypoints[best_order[0]]
    assert segment_paths[-1][-1] == waypoints[best_order[-1]]


def test_tsp_closed_static_smoke():
    slope_dem = np.zeros((3, 3), dtype=float)
    waypoints = [(0, 0), (0, 2), (2, 2)]

    best_order, best_cost, segment_paths = _best_static_tsp_route(
        waypoints, slope_dem, "CL"
    )

    assert sorted(best_order) == [0, 1, 2]
    assert best_cost > 0
    assert len(segment_paths) == len(waypoints)
    assert segment_paths[0][0] == waypoints[best_order[-1]]
    assert segment_paths[-1][-1] == waypoints[best_order[-1]]


def test_tsp_open_tdd_smoke():
    slope_dem = np.zeros((3, 3), dtype=float)
    waypoints = [(0, 0), (0, 2), (2, 2)]

    best_order, best_cost, segment_paths, departures = _best_tdd_tsp_route(
        waypoints, slope_dem, "OL"
    )

    assert sorted(best_order) == [0, 1, 2]
    assert best_cost > 0
    assert len(segment_paths) == len(waypoints) - 1
    assert len(departures) == len(waypoints) - 1
    assert segment_paths[0][0] == waypoints[best_order[0]]
    assert segment_paths[-1][-1] == waypoints[best_order[-1]]


def test_tsp_closed_tdd_smoke():
    slope_dem = np.zeros((3, 3), dtype=float)
    waypoints = [(0, 0), (0, 2), (2, 2)]

    best_order, best_cost, segment_paths, departures = _best_tdd_tsp_route(
        waypoints, slope_dem, "CL"
    )

    assert sorted(best_order) == [0, 1, 2]
    assert best_cost > 0
    assert len(segment_paths) == len(waypoints)
    assert len(departures) == len(waypoints)
    assert segment_paths[0][0] == waypoints[best_order[-1]]
    assert segment_paths[-1][-1] == waypoints[best_order[-1]]
