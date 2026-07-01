import numpy as np
#import richdem as rd
import rasterio as rio
from rasterio.plot import show
import matplotlib.pyplot as plt
from time import perf_counter
import elevation 
import random
import copy
import datetime
import BORAS

t1_start = perf_counter() 

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

def evaluate_move(move,position, old_position, start,end,grid_size, fitness, old_fitness,path,old_move,slope_dem):
    position = move_position(grid_size,position,move,end)
    distance_to_end=abs(position[0]-end[0]) + abs(position[1]-end[1]) #Manhattan Distance
    max_dist = abs(start[0]-end[0]) + abs(start[1]-end[1]) #Manhattan Distance
    norm_dist = (max_dist - distance_to_end)/max_dist #Normalise
    slope_point = slope_dem[position[0]][position[1]]
    if slope_point > max_slope:
        norm_slope = 0.01
    else:
        norm_slope = (max_slope-slope_point)/max_slope
    fitness = (norm_dist*10+norm_slope)
    for old_position in path:
        if position == old_position:
            fitness = fitness/500
    if move[0] != old_move[0]:
            fitness = fitness/10
    if fitness <= 0:
        fitness = 0.0001

    return fitness


def new_move(moves, position, old_position,start, end, grid_size, old_fitness,path, move):
    fitness = []
    old_move = move
    for move in moves:
       total_distance = evaluate_move(move,position, old_position, start, end, grid_size, fitness, old_fitness,path, old_move,slope_dem) 
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

def calc_slope(path,slope_dem):
    slope = 0
    flag_max_slope =0
    for i in range((len(path)-1)):
        position = path[i]
        slope_point = slope_dem[position[0]][position[1]]
        slope = slope + slope_point
        if slope_point > max_slope:
            flag_max_slope = 1
    return [slope,flag_max_slope]

def select_pop(pop, fitness, num_to_select):
    selected =[]
    for i in range(num_to_select):
        max_fitness = max(fitness)
        idx_max = fitness.index(max_fitness)
        fitness.pop(idx_max)
        selected.append(pop[idx_max])
        pop.pop(idx_max)
    return selected

def crossover(parent1,parent2,crossover_rate=0.85):
    if random.random()< crossover_rate:

        common_point1 =[]
        common_point2 =[]
        for x in parent1:
            for y in parent2:
                if x == y:
                    common_point1 = tuple(x)
                    common_point2 = tuple(y)
        if  not common_point1 or common_point2:
            return parent1
        else:
            crossover_points= random.randint(0,len(common_point1)-1)
            child = parent1[:parent1.index(common_point1[crossover_points])] + parent2[parent2.index(common_point2[crossover_points]):]
            return child
    else:
        return parent1


def mutation(path, end,mutation_rate=0.4):
    if random.random()< mutation_rate:
            mutation_point= random.randint(1,len(path[0])-1)
            start = tuple(path[mutation_point-2])
            path[:mutation_point].append(create_path(moves,start, end, grid_size))
    return path

def  termination_condition(generations, max_generations):
    return generations>= max_generations

def normalize_pop(pop):
    tot_distance = []
    tot_slope = []
    flag_ms =[]
    min_dist = abs(start[0]-end[0]) + abs(start[1]-end[1])
    max_tot_distance = grid_size[0]* grid_size[1]
    max_tot_slope =max_tot_distance * 90
    for i in range(len(pop)):
        tot_distance1 = calc_dist(pop[i])
        tot_slope1,flag= calc_slope(pop[i],dem)
        flag_ms.append(flag)
        tot_distance.append(tot_distance1)
        tot_slope.append(tot_slope1)    
    tot_distance = np.array(tot_distance)
    tot_slope = np.array(tot_slope)
    norm_dist =np.array((1-(tot_distance-min_dist)/tot_distance))
    norm_slope = np.array((max_tot_slope-tot_slope)/max_tot_slope)
    norm_fitness =np.add(norm_slope,norm_dist)/2
    norm_fitness = norm_fitness.tolist()    
    for i in range(len(pop)):
        if flag_ms[i] ==1:
            norm_fitness[i] = norm_fitness[i]/10
    return [norm_fitness,tot_slope,tot_distance]

