import numpy as np
import heapq
import rasterio as rio
import matplotlib.pyplot as plt
import time
import datetime


def read_slope_map(file_path):
    try:
        with rio.open(file_path) as src:
            slope_map = src.read(1)  # Read first band (assuming slope map is single band)
            slope_map = np.flipud(slope_map)  # Flip array vertically to align with imshow 'lower' origin
            slope_map[slope_map == -9999] = np.nan  # Handle NoData values if present
        print(f"Slope map shape: {slope_map.shape}")
        return slope_map
    except Exception as e:
        print(f"Error reading slope map file: {e}")
        return None


def calculate_slope_traversed(slope_map, path):
    total_slope = 0
    for point in path:
        total_slope += slope_map[point]
    return total_slope


def calc_traverse_time(path, slope_map):
    slope_dem = slope_map
    time = 0
    for position in path:
        speed = 0.025 - (0.001 * slope_dem[position[0]][position[1]])
        time_s = int(1 / speed)
        time = time + time_s
    time_total = str(datetime.timedelta(seconds=time))
    return time_total


def calculate_cost(slope_map, current, neighbor, max_slope):
    slope = slope_map[neighbor]
    distance = np.sqrt((neighbor[0] - current[0]) ** 2 + (neighbor[1] - current[1]) ** 2)
    time_to_traverse = int(1 / (0.025 - 0.001 * slope_map[neighbor]))
    if slope > max_slope:
        # Apply penalty for exceeding max_slope
        cost = distance * (1 + (slope - max_slope))
    else:
        cost = time_to_traverse
    return cost


def dijkstra(slope_map, start, end, max_slope):
    if slope_map is None:
        print("Slope map data is not available.")
        return [], 0, 0, 0, "00:00:00"

    rows, cols = slope_map.shape
    start_index = start
    end_index = end

    distances = {start_index: 0}
    total_distance = 0
    total_slope = 0
    priority_queue = [(0, start_index)]
    previous_nodes = {start_index: None}

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    start_time = time.time()

    while priority_queue:
        current_time, current_node = heapq.heappop(priority_queue)

        if current_node == end_index:
            total_time = distances[current_node]  # Final total time to end_index
            break

        for direction in directions:
            neighbor = (current_node[0] + direction[0], current_node[1] + direction[1])
            if 0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols:
                time_to_traverse = int(1 / (0.025 - 0.001 * slope_map[neighbor]))
                new_time = current_time + time_to_traverse
                
                cost = calculate_cost(slope_map, current_node, neighbor, max_slope)
                
                if neighbor not in distances or new_time < distances[neighbor]:
                    distances[neighbor] = new_time
                    previous_nodes[neighbor] = current_node
                    heapq.heappush(priority_queue, (new_time, neighbor))

    if end_index not in previous_nodes:
        print("No path found.")
        return [], 0, 0, "00:00:00"

    path = []
    current_node = end_index
    while current_node:
        path.append(current_node)
        current_node = previous_nodes[current_node]

    path.reverse()

    total_slope_traversed = calculate_slope_traversed(slope_map, path)
    algorithm_time = time.time() - start_time

    # Calculate traverse time using slope_map
    traverse_time = calc_traverse_time(path, slope_map)

    return path, total_slope_traversed, algorithm_time, traverse_time


def main():
    slope_map_file_path = 'lunargem_4to5_slope.tif'
    start_index = (120, 290)  # Replace with your start index (row, col)
    end_index = (300, 100)  # Replace with your end index (row, col)
    max_slope = 15  # Maximum allowable slope (degrees)

    print(f"Reading slope map file from: {slope_map_file_path}")
    slope_map = read_slope_map(slope_map_file_path)

    if slope_map is None:
        print("Failed to read slope map file. Exiting.")
        return

    print("Slope map file successfully read.")

    path, total_slope, algorithm_time, traverse_time = dijkstra(slope_map, start_index, end_index, max_slope)

    if not path:
        print("No path found or slope map data is not available.")
        return

    print("Shortest path:")
    print(path)
    print(f"Total slope traversed: {total_slope}")
    print(f"Algorithm time: {algorithm_time} seconds")
    print(f"Estimated traverse time: {traverse_time}")

    # Plotting
    fig, ax = plt.subplots(1, figsize=(5, 5))

    # Plot slope map
    ax.imshow(slope_map, origin='lower', cmap='Greys_r', interpolation='none')

    # Extract x, y coordinates for path plotting
    path_x = [point[1] for point in path]  # Col indices
    path_y = [point[0] for point in path]  # Row indices

    # Plot path
    ax.plot(path_x, path_y, marker='o', color='red', markersize=5, linewidth=2)

    ax.set_title('Shortest Path Overlay on Slope Map')
    ax.set_xlabel('Column Index')
    ax.set_ylabel('Row Index')
    ax.grid(False)
    plt.colorbar(ax.imshow(slope_map, origin='lower', cmap='Greys_r', interpolation='none'), ax=ax)

    plt.show()


if __name__ == "__main__":
    main()
