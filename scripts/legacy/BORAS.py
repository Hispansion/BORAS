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
    if move == "U" and y > 0:
        new_position = (x,y-1)
    elif move== "D" and y < grid_size[1]-1:
        new_position = (x,y+1)
    elif move == "L" and x > 0:
        new_position = (x-1,y)
    elif move == "R" and x < grid_size[0]-1:
        new_position = (x+1,y)
    elif move == "UL" and y > 0 and x > 0:
        new_position = (x - 1, y - 1)
    elif move == "DL" and y < grid_size[1] - 1 and x > 0:
        new_position = (x - 1, y + 1)
    elif move == "UR" and x < grid_size[0] - 1 and y > 0:
        new_position = (x + 1, y - 1)
    elif move == "DR" and x < grid_size[0] - 1 and y < grid_size[1] - 1:
        new_position = (x + 1, y + 1)
    elif x == end[0] and y == end[1]:
        new_position = position
    else:
        new_position = position
    return new_position

def evaluate_move(grid_size,move,start,end,position):
    position = move_position(grid_size,position,move,end)
    distance_to_end=np.sqrt((position[0]-end[0])**2 + (position[1]-end[1])**2) #Euclidean Distance
    max_dist = np.sqrt((start[0]-end[0])**2 + (start[1]-end[1])**2) #Euclidean Distance
    norm_dist = (max_dist - distance_to_end)/max_dist #Normalise
    return norm_dist


def new_move(moves,start, end, grid_size,position):
    fitness = []
    for move in moves:
       total_distance = evaluate_move(grid_size,move,start,end,position) 
       fitness.append(total_distance)
    max_fitness = np.max(fitness)
    move = moves[fitness.index(max_fitness)]
    move = str(move).strip('[]')
    move = str(move).replace("'","")
    fitness= fitness[moves.index(move)]
    return move

def create_segment(moves,start, end, grid_size):
    path = []
    position = start
    path.append(position)
    while position != end:
        move= new_move(moves, start, end, grid_size,position)
        position = tuple(move_position(grid_size,position,move,end))
        if position not in path:
            path.append(position)
    return path


def calc_dist(path):
    tot_distance=0
    for i in range((len(path)-1)):
        step1 = path[i]
        step2 = path[i+1]
        step_dist = np.sqrt((step1[0]-step2[0])**2 + (step1[1]-step2[1])**2)
        if step1[0] != step2[0] & step1[1]!=step2[1]:
            x=np.sqrt(2)
        else:
            x=1
        tot_distance = tot_distance + x*step_dist
    return tot_distance

def calc_slope(path,max_slope,slope_dem):
    slope = 0
    flag_max_slope = 0
    for i in range((len(path)-1)):
        position = path[i]
        slope_point = slope_dem[position[0]][position[1]]
        slope = slope + slope_point
        if slope_point >= max_slope:
            flag_max_slope = 1
    return [slope,flag_max_slope]

def select_pop_max(pop, fitness,pop_size, num_to_select):
    selected =[]
    for _ in range(pop_size):
        while len(selected) != num_to_select:
            max_fitness = max(fitness)
            idx_max = fitness.index(max_fitness)
            fitness.pop(idx_max)
            if pop[idx_max] not in selected:
                selected.append(pop[idx_max])
            pop.pop(idx_max)
        return selected

def select_pop_rand(pop, fitness,pop_size, num_to_select):
    selected =[]
    for i in range(num_to_select):
        x = random.randint(0,(pop_size-i-1))
        fitness.pop(x)
        selected.append(pop[x])
        pop.pop(x)
    return selected

def crossover(parent1,parent2, moves, grid_size, crossover_rate=1):
    if random.random()< crossover_rate:
        x = random.randint(0,1)
        crossover_point1= random.randint(0,(len(parent1)-1))
        crossover_point2= random.randint(0,(len(parent2)-1))
        child = parent1[:crossover_point1] + create_path(parent1[crossover_point1],parent2[crossover_point2],moves, grid_size, x) + parent2[crossover_point2:]
        return child
    else:
        return parent1


