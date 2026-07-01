import numpy as np
#import richdem as rd
import rasterio as rio
from rasterio.plot import show
import matplotlib.pyplot as plt
from time import perf_counter
import pandas as pd
import elevation 
import random
import pickle
import copy
import datetime
import BORAS_v1
save_path = 'results_fit_ev_64_c.pickle'
def ga():
    t1_start = perf_counter() 

    #DEM 
    
    filename = "lunargem_4to5_slope.tif"
    dem = rio.open(filename)
    print(filename)
    slope_dem =dem.read(1)

    # SET GRID SIZE
    grid_size=(dem.shape[0],dem.shape[1])
    start=(120,100) #SELECT STARTING POINT
    end=(350,100) #SELECT ENDING POINT
    #moves=['U', 'D', 'L', 'R' ] #POSSIBLE MOVEMENTS: UP, DOWN, LEFT & RIGHT
    moves=["U", "D", "L", "R","UL", "DL", "UR","DR"]

    #SYSTEM CONSTRAINTS
    max_slope = 15

    # INITIALIZE POPULATION(DIFFERENT RANDOM PATHS)
    pop_size= 64 #Always multiples of 8!
    print("Population size =", pop_size)
    pop = []
    max_generations= 200
    deloop_flag = True


    for i in range(pop_size):
        x=random.randint(1,4)
        populant = BORAS_v1.create_path(start,end,moves, grid_size, num_points=x)
        pop.append(populant)

    #EVALUATE POPULATION
    norm_fitness = []
    norm_fitness,x,y = BORAS_v1.normalize_pop(pop,start,end,grid_size,pop_size,max_slope,slope_dem)
    for i in range(pop_size):
        if deloop_flag == True:
            delooped_path = BORAS_v1.deloop(pop[i],grid_size,moves)
            delooped_fitness = BORAS_v1.normalize_path(delooped_path,start,end, grid_size, max_slope,slope_dem)
            if norm_fitness[i] <= delooped_fitness:
                pop[i] = delooped_path
                norm_fitness[i] = delooped_fitness

    #GENERATION INFO
    best_fitness = max(norm_fitness)
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

    return best_fitness,fitnesses_gen

fitnesses = []
gen_fit = []
runs = 25
for _ in range (runs):
    fitness, gen_fitness = ga()
    fitnesses.append(fitness)
    gen_fit.append(gen_fitness)

gen_fit = pd.DataFrame(gen_fit)
gen_fit_mean = list(gen_fit.mean())
with open(save_path, 'wb') as file:
    pickle.dump(gen_fit,file)
print("Average fitness:",gen_fit_mean)
ax3=plt.figure()
plt.plot(gen_fit_mean)
plt.show()