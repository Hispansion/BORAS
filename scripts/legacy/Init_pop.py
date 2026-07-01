import numpy as np
import matplotlib.pyplot as plt
import random

#INITIALIZE POPULATION(DIFFERENT RANDOM PATHS)
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
    elif x == end[0] and y == end[1]:
        new_position = position
    else:
            new_position = position
    return new_position

def new_move(moves, position, old_position,start, end, grid_size, old_fitness):
    fitness = []
    for move in moves:
       total_distance = evaluate_move(move,position, old_position, start, end, grid_size, fitness, old_fitness,path) 
       fitness.append(total_distance)
    move = random.choices(moves, weights=fitness)
    move = str(move).strip('[]')
    move = str(move).replace("'","")
    fitness= fitness[moves.index(move)]
    return[move,fitness]

def evaluate_move(move,position, old_position, start,end,grid_size, fitness, old_fitness,path):
    position = move_position(grid_size,position,move,end)
    distance_to_end=abs(position[0]-end[0]) + abs(position[1]-end[1])
    max_dist = abs(start[0]-end[0]) + abs(start[1]-end[1])
    fitness = (max_dist - distance_to_end)/max_dist
    if fitness < old_fitness:
        fitness = fitness/10
    for old_position in path:
        if position == old_position:
            fitness = fitness/20
    return fitness

def calc_dist(path):
    tot_distance=0
    for i in range((len(path[0])-1)):
        step1 = path[0][i]
        step2 = path[0][i+1]
        step_dist = abs(step1[0]-step2[0]) + abs(step1[1]-step2[1])
        tot_distance = tot_distance + step_dist

#SET GRID SIZE
grid_size=(20,20)
start=(0,0) #SELECT STARTING POINT
end=(19,19) #SELECT ENDING POINT
moves=['U', 'D', 'L', 'R' ] #POSSIBLE MOVEMENTS: UP, DOWN, LEFT & RIGHT
path = []

def create_path(moves,start, end, grid_size):
    position = start
    old_fitness = 0
    while position != end:
        old_position = position
        move, old_fitness = new_move(moves,position, old_position, start, end, grid_size, old_fitness)
        position = tuple(move_position(grid_size,position,move,end))
        if position not in path:
            path.append(position)
    return[path]

path = create_path(moves, start, end, grid_size)
print(path)
print(len(path[0]))



print(tot_distance)
fig = plt.plot(*zip(*path[0]))
plt.show()