def normalize_path(path):
    tot_distance = []
    tot_slope = []
    min_dist = abs(start[0]-end[0]) + abs(start[1]-end[1])
    max_tot_distance = grid_size[0]* grid_size[1]
    max_tot_slope =max_tot_distance * 90
    tot_distance = calc_dist(path)
    tot_slope,flag= calc_slope(path,dem)
    norm_dist =(1-(tot_distance-min_dist)/tot_distance)
    norm_slope = (max_tot_slope-tot_slope)/max_tot_slope
    norm_fitness =(norm_slope+norm_dist)/2    
    if flag == 1:
        norm_fitness = norm_fitness/10
    return norm_fitness

def evaluate_heuristic_move(move,position, start,end,grid_size):
    position = move_position(grid_size,position,move,end)
    distance_to_end=abs(position[0]-end[0]) + abs(position[1]-end[1]) #Manhattan Distance
    max_dist = abs(start[0]-end[0]) + abs(start[1]-end[1]) #Manhattan Distance
    norm_dist = (max_dist - distance_to_end)/max_dist #Normalise
    return norm_dist


def new_heuristic_move(moves, position,start, end, grid_size, move):
    fitness = []
    old_move = move
    for move in moves:
        move_fitness = evaluate_heuristic_move(move,position, start, end, grid_size) 
        fitness.append(move_fitness)
    max_fitness = max(fitness)
    idx_max = fitness.index(max_fitness)
    move = moves[idx_max]
    move = str(move).strip('[]')
    move = str(move).replace("'","")
    return move

def create_heuristic_path(moves,start, end, grid_size):
    path = []
    position = start
    old_fitness = 0
    path.append(position)
    move = 'R'
    while position != end:
        old_position = position
        move= new_heuristic_move(moves,position,old_position, start, end, grid_size, old_fitness)
        position = tuple(move_position(grid_size,position,move,end))
        path.append(position)
    return path

def deloop (path,grid_size):
    n = random.randint(10,20)
    delooped_path = []
    section = []
    for i in range(0, len(path[0]), n):
        if i+n >(len(path[0])-1):
            n = (len(path[0])) -i
        section = path[0][i:i+n]
        start = section[0]
        end = section[-1]
        min_dist = abs(start[0]-end[0]) + abs(start[1]-end[1])
        s_dist = calc_dist(section)
        if  min_dist == 0:
            delooped_path.extend(section)
        else:
            if (s_dist/min_dist)>1.15:
                section = create_heuristic_path(moves,start, end, grid_size)
                delooped_path.extend(section) 
            else:
                delooped_path.extend(section)
    return delooped_path

#def calc_traverse_time(path):
    slope_dem =dem.read(1)
    time = 0
    for position in path:
        speed = 0.025 - (0.001*slope_dem[position[0]][position[1]])
        time_s = int(1/speed)
        time = time + time_s
    time_total = str(datetime.timedelta(seconds=time))
    return time_total
#DEM 

filename = "lunargem_4to5_slope.tif"
dem = rio.open(filename)
print(filename)
slope_dem =dem.read(1)

# SET GRID SIZE
grid_size=(dem.shape[0],dem.shape[1])
start=(280,280) #SELECT STARTING POINT
end=(80,120) #SELECT ENDING POINT
moves=['U', 'D', 'L', 'R' ] #POSSIBLE MOVEMENTS: UP, DOWN, LEFT & RIGHT
#moves=['U', 'D', 'L', 'R',c]

#SYSTEM CONSTRAINTS
max_slope = 15

# INITIALIZE POPULATION(DIFFERENT RANDOM PATHS)
pop_size= 8 #Always multiples of 8!
print("Population size =", pop_size)
pop = []
max_generations=1
deloop_flag = True

