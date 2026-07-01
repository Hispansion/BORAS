import numpy as np
#import richdem as rd
import rasterio as rio
from rasterio.plot import show
import matplotlib.pyplot as plt
from time import perf_counter
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

def evaluate_heursitic_move(move,position, start,end,grid_size):
    position = move_position(grid_size,position,move,end)
    distance_to_end=abs(position[0]-end[0]) + abs(position[1]-end[1]) #Manhattan Distance
    max_dist = abs(start[0]-end[0]) + abs(start[1]-end[1]) #Manhattan Distance
    norm_dist = (max_dist - distance_to_end)/max_dist #Normalise
    return norm_dist


def new_heuristic_move(moves, position,start, end, grid_size, move):
    fitness = []
    old_move = move
    for move in moves:
        move_fitness = evaluate_move(move,position, start, end, grid_size, fitness) 
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
        move= new_move(moves,position, old_position, start, end, grid_size, old_fitness, path, move)
        position = tuple(move_position(grid_size,position,move,end))
        if position not in path:
            path.append(position)
    return[path]

def deloop (path,grid_size):
    n = 20
    delooped_path = []
    for path in range(0, len(l), n):  
        section = yield path[i:i + n] 
        section_fit = normalize(path)
        start = section[0]
        end = section[-1]
        min_dist = abs(start[0]-end[0]) + abs(start[1]-end[1])
        s_dist = calc_dist(section)

        if (s_dist/min_dist)>1.15:
           section = create_heuristic_path(moves,start, end, grid_size)
           delooped_path.append(section) 
        else:
           delooped_path.append(section)
    return delooped_path