def mutation(path, end, moves, grid_size, mutation_rate=0.5):
    if random.random()< mutation_rate:
            x = random.randint(1,2)
            mutation_point= random.randint(2,len(path[0]))
            start = path[mutation_point-2]
            path[:mutation_point].append(create_path(start,end,moves, grid_size,num_points=x))
    return path

def  termination_condition(generations, max_generations):
    return generations>= max_generations

def normalize_pop(pop,start,end,grid_size,pop_size,max_slope,slope_dem):
    tot_distance = []
    tot_slope = []
    tot_time = []
    flag_ms =np.ones(pop_size)
    min_dist = np.sqrt((start[0]-end[0])**2 + (start[1]-end[1])**2)
    max_tot_distance = grid_size[0]* grid_size[1]
    max_tot_slope =max_tot_distance * 90
    for i in range(len(pop)):
        tot_distance1 = calc_dist(pop[i])
        tot_slope1,flag= calc_slope(pop[i],max_slope,slope_dem)
        tot_time1 = BORAS.calc_traverse_time(pop[i],slope_dem)
        flag_ms[i]=flag
        tot_distance.append(tot_distance1)
        tot_slope.append(tot_slope1)
        tot_time.append(tot_time1)
    tot_distance = np.array(tot_distance)
    tot_slope = np.array(tot_slope)
    tot_time = np.array(tot_time)
    norm_time = np.array((1-((tot_time-(min_dist/0.025))/tot_time)))
    norm_dist =np.array((1-(tot_distance-min_dist)/tot_distance))
    norm_slope = np.array((max_tot_slope-tot_slope)/max_tot_slope)
    #norm_fitness =np.add(norm_slope,norm_dist,3*norm_time)/5
    norm_fitness = norm_time
    norm_fitness = norm_fitness.tolist()    
    
    for i in range(pop_size):
        if flag_ms[i] == 1:
            norm_fitness[i] = norm_fitness[i]/2
    return [norm_fitness,tot_slope,tot_distance]

def normalize_path(path,start,end, grid_size, max_slope,slope_dem):
    tot_distance = []
    tot_slope = []
    flag=1
    min_dist = np.sqrt((start[0]-end[0])**2 + (start[1]-end[1])**2)
    max_tot_distance = grid_size[0]* grid_size[1]
    max_tot_slope =max_tot_distance * 90
    tot_distance = calc_dist(path)
    tot_slope,flag= calc_slope(path,max_slope,slope_dem)
    tot_time = BORAS.calc_traverse_time(path,slope_dem)
    norm_time = (1-((tot_time-(min_dist/0.025))/tot_time))
    norm_dist =(1-(tot_distance-min_dist)/tot_distance)
    norm_slope = (max_tot_slope-tot_slope)/max_tot_slope
    #norm_fitness =(norm_slope+norm_dist+3*norm_time)/5
    norm_fitness = norm_time
    if flag == 1:
        norm_fitness = norm_fitness/2
    return norm_fitness

def evaluate_heuristic_move(move,position, start,end,grid_size):
    position = move_position(grid_size,position,move,end)
    distance_to_end=np.sqrt((position[0]-end[0])**2 + (position[1]-end[1])**2) #Euclidean Distance
    max_dist = np.sqrt((start[0]-end[0])**2 + (start[1]-end[1])**2) #Euclidean Distance
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
        move= new_heuristic_move(moves, position,start, end, grid_size, move)
        position = tuple(move_position(grid_size,position,move,end))
        path.append(position)
    return path

def deloop (path,grid_size,moves):
    n = random.randint(10,20)
    delooped_path = []
    section = []
    for i in range(0, len(path), n):
        if i+n >(len(path)-1):
            n = (len(path)) -i
        section = path[i:i+n]
        start = section[0]
        end = section[-1]
        min_dist = np.sqrt((start[0]-end[0])**2 + (start[1]-end[1])**2)
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

def calc_traverse_time(path,slope_dem):
    time = 0 
    for i in range((len(path)-1)):
        step1 = path[i]
        step2 = path[i+1]
        if step1[0] != step2[0] & step1[1]!=step2[1]:
            x=np.sqrt(2)
        else:
            x=1
        position = path[i]
        speed = 0.025 - (0.001*slope_dem[position[0]][position[1]])
        if speed <= 0:
            speed = 0.0005
        time_s = int(x/speed)
        time = time + time_s
    #time_total = str(datetime.timedelta(seconds=time))
    return time