def create_path(moves,start, end, grid_size):
    path = []
    position = start
    old_fitness = 0
    path.append(position)
    move = 'R'
    while position != end:
        old_position = position
        move, old_fitness = new_move(moves,position, old_position, start, end, grid_size, old_fitness, path, move)
        position = tuple(move_position(grid_size,position,move,end))
        path.append(position)
    return path


for i in range(pop_size):
    te_start = perf_counter() 
    populant = create_path(moves,start, end, grid_size)
    print(len(populant))
    pop.append(populant)
    te_stop = perf_counter()
    print("Elapsed time to create a single path in seconds:", (te_stop-te_start))  

#EVALUATE POPULATION
norm_fitness = []
norm_fitness,tot_slope,tot_distance = normalize_pop(pop) 

for i in range(pop_size):
    if deloop_flag == True:
        delooped_path = deloop(pop,grid_size)
        delooped_fitness = normalize_path(delooped_path)
        if norm_fitness[i] <= delooped_fitness:
            pop[i] = delooped_path
            norm_fitness[i] = delooped_fitness

#GENERATION INFO
best_fitness = max(norm_fitness)
best_path_idx = norm_fitness.index(best_fitness)
print(f'Generation 0: Best fitness = {best_fitness}.')

    
def evolutionary_algorithm(grid_size,start,end,moves, pop, max_generations,norm_fitness):
    generations = 0
    while not termination_condition(generations,max_generations):

        generations += 1

        #SELECT POPULATION FOR NEXT GEN
        selected_pop_size = int(pop_size/4)
        select_fitness = copy.deepcopy(norm_fitness)
        pop_w_elite = copy.deepcopy(pop)
        elite_pop = select_pop(pop,select_fitness,selected_pop_size)
        select_fitness = copy.deepcopy(norm_fitness)
        selected_pop = select_pop(pop_w_elite,select_fitness,selected_pop_size*2)
        random.shuffle(selected_pop)
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

        #DELOOP
        for i in range(pop_size):
            if deloop_flag == True:
                delooped_path = deloop(pop,grid_size)
                delooped_fitness = normalize_path(delooped_path)
                if norm_fitness[i] <= delooped_fitness:
                    pop[i] = delooped_path
                    norm_fitness[i] = delooped_fitness

        #EVALUATE POPULATION
        norm_fitness = []
        norm_fitness,tot_slope,tot_distance = normalize_pop(pop)
        if norm_fitness == [0]*len(norm_fitness):
            print('Norm_fitness is full of zeros')
            break 



        #GENERATION INFO
        best_fitness = max(norm_fitness)
        best_path_idx = norm_fitness.index(best_fitness)
        print(f'Generation {generations}: Best fitness = {best_fitness}.')
 
    best_path = pop[best_path_idx]
    best_t_dist = tot_distance[best_path_idx]
    best_t_slp =  tot_slope[best_path_idx]
    print('Total distance:',best_t_dist)
    print('Total slope:',best_t_slp)
    return best_path

# RUN EVOLUTIONARY ALGORITHM

best_path = evolutionary_algorithm(grid_size, start, end, moves, pop, max_generations,norm_fitness)
t1_stop = perf_counter()

print('Best path found:',best_path)
print("Elapsed time during the whole program in minutes:", (t1_stop-t1_start)/60)
#traverse_time = calc_traverse_time(best_path)
traverse_time = BORAS.calc_traverse_time(best_path,dem)
print ('Total traverse time:',traverse_time)


dem_array = dem.read(1).astype('float64')
fig, ax = plt.subplots(figsize=(5, 5))
plt.plot(*zip(*best_path))
plt.imshow(dem_array, origin='lower', cmap='Greys_r',interpolation='none')
plt.colorbar()
plt.contour(dem_array, origin='lower', linewidths=0.7)
plt.axis = ((0,grid_size[0],0,grid_size[1]),'equal')
plt.xticks(np.arange(0,grid_size[0],(grid_size[0]/10)))
plt.yticks(np.arange(0,grid_size[1],(grid_size[1]/10)))
plt.grid(False)
plt.show()