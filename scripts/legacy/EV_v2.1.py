import numpy as np
#import richdem as rd
import rasterio as rio
from rasterio.plot import show
import matplotlib.pyplot as plt
from time import perf_counter
import pandas as pd
import elevation 
import random
import copy
import datetime
import BORAS_v1

t1_start = perf_counter() 

#DEM 

filename = "lunargem_4to5_slope.tif"
#filename = 'Wp2_3_slope.tif'
dem = rio.open(filename)
print(filename)
slope_dem =dem.read(1)

# SET GRID SIZE
grid_size=(dem.shape[0],dem.shape[1])
#og_start=(2655, 1078) #SELECT STARTING POINT
#og_end=(2666, 1366) #SELECT ENDING POINT
#start,end = BORAS_v1.new_start_end(og_start,og_end,slope_dem)
start = (120,84)
end = (266,284)
#moves=['U', 'D', 'L', 'R' ] #POSSIBLE MOVEMENTS: UP, DOWN, LEFT & RIGHT
moves=["U", "D", "L", "R","UL", "DL", "UR","DR"]

#SYSTEM CONSTRAINTS
max_slope = 15

# INITIALIZE POPULATION(DIFFERENT RANDOM PATHS)
pop_size= 128 #Always multiples of 8!
print("Population size =", pop_size)
pop = []
max_generations= 300
deloop_flag = True


for i in range(pop_size):
    x=random.randint(1,4)
    populant = BORAS_v1.create_path(start,end,moves, grid_size, slope_dem,num_points=x)
    pop.append(populant)

#EVALUATE POPULATION
norm_fitness = []
norm_fitness,tot_slope,tot_distance = BORAS_v1.normalize_pop(pop,start,end,grid_size,pop_size,max_slope,slope_dem)
for i in range(pop_size):
    if deloop_flag == True:
        delooped_path = BORAS_v1.deloop(pop[i],grid_size,moves)
        delooped_fitness = BORAS_v1.normalize_path(delooped_path,start,end, grid_size, max_slope,slope_dem)
        if norm_fitness[i] <= delooped_fitness:
            pop[i] = delooped_path
            norm_fitness[i] = delooped_fitness

#GENERATION INFO
best_fitness = max(norm_fitness)
best_path_idx = norm_fitness.index(best_fitness)
print(f'Generation 0: Best fitness = {best_fitness}.')

# RUN EVOLUTIONARY ALGORITHM

best_path,fitnesses_gen,gen_com = BORAS_v1.evolutionary_algorithm(grid_size,start,end,moves, pop, pop_size, max_generations, deloop_flag,norm_fitness,max_slope,slope_dem)
t1_stop = perf_counter()

print('Best path found:',best_path)
print("Elapsed time during the whole program in minutes:", (t1_stop-t1_start)/60)
#traverse_time = calc_traverse_time(best_path)
time_total = BORAS_v1.calc_traverse_time(best_path,slope_dem)
traverse_time = str(datetime.timedelta(seconds=time_total))
print ('Total traverse time:',traverse_time)

# Plotting
fig, ax = plt.subplots(1, figsize=(5, 5))

    # Plot slope map
ax.imshow(slope_dem, origin='upper', cmap='Greys_r', interpolation='none')

    # Extract x, y coordinates for path plotting
path_x = [point[1] for point in best_path]  # Col indices
path_y = [point[0] for point in best_path]  # Row indices

    # Plot path
ax.plot(path_x, path_y, marker='o', color='cyan', markersize=1, linewidth=0.5)

ax.set_title('Shortest Path Overlay on Slope Map')
ax.set_xlabel('Column Index')
ax.set_ylabel('Row Index')
ax.grid(False)
plt.colorbar(ax.imshow(slope_dem, origin='upper', cmap='Greys_r', interpolation='none'), ax=ax)

plt.show()