def create_path(start,end,moves, grid_size, num_points):
    int_points = []
    path = []
    int_points.append(start)
    for _ in range(num_points):
        i = random.randint(0,(grid_size[0]-1))
        j = random.randint(0,(grid_size[1]-1))
        position = (i,j)
        int_points.append(position)
    int_points.append(end)
    for x in range(len(int_points)-1):
        segment = create_segment(moves,int_points[x],int_points[x+1],grid_size)
        path.extend(segment)
    return path

def evolutionary_algorithm(grid_size,start,end,moves, pop, pop_size, max_generations, deloop_flag,norm_fitness,max_slope,slope_dem):
    generations = 0
    fitnesses_gen = []
    while not termination_condition(generations,max_generations):

        generations += 1

        #BUILD NEXT GEN
        next_gen = []  

        #SELECT POPULATION FOR NEXT GEN
        selected_pop_size = int(pop_size/8)
        select_fitness = copy.deepcopy(norm_fitness)
        pop_w_elite = copy.deepcopy(pop)
        elite_pop = select_pop_max(pop,select_fitness, pop_size, selected_pop_size*2)
        select_fitness = copy.deepcopy(norm_fitness)
        selected_pop = select_pop_rand(pop_w_elite,select_fitness, pop_size, selected_pop_size*2)
        selected_pop = selected_pop +  elite_pop
        

        #ELITE
        for i in range(selected_pop_size*2):
            next_gen.append(elite_pop[i])

        pop_indexes = list(np.arange(0,(selected_pop_size*4),1,dtype=int))

        #GENERAL    
        for i in range(0, (selected_pop_size*4),2):
            i,j = random.sample(pop_indexes,k=2)
            pop_indexes.remove(i)
            pop_indexes.remove(j)
            parent1 =[]
            parent2=[]
            child1=[]
            child2=[]
            parent1 , parent2 = selected_pop[i],selected_pop[j]
            child1,child2 = crossover(parent1,parent2, moves, grid_size), crossover(parent2,parent1, moves, grid_size)
            #MUTATION
            child1,child2 = mutation(child1,end, moves, grid_size),mutation(child2,end, moves, grid_size)
            next_gen.append(child1)
            next_gen.append(child2)

        #IMIGRANT POPULATION
        for i in range(selected_pop_size*2):
            x=random.randint(1,3)
            imigrant = create_path(start,end,moves, grid_size,num_points=x)
            next_gen.append(imigrant)
        if len(next_gen) != pop_size:
            print("Next GEN Size different than Pop Size")
            break  
        
        pop[:] = next_gen

        #EVALUATE POPULATION
        norm_fitness = []
        norm_fitness,tot_slope,tot_distance = normalize_pop(pop,start,end,grid_size,pop_size,max_slope,slope_dem)
        if norm_fitness == [0]*len(norm_fitness):
            print('Norm_fitness is full of zeros')
            break 

        #DELOOP
        for i in range(pop_size):
            if deloop_flag == True:
                delooped_path = deloop(pop[i],grid_size,moves)
                delooped_fitness = normalize_path(delooped_path,start,end, grid_size, max_slope,slope_dem)
                if norm_fitness[i] <= delooped_fitness:
                    pop[i] = delooped_path
                    norm_fitness[i] = delooped_fitness

        #EVALUATE POPULATION
        norm_fitness = []
        norm_fitness,tot_slope,tot_distance = normalize_pop(pop,start,end,grid_size,pop_size,max_slope,slope_dem)
        for i in range(pop_size):
            if norm_fitness == [0]*len(norm_fitness):
                print('Norm_fitness is full of zeros')
                break 

        #GENERATION INFO
        best_fitness = max(norm_fitness)
        fitnesses_gen.append(best_fitness)
        best_path_idx = norm_fitness.index(best_fitness)
        print(f'Generation {generations}: Best fitness = {best_fitness}.')
 
    best_path = pop[best_path_idx]
    best_t_dist = tot_distance[best_path_idx]
    best_t_slp =  tot_slope[best_path_idx]
    print('Total distance:',best_t_dist)
    print('Total slope:',best_t_slp)
    return best_path,fitnesses_gen
