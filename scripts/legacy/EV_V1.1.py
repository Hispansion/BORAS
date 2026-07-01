import numpy as np
#import richdem as rd
import rasterio as rio
from rasterio.plot import show
import matplotlib.pyplot as plt
import elevation 
import random
import copy

def move_position(grid_size,position,move,end):
    x, y = position
    if move[0] == 'U' and y > 0:
        new_position = (x,y-1)
    elif move[0] == 'D' and y < grid_size[1]-1:
        new_position = (x,y+1)
    elif move[0] == 'L' and x > 0:
        new_position = (x-1,y)
    elif move[0] == 'R' and x < grid_size[0]-1:
        new_position = (x+1,y)
    #elif move[0] == "UL" and y > 0 and x > 0:
        #new_position = (x - 1, y - 1)
    #elif move[0] == "DL" and y < grid_size[1] - 1 and x > 0:
        #new_position = (x - 1, y + 1)
    #elif move[0] == "UR" and x < grid_size[0] - 1 and y > 0:
        #new_position = (x + 1, y - 1)
    #elif move[0] == "DR" and x < grid_size[0] - 1 and y < grid_size[1] - 1:
        #new_position = (x + 1, y + 1)
    elif x == end[0] and y == end[1]:
        new_position = position
    else:
        new_position = position
    return new_position

def evaluate_move(move,position, old_position, start,end,grid_size, fitness, old_fitness,path,dem):
    position = move_position(grid_size,position,move,end)
    distance_to_end=abs(position[0]-end[0]) + abs(position[1]-end[1]) #Manhattan Distance
    max_dist = abs(start[0]-end[0]) + abs(start[1]-end[1]) #Manhattan Distance
    norm_dist = (max_dist - distance_to_end)/max_dist #Normalise Distance
    slope_dem =dem.read(2)
    slope_point = slope_dem[position[0]][position[1]]
    if slope_point > max_slope:
        norm_slope = 0.1
    else:
        norm_slope = (max_slope-slope_point)/max_slope
    fitness = (norm_dist+norm_slope)/2
    if fitness < old_fitness:
        fitness = fitness/30
    for old_position in path:
        if position == old_position:
            fitness = fitness/20
    return fitness


def new_move(moves, position, old_position,start, end, grid_size, old_fitness,path):
    fitness = []
    for move in moves:
       total_distance = evaluate_move(move,position, old_position, start, end, grid_size, fitness, old_fitness,path,dem) 
       fitness.append(total_distance)
    move = random.choices(moves, weights=fitness)
    move = str(move).strip('[]')
    move = str(move).replace("'","")
    fitness= fitness[moves.index(move)]
    return[move,fitness]

def calc_dist(path):
    tot_distance=0
    for i in range((len(path)-1)):
        step1 = path[i]
        step2 = path[i+1]
        step_dist = abs(step1[0]-step2[0]) + abs(step1[1]-step2[1])
        tot_distance = tot_distance + step_dist
    return tot_distance

def calc_slope(path,dem):
    slope = 0
    flag_max_slope =0
    slope_dem =dem.read(2)
    for i in range((len(path)-1)):
        position = path[i]
        slope_point = slope_dem[position[0]][position[1]]
        slope = slope + slope_point
        if slope_point > max_slope:
            flag_max_slope = 1
    return [slope,flag_max_slope]

# def evaluate_path(path,position,end):
#   for path in pop:
#  print(len(path{\}))
# return distance_to_end

def select_pop(pop, fitness, num_to_select):
    selected =[]
    for i in range(num_to_select):
        max_fitness = max(fitness)
        idx_max = fitness.index(max_fitness)
        fitness.pop(idx_max)
        selected.append(pop[idx_max])
        pop.pop(idx_max)
    return selected

def crossover(parent1,parent2,crossover_rate=0.9):
    if random.random()< crossover_rate:

        common_point1 =[]
        common_point2 =[]
        for x in parent1[0]:
            for y in parent2[0]:
                if x == y:
                    common_point1 = tuple(x)
                    common_point2 = tuple(y)
        if  not common_point1 or common_point2:
            return parent1
        else:
            crossover_points= random.randint(0,len(common_point1))
            child = parent1[:parent1.index(common_point1[crossover_points])] + parent2[parent2.index(common_point2[crossover_points]):]
            return child
    else:
        return parent1

def mutation(path, end,mutation_rate=0.4):
    if random.random()< mutation_rate:
            mutation_point= random.randint(2,len(path[0]))
            start = tuple(path[0][mutation_point-2])
            path[0][:mutation_point].append(create_path(moves,start, end, grid_size))
    return path

def  termination_condition(generations, max_generations):
    return generations>= max_generations

def normalize(pop):
    tot_distance = []
    tot_slope = []
    flag_ms =[]
    max_tot_distance = grid_size[0]* grid_size[1]
    max_tot_slope =max_tot_distance * 90
    for i in range(len(pop)):
        tot_distance1 = calc_dist(pop[i][0])
        tot_slope1,flag= calc_slope(pop[i][0],dem)
        flag_ms.append(flag)
        tot_distance.append(tot_distance1)
        tot_slope.append(tot_slope1)    
    tot_distance = np.array(tot_distance)
    tot_slope = np.array(tot_slope)
    norm_dist =np.array((max_tot_distance-tot_distance)/max_tot_distance)
    norm_slope = np.array((max_tot_slope-tot_slope)/max_tot_slope)
    norm_fitness =np.add(norm_slope,norm_dist)/2
    norm_fitness = norm_fitness.tolist()    
    for i in range(len(pop)):
        if flag_ms[i] ==1:
            norm_fitness[i] = norm_fitness[i]/10
    return [norm_fitness,tot_slope,tot_distance]


#DEM 

filename = "DEM-1.tif"
dem = rio.open(filename)

# SET GRID SIZE
grid_size=(dem.shape[0],dem.shape[1])
start=(4,80) #SELECT STARTING POINT
end=(189,120) #SELECT ENDING POINT
moves=['U', 'D', 'L', 'R' ] #POSSIBLE MOVEMENTS: UP, DOWN, LEFT & RIGHT
#moves=['U', 'D', 'L', 'R',c]

#SYSTEM CONSTRAINTS
max_slope = 15

# INITIALIZE POPULATION(DIFFERENT RANDOM PATHS)
pop_size= 128
pop = []
max_generations=100

def create_path(moves,start, end, grid_size):
    path = []
    position = start
    old_fitness = 0
    path.append(position)
    while position != end:
        old_position = position
        move, old_fitness = new_move(moves,position, old_position, start, end, grid_size, old_fitness, path)
        position = tuple(move_position(grid_size,position,move,end))
        if position not in path:
            path.append(position)
    return[path]


for i in range(pop_size):
    populant = create_path(moves,start, end, grid_size)
    pop.append(populant)    



    
def evolutionary_algorithm(grid_size,start,end,moves, pop, max_generations):
    generations = 0
    while not termination_condition(generations,max_generations):
        #EVALUATE POPULATION
        norm_fitness = []
        norm_fitness,tot_slope,tot_distance = normalize(pop)
        if norm_fitness == [0]*len(norm_fitness):
            print('Norm_fitness is full of zeros')
            break 
        #GENERATION INFO
        best_fitness = max(norm_fitness)
        best_path_idx = norm_fitness.index(best_fitness)
        print(f'Generation {generations}: Best fitness = {best_fitness}.')
        generations += 1

        #SELECT POPULATION FOR NEXT GEN
        selected_pop_size = int(pop_size/4)
        select_fitness = copy.deepcopy(norm_fitness)
        elite_pop = select_pop(pop,select_fitness,selected_pop_size)
        selected_pop = select_pop(pop,select_fitness,selected_pop_size*2)
        #BUILD NEXT GEN
        next_gen = []
        #ELITE
        for i in range(selected_pop_size):
            next_gen.append(elite_pop[i])

        #GENERAL    
        for i in range(0, (selected_pop_size*2),2):

            #CROSSOVER
            parent1 =[]
            parent2=[]
            child1=[]
            child2=[]
            parent1 , parent2 = selected_pop[i],selected_pop[i+1]
            child1,child2 = crossover(parent1,parent2), crossover(parent2,parent1)

            #MUTATION
            child1,child2 = mutation(child1,end),mutation(child2,end)
            next_gen.append(child1)
            next_gen.append(child2)

        #IMIGRANT POPULATION
        for i in range(selected_pop_size):
            imigrant = create_path(moves,start, end, grid_size)
            next_gen.append(imigrant)
        
        if len(next_gen) != pop_size:
            print("Next GEN Size different than Pop Size")
            break  
        
        pop[:] = next_gen
        
    print(tot_slope)
    best_path = pop[best_path_idx]
    best_t_dist = tot_distance[best_path_idx]
    best_t_slp =  tot_slope[best_path_idx]
    print('Total distance:',best_t_dist)
    print('Total slope:',best_t_slp)
    return best_path

# RUN EVOLUTIONARY ALGORITHM

best_path = evolutionary_algorithm(grid_size, start, end, moves, pop, max_generations)
print('Best path found:',best_path)
best_fitness = sum(map(len, best_path))
print(best_fitness)

dem_array = dem.read(1).astype('float64')
fig, ax = plt.subplots(1, figsize=(5, 5))
plt.plot(*zip(*best_path[0]))
plt.imshow(dem_array, origin='lower', cmap='Greys_r',interpolation='none')
plt.colorbar()
plt.contour(dem_array, origin='lower', linewidths=0.7)
plt.axis = ((0,grid_size[0],0,grid_size[1]),'equal')
plt.xticks(np.arange(0,grid_size[0],(grid_size[0]/10)))
plt.yticks(np.arange(0,grid_size[1],(grid_size[1]/10)))
plt.grid(False)
dem_array = dem.read(2).astype('float64')
fig, ax = plt.subplots(1, figsize=(5, 5))
plt.plot(*zip(*best_path[0]))
plt.imshow(dem_array, origin='lower', cmap='Greys_r',interpolation='none')
plt.colorbar()
plt.contour(dem_array, origin='lower', linewidths=0.7)
plt.axis = ((0,grid_size[0],0,grid_size[1]),'equal')
plt.xticks(np.arange(0,grid_size[0],(grid_size[0]/10)))
plt.yticks(np.arange(0,grid_size[1],(grid_size[1]/10)))
plt.grid(False)
plt.show()