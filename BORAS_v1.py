import numpy as np
#import richdem as rd
import rasterio as rio
import matplotlib
from rasterio.plot import show
import matplotlib.pyplot as plt
import time
from time import perf_counter
import elevation 
import random
import copy
import datetime
from datetime import timedelta
from numba import njit
import networkx as nx
import pyproj
from rasterio.warp import transform
from rasterio.transform import rowcol
from astropy.time import Time
from queue import PriorityQueue
import pandas as pd
import ast
# Use a headless backend so imports work in CI and non-GUI environments.
matplotlib.use("Agg")

#8-point Cardinality movement function.

def move_position(grid_size,position,move,end):
    x, y = position
    if move == "U" and y > 0:   #Upward
        new_position = (x,y-1)
    elif move== "D" and y < grid_size[1]-1:   #Downward
        new_position = (x,y+1)
    elif move == "L" and x > 0:   #Left
        new_position = (x-1,y)
    elif move == "R" and x < grid_size[0]-1:   #Right
        new_position = (x+1,y)
    elif move == "UL" and y > 0 and x > 0:  #Upward Left
        new_position = (x - 1, y - 1)
    elif move == "DL" and y < grid_size[1] - 1 and x > 0:   #Downward Left
        new_position = (x - 1, y + 1)
    elif move == "UR" and x < grid_size[0] - 1 and y > 0:   #Upward Right
        new_position = (x + 1, y - 1)
    elif move == "DR" and x < grid_size[0] - 1 and y < grid_size[1] - 1:   #Downward Left
        new_position = (x + 1, y + 1)
    elif x == end[0] and y == end[1]:
        new_position = position
    else:
        new_position = position
    return new_position

#Evaluate the move as a function of the distance to the end point

def evaluate_move(grid_size,move,start,end,position):
    norm_dist = 0
    position = move_position(grid_size,position,move,end)
    distance_to_end=np.sqrt((position[0]-end[0])**2 + (position[1]-end[1])**2) #Euclidean Distance
    max_dist = np.sqrt((start[0]-end[0])**2 + (start[1]-end[1])**2) #Euclidean Distance
    norm_dist = (max_dist - distance_to_end)/max_dist #Normalisation of the distance
    if norm_dist<0:
        norm_dist = -norm_dist/4
    if norm_dist>1:
        norm_dist = norm_dist-1
    return norm_dist

#Selection of the movement out of the 8 options, the max fitness value is selected.

def new_move(moves,start, end, grid_size,position):
    fitness = []
    for move in moves:
       total_distance = evaluate_move(grid_size,move,start,end,position) 
       fitness.append(total_distance)
    max_fitness = np.max(fitness) #Select Max fitness value movement
    move = moves[fitness.index(max_fitness)]
    move = str(move).strip('[]')
    move = str(move).replace("'","")
    fitness= fitness[moves.index(move)]
    return move

#Selection of the movement out of the 8 options, the movement selected is chosen randomly from a fitness weighed list.

def new_move2(moves,start, end, grid_size,position):
    fitness = []
    for move in moves:
       total_distance = evaluate_move(grid_size,move,start,end,position) 
       fitness.append(total_distance)
    move = random.choices(moves,fitness) #Select with probabilities based on their fitness value
    move = str(move).strip('[]')
    move = str(move).replace("'","")
    fitness= fitness[moves.index(move)]
    return move

#From a start and end point create a path segment joining those 2 points

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
    flag_max_slope = 1
    for i in range((len(path)-1)):
        position = path[i]
        slope_point = slope_dem[position[0]][position[1]]
        slope = slope + slope_point
        if slope_point > max_slope:
            flag_max_slope = 1.5
    return slope,flag_max_slope

def select_pop_max(pop, fitness,pop_size,min_max, num_to_select):
    selected =[]
    for _ in range(pop_size):
        while len(selected) != num_to_select:
            if min_max == True:
                max_fitness = max(fitness)
            else:
                max_fitness = min(fitness)
            idx_max = fitness.index(max_fitness)
            fitness.pop(idx_max)
            if pop[idx_max] not in selected:
                selected.append(pop[idx_max])
            pop.pop(idx_max)
        return selected
    
def select_pop_max2(pop, fitness,pop_size,min_max, num_to_select):
    selected =[]
    for _ in range(pop_size):
        while len(selected) != num_to_select:
            if min_max == True:
                max_fitness = max(fitness)
            else:
                max_fitness = min(fitness)
            idx_max = fitness.index(max_fitness)
            fitness.pop(idx_max)
            selected.append(pop[idx_max])
            pop.pop(idx_max)
        return selected

def select_pop_rand(pop, fitness,pop_size, num_to_select):
    selected =[]
    for i in range(num_to_select):
        x = random.randint(0,((pop_size-(pop_size-num_to_select))-i-1))
        fitness.pop(x)
        selected.append(pop[x])
        pop.pop(x)
    return selected


def crossover(parent1,parent2, moves, grid_size, dem,crossover_rate=0.9):
    if random.random()< crossover_rate:
        x = random.randint(0,2)
        #x = random.randint(0,6) for larger maps
        crossover_point1= random.randint(1,(len(parent1)-1))
        crossover_point2= random.randint(1,(len(parent2)-1))
        child = parent1[:crossover_point1] + create_path(parent1[crossover_point1],parent2[crossover_point2],moves, grid_size,dem, x) + parent2[crossover_point2:]
        return child
    else:
        return parent1
    
def crossover2(parent1,parent2, moves, grid_size, dem, crossover_rate= 0.9):
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
            crossover_points= random.randint(0,len(common_point1))
            child = parent1[:parent1.index(common_point1[crossover_points])] + parent2[parent2.index(common_point2[crossover_points]):]
            return child
    else:
        return parent1

def crossover3(parent1,parent2,crossover_rate=0.9):
    if random.random()< crossover_rate:
            crossover_point= random.randint(0,(len(parent1)-1))
            child = parent1[:crossover_point]+parent2[crossover_point:]
            return child
    else:
        return parent1

def mutation(path, end, moves, grid_size,dem, mutation_rate=0.3):
    if random.random()< mutation_rate:
        x = random.randint(0,2)
        #x = random.randint(1,3) for larger maps
        mutation_point = random.randint(1,len(path)-2)
        start = path[mutation_point]
        path = path[:mutation_point] + (create_path(start,end,moves, grid_size,dem,num_points=x))
    return path

def mutation3(path, end, moves, grid_size,dem, mutation_rate=0.3):
    if random.random()< mutation_rate:
        x = random.randint(0,2)
        #x = random.randint(1,3) for larger maps
        if random.random()< mutation_rate*0.2:
            slp_mp = 0
            same = 0
            while slp_mp < 15 and same<8:
                same += 1 
                mutation_point= random.randint(2,len(path)-1)
                mutation_point_cord = path[mutation_point]
                slp_mp = dem[mutation_point_cord[0]][mutation_point_cord[1]]
                start = path[mutation_point-1]
        else:
            mutation_point = random.randint(2,len(path)-1)
            start = path[mutation_point]

        path = path[:mutation_point] + (create_path2(start,end,moves, grid_size,dem,num_points=x))
    return path

def mutation2(path, mutation_rate=0.1):
    if random.random()< mutation_rate:
        mutation_point1= random.randint(0,(len(path)-1))
        mutation_point2= random.randint(0,(len(path)-1))
        place_holder = path[mutation_point1]
        path[mutation_point1] = path[mutation_point2]
        path[mutation_point2] = place_holder
    return path

def  termination_condition(generations, max_generations):

    return generations>= max_generations


def normalize_pop(pop,start,end,grid_size,pop_size,max_slope,slope_dem,start_epoch,roots,time_dependent):
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
        if time_dependent == True:
            tot_time1 = calc_traverse_time_w_illum(pop[i],slope_dem,start_epoch,roots)
        else:
            tot_time1 = calc_traverse_time(pop[i],slope_dem)
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
    norm_fitness = (norm_time*99 +norm_dist)/100
    norm_fitness = norm_fitness.tolist()    
    for i in range(pop_size):
        if flag_ms[i] == 1.5:
            norm_fitness[i] = norm_fitness[i]/2
    return norm_fitness,tot_slope,tot_distance


def normalize_path(path,start,end, grid_size, max_slope,slope_dem,start_epoch,roots,time_dependent):
    tot_distance = []
    tot_slope = []
    tot_time = []
    flag=1
    min_dist = np.sqrt((start[0]-end[0])**2 + (start[1]-end[1])**2)
    max_tot_distance = grid_size[0]* grid_size[1]
    max_tot_slope =max_tot_distance * 90
    tot_distance = calc_dist(path)
    tot_slope,flag= calc_slope(path,max_slope,slope_dem)
    if time_dependent == True:
        tot_time = calc_traverse_time_w_illum(path,slope_dem,start_epoch,roots)
    else:
        tot_time = calc_traverse_time(path,slope_dem)
    norm_time = (1-((tot_time-(min_dist/0.025))/tot_time))
    norm_dist =(1-(tot_distance-min_dist)/tot_distance)
    norm_slope = (max_tot_slope-tot_slope)/max_tot_slope
    #norm_fitness =(norm_slope+norm_dist+3*norm_time)/5
    norm_fitness = (norm_time*99 +norm_dist)/100
    if flag == 1.5:
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
    n = random.randint(2,round(len(path)/2)) #Has to be selected in accordance to the size of the path
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
    flag = 1
    for i in range(len(path)-1):
        step1 = path[i]
        step2 = path[i+1]
        if step1[0] != step2[0] & step1[1]!=step2[1]:
            x=np.sqrt(2)
        else:
            x=1
        position = path[i]
        speed1 = 0.025 - (0.001*slope_dem[step1[0]][step1[1]])
        speed2 = 0.025 - (0.001*slope_dem[step2[0]][step2[1]])
        speed = (speed1+speed2)/2
        if speed1 < 0.01 or speed2 < 0.01:
            speed = 0.000001
            flag = 1.5
        time_s = float(x/speed)
        time = time + time_s
    time = time*flag
    return time

#def calc_traverse_time_w_illum(path,slope_dem,start_epoch, roots):
    time = Time(start_epoch, format = 'iso', scale='tdb')
    time = time.cxcsec
    start_time = time
    flag = 1
    for position in path:
        i = (position[0]*slope_dem.shape[1]) + position[1]
        for sunrises in roots[str(i)]['sunrises']:
            for sunsets in roots[str(i)]['sunsets']:
                if time >= (sunrises * 24 * 60 * 60) and time < (sunsets * 24 * 60 * 60):
                    illumination = True
                    break
                elif sunrises > sunsets and time < (sunsets * 24 * 60 * 60):
                    illumination = True
                    break
                elif sunrises == [] and sunsets == []:
                    illumination = False
                    sunrise = np.inf
                    break
                elif (sunrises * 24 * 60 * 60) < time and (sunsets * 24 * 60 * 60) < time:
                    illumination = False
                    sunrise = np.inf
                    break
                elif (sunrises * 24 * 60 * 60) > time and (sunsets * 24 * 60 * 60) > time:
                    illumination = False
                    sunrise = sunrises * 24 * 60 * 60
                    break
        idx = path.index(position)
        if illumination == True:
            step1 = path[idx]
            if idx<len(path)-1:
                step2 = path[idx+1]
            else:
                step2 = path[idx]
            if step1[0] != step2[0] and step1[1]!=step2[1]:
                x=np.sqrt(2)
            else:
                x=1
            speed1 = 0.025 - (0.001*slope_dem[step1[0]][step1[1]])
            speed2 = 0.025 - (0.001*slope_dem[step2[0]][step2[1]])
            speed = (speed1+speed2)/2
            if speed1 < 0.01 or speed2 < 0.01:
                speed = 0.000001
                flag = 1.5
            time_s = float(x/speed)
        else:
            step1 = path[idx]
            if idx<len(path)-1:
                step2 = path[idx+1]
            else:
                step2 = path[idx]
            if step1[0] != step2[0] and step1[1]!=step2[1]:
                x=np.sqrt(2)
            else:
                x=1
            speed1 = 0.025 - (0.001*slope_dem[step1[0]][step1[1]])
            speed2 = 0.025 - (0.001*slope_dem[step2[0]][step2[1]])
            speed = (speed1+speed2)/2
            if speed1 < 0.01 or speed2 < 0.01:
                speed = 0.000001
                flag = 1.5
            if sunrise == np.inf:
                time_s == np.inf
            else:
                time_s = float(x/speed) + (sunrise-time)
        time = time + time_s
    time = (time-start_time)*flag
    #time_total = str(datetime.timedelta(seconds=time))
    return time

def calc_traverse_time_w_illum(path, slope_dem, start_epoch, roots):
    """
    Calculate the traverse time for a given path based on slope, illumination, and time.

    Args:
    - path: List of positions representing the path.
    - slope_dem: The slope DEM matrix.
    - start_epoch: Starting time in ISO format.
    - roots: Illumination data.

    Returns:
    - Total traversal time adjusted with flag (in days).
    """
    time = Time(start_epoch, format='iso', scale='tdb')
    time_in_days = time.cxcsec / (24 * 60 * 60)  # Convert initial time to days
    start_time = time_in_days
    flag = 1

    for position in path:
        i = (position[0] * slope_dem.shape[1]) + position[1]

        # Get sunrise and sunset times for this position
        sunrises = roots.get(str(i), {}).get('sunrises', [])
        sunsets = roots.get(str(i), {}).get('sunsets', [])

        illumination = False
        sunrise = np.inf

        for sunrise_time, sunset_time in zip(sunrises, sunsets):
            if time_in_days >= sunrise_time and time_in_days < sunset_time:
                illumination = True
                break
            elif sunrise_time > time_in_days:
                illumination = False
                sunrise = sunrise_time
                break

        idx = path.index(position)
        step1 = path[idx]

        # Determine the next step
        if idx < len(path) - 1:
            step2 = path[idx + 1]
        else:
            step2 = path[idx]

        # Calculate distance factor
        distance_factor = np.sqrt(2) if step1[0] != step2[0] and step1[1] != step2[1] else 1

        # Speed calculation based on slope
        speed1 = 0.025 - (0.001 * slope_dem[step1[0]][step1[1]])
        speed2 = 0.025 - (0.001 * slope_dem[step2[0]][step2[1]])
        speed = (speed1 + speed2) / 2 if speed1 >= 0.01 and speed2 >= 0.01 else 0.000001

        if illumination:
            # The sun is up, so normal travel speed applies
            time_s = float(distance_factor / speed)
            time_days = time_s / (24 * 60 * 60)  # Convert seconds to days
        else:
            # The sun is down, so delay travel until the next sunrise
            if sunrise == np.inf:
                time_days = np.inf  # Infinite time if there's no next sunrise
            else:
                wait_time_days = sunrise - time_in_days
                time_s = float(distance_factor / speed)
                time_days = time_s / (24 * 60 * 60)  # Convert seconds to days
                time_days += wait_time_days

        # Update time in days
        time_in_days += time_days

        # Update the flag if the speed was very low
        if speed1 < 0.01 or speed2 < 0.01:
            flag = 1.5

    # Calculate total time and apply the flag
    total_traverse_time = ((time_in_days - start_time) * flag)*24*60*60

    return total_traverse_time


#Creates a path by joininng the different segements

def create_path(start,end,moves, grid_size,dem, num_points):
    int_points = []
    path = []
    int_points.append(start) #First point to join by segments
    slp = 20
    for _ in range(num_points):
        while slp > 15: #Randomly searching the grid for a point with a traversable slope
            i = random.randint(0,(grid_size[0]-1))
            j = random.randint(0,(grid_size[1]-1))
            position = (i,j)
            slp = dem[i][j]
        int_points.append(position)
    int_points.append(end)
    for x in range(len(int_points)-1):
        segment = create_segment(moves,int_points[x],int_points[x+1],grid_size)
        path.extend(segment)
    return path

def create_path2(start,end,moves, grid_size,dem, num_points):
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


def crop_grid(start,end,filename,new_filename):
    dem = rio.open(filename)
    min_x = min((start[0],end[0]))
    max_x = max((start[0],end[0]))
    min_y = min((start[1],end[1]))
    max_y = max((start[1],end[1]))
    padding = 50
    # load the geotiff (a DSM in this case) and read the data - only one index in this case
    dsm_data = dem.read(1).astype('float64')

    # crop the data
    dsm_crop = dsm_data[(min_y-padding):(max_y+padding), (min_x-padding):(max_x+padding)]

    # make a copy of the geotiff metadata
    new_meta = dem.meta.copy()

    # create a translation transform to shift the pixel coordinates
    crop = rio.Affine.translation(min_x, min_y)

    # prepend the pixel translation to the original geotiff transform
    new_xform = dem.transform * crop

    # update the geotiff metadata with the new dimensions and transform
    new_meta['width'] = max_x - min_x + padding*2
    new_meta['height'] = max_y - min_y+ padding*2
    new_meta['transform'] = new_xform

    # write the cropped geotiff to disk
    with rio.open(new_filename, "w", **new_meta) as dest:
        dest.write(dsm_crop.reshape(1,dsm_crop.shape[0], dsm_crop.shape[1]))

    dest.close()
    return
def new_start_end(start,end,dem):
    new_start =[0,0]
    new_end = [0,0]
    padding = 50
    grid_size=(dem.shape[0],dem.shape[1])
    min_x = min((start[0],end[0]))
    max_x = max((start[0],end[0]))
    min_y = min((start[1],end[1]))
    max_y = max((start[1],end[1]))

    if min_x == start[0]:
        new_start[0] = padding
        new_end[0] = grid_size[0]-padding
    else:
        new_end[0] = padding
        new_start[0] = grid_size[0]-padding

    if min_y == start[1]:
        new_start[1] = padding
        new_end[1] = grid_size[1]-padding
    else:
        new_end[1] = padding
        new_start[1] = grid_size[1]-padding

    new_start = tuple(new_start)
    new_end = tuple(new_end)
    return new_start, new_end

def trans_path(start,new_start,best_ga_path):
    diff_x = start[1] - new_start[1]
    diff_y = start[0] - new_start[0]
    best_ga_path_trans = []
    for i in range(len(best_ga_path)):
        best_ga_path_trans.append(((best_ga_path[i][1]+diff_x),(best_ga_path[i][0]+diff_y)))
    return best_ga_path_trans

def translate_back_to_original(start, end,best_ga_path):
    min_x = min(start[1], end[1])
    min_y = min(start[0], end[0])
    padding = 50
    best_ga_path_trans =[]
    for (x, y) in best_ga_path:
        translated_point = (x + min_x - padding, y + min_y - padding) 
        best_ga_path_trans.append(translated_point)
    return best_ga_path_trans

def coord_to_px(waypoints_d,dem):
    waypoints = []
    moon_geographic_crs = "GEOGCS['GCS_Moon',DATUM['D_Moon',SPHEROID['Moon_localRadius',1737400,0]],PRIMEM['Reference_Meridian',0],UNIT['degree',0.0174532925199433]]"
    transformer = pyproj.Transformer.from_crs(moon_geographic_crs, dem.crs, always_xy=True)
    for point in waypoints_d:
        trans_point = transformer.transform(point[1],point[0])
        wpoint1, wpoint2 = rowcol(dem.transform,trans_point[0],trans_point[1])
        wpoint = (wpoint1,wpoint2)
        waypoints.append(wpoint)
    return waypoints

def find_closest(k):
    lst = [32,64,128,256,512,1024]
    closest_num = lst[0]
    for num in lst:
        if abs(num - k) < abs(closest_num - k):
            closest_num = num
        if num > k:
            break
    return closest_num


def evolutionary_algorithm(grid_size,start,end,moves, pop, pop_size, max_generations, deloop_flag,norm_fitness_old,max_slope,slope_dem):
    generations = 0
    fitnesses_gen = []
    best_fitness_r = 0
    same = 0
    flag =1
    while (same<= 33 or flag ==1.5) and not termination_condition(generations,max_generations):
        t1_start = perf_counter() 
        generations += 1
        old_best_fitness = best_fitness_r
        #BUILD NEXT GEN
        next_gen = []  

        #SELECT POPULATION FOR NEXT GEN
        selected_pop_size = int(pop_size/8)
        select_fitness = copy.deepcopy(norm_fitness)
        pop_w_elite = copy.deepcopy(pop)
        elite_pop = select_pop_max2(pop,select_fitness, pop_size ,True, selected_pop_size*2)
        selected_pop = select_pop_rand(pop,select_fitness, pop_size, selected_pop_size*4)
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
            child1,child2 = crossover(parent1,parent2, moves, grid_size,slope_dem), crossover(parent2,parent1, moves, grid_size,slope_dem)
            #MUTATION
            child1,child2 = mutation(child1,end, moves, grid_size,slope_dem),mutation(child2,end, moves, grid_size,slope_dem)
            next_gen.append(child1)
            next_gen.append(child2)

        #IMIGRANT POPULATION
        for i in range(selected_pop_size*2):
            x=random.randint(1,8) # Size according length of path or grid
            imigrant = create_path(start,end,moves, grid_size,slope_dem,num_points=x)
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


        #GENERATION INFO
        best_fitness = max(norm_fitness)
        best_fitness_r = round(best_fitness,12)

        fitnesses_gen.append(best_fitness)
        best_path_idx = norm_fitness.index(best_fitness)
        print(f'Generation {generations}: Best fitness = {best_fitness}.')
        t1_stop = perf_counter()
        if best_fitness_r == old_best_fitness:
            same = same + 1
        else:
            same = 0
        best_path = pop[best_path_idx]
        _,flag = calc_slope(best_path,max_slope,slope_dem)
    best_t_dist = tot_distance[best_path_idx]
    best_t_slp =  tot_slope[best_path_idx]
    print('Total distance:',best_t_dist)
    print('Total slope:',best_t_slp)
    
    gen_compt = (t1_stop-t1_start)

    return best_path, fitnesses_gen, gen_compt

def evolutionary_algorithm2(grid_size,start,end,moves, pop, pop_size, max_generations, deloop_flag,norm_fitness,max_slope,slope_dem,start_epoch,roots,time_dependent):
    generations = 0
    fitnesses_gen = []
    best_fitness_r = 0
    same = 0
    flag =1.5
    while (same<=100 or flag ==1.5) and not termination_condition(generations,max_generations):
        
        t1_start = perf_counter() 
        generations += 1
        old_best_fitness = best_fitness_r
        #BUILD NEXT GEN
        next_gen = []  
        #SELECT POPULATION FOR NEXT GEN
        selected_pop_size = int(pop_size/8)
        select_fitness = copy.deepcopy(norm_fitness)
        pop_w_elite = copy.deepcopy(pop)
        elite_pop = select_pop_max2(pop_w_elite,select_fitness, pop_size ,True, selected_pop_size*1)
        pop_copy = copy.deepcopy(pop)
        selected_pop = select_pop_rand(pop_w_elite,select_fitness, pop_size, selected_pop_size*5)
        selected_pop = selected_pop + elite_pop

        #ELITE
        for i in range(selected_pop_size*1):
            next_gen.append(elite_pop[i])
        
        pop_indexes = list(np.arange(0,(selected_pop_size*5),1,dtype=int))

        #GENERAL    
        for i in range(0, (selected_pop_size*5),2):
            i,j = random.sample(pop_indexes,k=2)
            pop_indexes.remove(i)
            pop_indexes.remove(j)
            parent1 =[]
            parent2=[]
            child1=[]
            child2=[]
            parent1 , parent2 = selected_pop[i],selected_pop[j]
            child1,child2 = crossover(parent1,parent2, moves, grid_size,slope_dem), crossover(parent2,parent1, moves, grid_size,slope_dem)
            #MUTATION
            child1,child2 = mutation(child1,end, moves, grid_size,slope_dem),mutation(child2,end, moves, grid_size,slope_dem)
            next_gen.append(child1)
            next_gen.append(child2)

        #IMIGRANT POPULATION
        for i in range(selected_pop_size*2):
            x=random.randint(1,2) # Size according length of path or grid
            imigrant = create_path(start,end,moves, grid_size,slope_dem,num_points=x)
            next_gen.append(imigrant)
        if len(next_gen) != pop_size:
            print("Next GEN Size different than Pop Size")
            break 
    

        #EVALUATE POPULATION
        norm_fitness = []
        norm_fitness,tot_slope,tot_distance = normalize_pop(next_gen,start,end,grid_size,pop_size,max_slope,slope_dem,start_epoch,roots,time_dependent)
        if norm_fitness == [0]*len(norm_fitness):
            print('Norm_fitness is full of zeros')
            break 

        #DELOOP
        for i in range(pop_size):
            if deloop_flag == True:
                delooped_path = deloop(next_gen[i],grid_size,moves)
                delooped_fitness = normalize_path(delooped_path,start,end, grid_size, max_slope,slope_dem,start_epoch,roots,time_dependent)
                if norm_fitness[i] <= delooped_fitness:
                    next_gen[i] = delooped_path
                    norm_fitness[i] = delooped_fitness

        #EVALUATE POPULATION
        norm_fitness = []
        norm_fitness,tot_slope,tot_distance = normalize_pop(next_gen,start,end,grid_size,pop_size,max_slope,slope_dem,start_epoch,roots,time_dependent)
        for i in range(pop_size):
            if norm_fitness == [0]*len(norm_fitness):
                print('Norm_fitness is full of zeros')
                break 
        
        pop[:] = next_gen
    
        #GENERATION INFO
        best_fitness = max(norm_fitness)
        best_fitness_r = round(best_fitness,12)

        fitnesses_gen.append(best_fitness)
        best_path_idx = norm_fitness.index(best_fitness)
        print(f'Generation {generations}: Best fitness = {best_fitness}.')
        t1_stop = perf_counter()
        if best_fitness_r == old_best_fitness:
            same = same + 1
        else:
            same = 0
        best_path = pop[best_path_idx]
        _,flag = calc_slope(best_path,max_slope,slope_dem)
    best_t_dist = tot_distance[best_path_idx]
    best_t_slp =  _
    print('Total distance:',best_t_dist)
    print('Total slope:',best_t_slp)
    print(flag)
    
    gen_compt = (t1_stop-t1_start)

    return best_path, fitnesses_gen, gen_compt

def ga(start,end,dem,start_epoch,roots,time_dependent):
    t1_start = perf_counter() 

    #DEM 

    #filename = "lunargem_4to5_slope.tif"
    #dem = rio.open(filename)
    #print(filename)
    slope_dem = dem.read(1).astype('float64')

    # SET GRID SIZE
    grid_size=(dem.shape[0],dem.shape[1])
    moves=["U", "D", "L", "R","UL", "DL", "UR", "DR"]

    #SYSTEM CONSTRAINTS
    max_slope = 15

    # INITIALIZE POPULATION(DIFFERENT RANDOM PATHS)
    
    pop_size = find_closest((np.sqrt(grid_size[0]**2+grid_size[1]**2)/5)) #Function to approximate the population size atuomatically based on the size of the map/exploration space.
    #pop_size= 128 #Always multiples of 8!
    print("Population size =", pop_size)
    pop = []
    max_generations= 1000
    deloop_flag = True


    for i in range(pop_size):
        x=random.randint(1,5) #Size depending on the length of the path or grid size
        populant = create_path(start,end,moves, grid_size, slope_dem, num_points=x)
        pop.append(populant)

    #EVALUATE POPULATION
    norm_fitness_old = []
    norm_fitness_old,tot_slope,tot_distance = normalize_pop(pop,start,end,grid_size,pop_size,max_slope,slope_dem,start_epoch,roots,time_dependent)
    for i in range(pop_size):
        if deloop_flag == True:
            delooped_path = deloop(pop[i],grid_size,moves)
            delooped_fitness = normalize_path(delooped_path,start,end, grid_size, max_slope,slope_dem,start_epoch,roots,time_dependent)
            if norm_fitness_old[i] <= delooped_fitness:
                pop[i] = delooped_path
                norm_fitness_old[i] = delooped_fitness

    #GENERATION INFO
    best_fitness = max(norm_fitness_old)
    best_path_idx = norm_fitness_old.index(best_fitness)
    print(f'Generation 0: Best fitness = {best_fitness}.')
    
    # RUN EVOLUTIONARY ALGORITHM

    best_path,fitnesses_gen,gen_compt = evolutionary_algorithm2(grid_size,start,end,moves, pop, pop_size, max_generations, deloop_flag,norm_fitness_old,max_slope,slope_dem,start_epoch,roots,time_dependent)
    t1_stop = perf_counter()

    print('Best path found:',best_path)
    print("Elapsed time during the whole program in minutes:", (t1_stop-t1_start)/60)
    #traverse_time = calc_traverse_time(best_path)
    if time_dependent == True:
        tot_time = calc_traverse_time_w_illum(best_path,slope_dem,start_epoch,roots)
    else:
        tot_time = calc_traverse_time(best_path,slope_dem)
    if np.isnan(tot_time) != True:
        traverse_time = str(datetime.timedelta(seconds=tot_time))
        print ('Total traverse time:',traverse_time)
    return best_fitness,fitnesses_gen,tot_time,best_path

def djikistras(start,end,slope_dem):
    t1_start = perf_counter()
    max_slope = 15
    # Create a directed graph
    G = nx.DiGraph()
    
    rows, cols = slope_dem.shape

    # Function to add edges to the graph with weights calculated from the fitness function
    def add_edges_with_weights(G, slope_dem, fitness_function):
        rows, cols = slope_dem.shape
        for i in range(rows):
            for j in range(cols):
                # Current node
                current_node = (i, j)
                # Define neighbors (8-connectivity)
                neighbors = [
                    (i-1, j-1), (i-1, j), (i-1, j+1),
                    (i, j-1),           (i, j+1),
                    (i+1, j-1), (i+1, j), (i+1, j+1)
                ]
                for neighbor in neighbors:
                    ni, nj = neighbor
                    if 0 <= ni < rows and 0 <= nj < cols:
                        # Compute the weight using the fitness function
                        weight = fitness_function((i, j),(ni, nj),slope_dem)
                        # Add edge to the graph
                        G.add_edge(current_node, neighbor, weight=weight)

    def fitness_function(step1, step2,slope_dem):
        if step1[0] != step2[0] & step1[1]!=step2[1]:
            x=np.sqrt(2)
        else:
            x=1
        speed1 = 0.025 - (0.001*slope_dem[step1[0]][step1[1]])
        speed2 = 0.025 - (0.001*slope_dem[step2[0]][step2[1]])
        speed = (speed1+speed2)/2
        if speed1 < 0.01 or speed2 < 0.01:
            speed = 0.0000001
        time_s = float(x/speed)
        return time_s  # Example fitness function: absolute difference in slope

    # Add edges to the graph
    add_edges_with_weights(G, slope_dem, fitness_function)
    shortest_path = nx.dijkstra_path(G, start, end)
    shortest_path_length = nx.dijkstra_path_length(G, start, end)
    t1_stop = perf_counter()

    best_t_dist = calc_dist(shortest_path)
    best_t_slp, flag = calc_slope(shortest_path, max_slope,slope_dem)
    if flag == 1:
        print('Path is feasible')
    else:
        print('Path is unfeasible, slope constraints violated')
    print('Total distance:',best_t_dist)
    print('Total slope:',best_t_slp)
    print('Best path found:',shortest_path)
    print("Elapsed time during the whole program in seconds:", (t1_stop-t1_start))
    #traverse_time = calc_traverse_time(best_path)
    traverse_time = str(datetime.timedelta(seconds=shortest_path_length))
    print ('Total traverse time:',traverse_time)
    return shortest_path_length,shortest_path

import numpy as np
from queue import PriorityQueue
import time

class Graph(object):
    def __init__(self, vertices, edges, weights):
        self.vertices = vertices
        self.edges = edges
        self.weights = weights
        self.in_adj = list()
        self.out_adj = list()

        for v in vertices:
            self.in_adj.append(list())
            self.out_adj.append(list())

        for e in edges:
            self.in_adj[e[1]].append(e)
            self.out_adj[e[0]].append(e)


class Pair(object):
    def __init__(self, tau, g, v):
        self.tau = tau
        self.g = g
        self.v = v

    def __lt__(self, other):
        return self.g[self.tau[self.v]] < other.g[other.tau[other.v]]

    def __str__(self):
        return str((self.v, self.tau[self.v], self.g[self.tau[self.v]]))

    def __repr__(self):
        return str((self.v, self.tau[self.v], self.g[self.tau[self.v]]))


def print_queue(Q):
    print("Current queue state:")
    for item in Q.queue:
        print(item)


def generate_graph_with_weights(slope_dem, roots, T):
    """
    Generate a time-expanded graph with weights.

    Args:
    - slope_dem: DEM containing the slope information.
    - roots: Illumination data.
    - T: Time range (in seconds).

    Returns:
    - vertices, edges, weights: The graph structure.
    """
    rows, cols = slope_dem.shape
    vertices = {}
    edges = []
    weights = {}

    vertex_id = 0
    for i in range(rows):
        for j in range(cols):
            vertices[(i, j)] = vertex_id
            vertex_id += 1

    for i in range(rows):
        for j in range(cols):
            current_node = (i, j)
            current_vertex = vertices[current_node]

            neighbors = [
                (i-1, j-1), (i-1, j), (i-1, j+1),
                (i, j-1),           (i, j+1),
                (i+1, j-1), (i+1, j), (i+1, j+1)
            ]
            for neighbor in neighbors:
                ni, nj = neighbor
                if 0 <= ni < rows and 0 <= nj < cols:
                    neighbor_vertex = vertices[(ni, nj)]
                    edges.append((current_vertex, neighbor_vertex))

                    def dynamic_weight_function(t, current_node=current_node, neighbor_node=(ni, nj)):
                        return generate_weight_function(slope_dem, roots, current_node, neighbor_node, t)()

                    weights[(current_vertex, neighbor_vertex)] = dynamic_weight_function

    return list(vertices.values()), edges, weights

def generate_weight_function(slope_dem, roots, node1, node2, t):
    """
    Generate a weight function based on slope, illumination, and time.

    Args:
    - slope_dem: The slope DEM matrix.
    - roots: Illumination data.
    - node1, node2: Coordinates of the two nodes (start and end).
    - t: Current time in days.

    Returns:
    - A function that computes the travel time between node1 and node2.
    """
    time_in_days = t
    i = node2[0] * slope_dem.shape[1] + node2[1]  # Convert the node coordinates to a unique index

    # Fetch sunrises and sunsets for the current node
    sunrises = roots.get(str(i), {}).get('sunrises', [])
    sunsets = roots.get(str(i), {}).get('sunsets', [])

    if not sunrises or not sunsets:
        print(f"Warning: Missing sunrises/sunsets for node {node2}. Defaulting to infinite weight.")
        return lambda: np.inf  # Return an infinite weight if data is missing
    
    illumination = False
    sunrise = np.inf  # Set the next sunrise to infinity as a fallback

    # Check illumination conditions
    for sunrise_time, sunset_time in zip(sunrises, sunsets):
        sunrise_seconds = sunrise_time
        sunset_seconds = sunset_time

        # Ensure consistent unit handling
        if time_in_days >= sunrise_seconds and time_in_days < sunset_seconds:
            illumination = True
            break
        elif sunrise_seconds > time_in_days:
            illumination = False
            sunrise = sunrise_seconds
            break

    def weight_function():
        """
        Calculate the traversal time between node1 and node2 based on whether the sun is up and the slope.
        """
        # Slope constraint: if slope exceeds 15°, assign a large travel time (invalid path)
        if slope_dem[node1[0]][node1[1]] > 15 or slope_dem[node2[0]][node2[1]] > 15:
            return np.inf  # Invalid path due to high slope

        distance_factor = np.sqrt(2) if node1[0] != node2[0] and node1[1] != node2[1] else 1

        # Speed calculation based on slope and illumination
        speed1 = 0.025 - (0.001 * slope_dem[node1[0]][node1[1]])
        speed2 = 0.025 - (0.001 * slope_dem[node2[0]][node2[1]])
        speed = (speed1 + speed2) / 2 if speed1 >= 0.01 and speed2 >= 0.01 else 0.000001

        if illumination:
            # The sun is up, so normal travel speed applies
            time_s = float(distance_factor / speed)
            time_days = time_s / (24 * 60 * 60)  # Convert seconds to days
        else:
            # The sun is down, so delay travel until the next sunrise
            wait_time_days = sunrise - time_in_days
            time_s = float(distance_factor / speed)
            time_days = time_s / (24 * 60 * 60)  # Convert seconds to days
            time_days += wait_time_days
        return time_days
    return weight_function


def time_refinement(Gt, vs, ve, T, check_fifo):
    """
    Refine the arrival times at each vertex for each possible start time in T.
    
    Args:
    - Gt: The graph.
    - vs: Start vertex.
    - ve: End vertex.
    - T: List of time steps.
    - check_fifo: Boolean to check if the graph is FIFO and apply a transformation if not.
    
    Returns:
    - A dictionary g where g[v][t] is the earliest arrival time at vertex v starting at time t.
    """
    ts = T[0]  # Start time
    te = T[-1]  # End time
    g = {v: {t: np.inf for t in T} for v in Gt.vertices}
    g[vs][ts] = ts  # The cost to reach vs at time ts is 0
    tau = {v: ts for v in Gt.vertices}  # Initialize tau as starting time
    
    Q = PriorityQueue()
    Q.put(Pair(tau, g[vs], vs))

    while not Q.empty():
        pair_i = Q.get()
        v_i = pair_i.v
        tau_i = tau[v_i]
        
        if tau_i >= te:
            continue

        for e in Gt.out_adj[v_i]:
            v_j = e[1]
            for t in T:
                if t < tau_i:
                    continue

                g_i_t = g[v_i][t]
                weight = Gt.weights[e](t)  # Call the weight function

                new_g = g_i_t + weight
                if new_g < g[v_j][t]:
                    g[v_j][t] = new_g
                    Q.put(Pair(tau, g[v_j], v_j))
                    tau[v_j] = t

                # Check for FIFO property
                if check_fifo and new_g < g[v_j][t]:
                    print(f"Non-FIFO detected for edge {e}, applying transformation.")
                    g[v_j][t] = max(g[v_i][t] + Gt.weights[e](t), g[v_j][t])  # Apply the transformation for non-FIFO

    return g



def path_selector(Gt, g, vs, ve, t_star, T):
    path = []
    path_times = []
    current_node = ve
    current_time = t_star
    total_traverse_time = 0

    while current_node != vs:
        found_previous = False
        for e in Gt.in_adj[current_node]:
            prev_node = e[0]
            edge_weight = Gt.weights[e](current_time)
            # Find the closest time in g[prev_node]
            available_times = list(g[prev_node].keys())
            closest_time = min(available_times, key=lambda t: abs(t - current_time))

            # Check if the edge satisfies the backtracking condition
            if g[prev_node][closest_time] + edge_weight == g[current_node][current_time]:
                path.append((prev_node, current_node))
                path_times.append(current_time-edge_weight)
                current_node = prev_node
                current_time = closest_time
                total_traverse_time += edge_weight
                found_previous = True
                break

        if not found_previous:
            print(f"Could not find valid previous node for {current_node} at time {current_time}")
            raise ValueError("Invalid path selection. No valid previous node found.")

    path = list(reversed(path))
    path_times = list(reversed(path_times))  # Reverse the path since we traced it backward
    #path_times = list(reversed(path_times))  # Reverse the times to match the path
    return path, total_traverse_time, path_times

def algorithm(Gt, vs, ve, T):
    """
    Main algorithm that handles the time-dependent shortest path search.

    Args:
    - Gt: The graph.
    - vs: Start vertex.
    - ve: End vertex.
    - T: List of time steps.

    Returns:
    - t_star: Optimal start time.
    - path: The best path found.
    - total_traverse_time: Total travel time for the path.
    """
    # Refine the arrival times at each vertex
    g = time_refinement(Gt, vs, ve, T, check_fifo=True)  # Check for FIFO and apply transformation if needed
    

    # Find the earliest arrival time at the destination vertex (`ve`)
    t_star = min(g[ve], key=lambda t: g[ve][t])
    print(t_star)
    # Use the earliest arrival time as the starting point for backtracking
    if not np.isinf(g[ve][t_star]):
        path, total_traverse_time, path_times = path_selector(Gt, g, vs, ve, t_star, T)
        return t_star, path, total_traverse_time, path_times
    else:
        return None


def TDD_expanded(start, end, slope_dem, roots, T): #one being used
    """
    Time-Dependent Dijkstra with time expansion for non-FIFO graphs.
    """
    # Convert start and end to linear index based on the DEM shape
    vs = (start[0] * slope_dem.shape[1]) + start[1]
    ve = (end[0] * slope_dem.shape[1]) + end[1]

    # Generate graph with weights
    vertices, edges, weights = generate_graph_with_weights(slope_dem, roots, T)
    Gt = Graph(vertices, edges, weights)

    print("The Graph has been correctly generated")
    start_time = time.time()

    result = algorithm(Gt, vs, ve, T)

    # Check if a valid path was found
    if result:
        t_star, p_star, total_traverse_time, path_times = result
        start_time_str, formatted_path, total_time_str = format_path(vertices, p_star, total_traverse_time, slope_dem.shape, t_star)
        
        print(f"Optimal Departure Time: {start_time_str}")
        print(f"Path Taken: {formatted_path}")
        print(f"Total Traverse Time: {total_traverse_time}")
        return start_time_str, formatted_path, total_traverse_time, path_times
    else:
        print("No valid path found.")
        return None,None,None,None

def vertex_to_dem_coordinates(vertex_id, dem_shape):
    """
    Convert a vertex ID back to DEM coordinates.
    """
    rows, cols = dem_shape
    i = vertex_id // cols
    j = vertex_id % cols
    return (i, j)


def format_path(vertices, path, total_traverse_time, dem_shape, start_time):
    """
    Format the output path to show DEM coordinates and traverse time.
    """
    formatted_path = []
    current_time = start_time

    for start, end in path:
        start_coords = vertex_to_dem_coordinates(start, dem_shape)
        formatted_path.append(start_coords)
        current_time += total_traverse_time / len(path)

    end_coords = vertex_to_dem_coordinates(path[-1][1], dem_shape)
    formatted_path.append(end_coords)

    total_time_str = total_traverse_time
    start_time_str = start_time

    return start_time_str, formatted_path, total_time_str




def vertex_to_dem_coordinates1(vertex_id, dem_shape, time_expanded, time_units):
    """
    Convert a vertex ID back to DEM coordinates.
    Handles both regular and time-expanded vertices.
    - time_expanded: True if the graph is time-expanded.
    - time_units: The number of time units per vertex in the time-expanded graph.
    """
    rows, cols = dem_shape

    if time_expanded and time_units is not None:
        # If the graph is time-expanded, split the vertex ID into spatial and time components
        spatial_vertex_id = vertex_id // time_units
        time_unit = vertex_id % time_units

        # Convert spatial vertex ID back to DEM coordinates
        i = spatial_vertex_id // cols
        j = spatial_vertex_id % cols

        return (i, j), time_unit  # Return both spatial coordinates and time unit
    else:
        # Regular (FIFO) graph, no time expansion
        i = vertex_id // cols
        j = vertex_id % cols
        return (i, j)



def format_path1(vertices, path, total_traverse_time, dem_shape, start_time, time_expanded, time_units=None):
    """
    Format the output path to show DEM coordinates and traverse time.
    Handles both FIFO and non-FIFO graphs.
    - time_expanded: True if the graph is time-expanded.
    - time_units: The number of time units per vertex in the time-expanded graph.
    """
    formatted_path = []
    current_time = start_time

    # Iterate through the path and format both the coordinates and time
    for start, end in path:
        if time_expanded:
            # For time-expanded graphs, we need to extract both spatial and time information
            start_coords, start_time_unit = vertex_to_dem_coordinates1(start, dem_shape, time_expanded=True, time_units=time_units)
            formatted_path.append((start_coords, start_time_unit))  # Append with time unit
            
            # In time-expanded graphs, time is usually attached to the node, so we don't manually add traverse time
            current_time = start_time_unit
        else:
            # For regular FIFO graphs, we just append the DEM coordinates
            start_coords = vertex_to_dem_coordinates(start, dem_shape)
            formatted_path.append(start_coords)

            # Update current time based on traversal time
            current_time += total_traverse_time / len(path)

    # Handle the final end point
    if time_expanded:
        end_coords, end_time_unit = vertex_to_dem_coordinates(path[-1][1], dem_shape, time_expanded=True, time_units=time_units)
        formatted_path.append((end_coords, end_time_unit))
        current_time = end_time_unit
    else:
        end_coords = vertex_to_dem_coordinates(path[-1][1], dem_shape)
        formatted_path.append(end_coords)

    total_time_str = current_time-start_time
    start_time_str = start_time

    return start_time_str, formatted_path, total_time_str


def generate_time_range_seconds(start_days, end_days, resolution_days):
    """
    Generate a time range in seconds with a given resolution in days.
    Converts the time range from days to seconds.
    
    Args:
    - start_days: Starting time in days.
    - end_days: Ending time in days.
    - resolution_days: Resolution of the time steps in days.
    
    Returns:
    - List of time points in seconds.
    """
    start_seconds = start_days * 24 * 60 * 60
    end_seconds = end_days * 24 * 60 * 60
    resolution_seconds = resolution_days * 24 * 60 * 60
    
    num_steps = int((end_seconds - start_seconds) / resolution_seconds) + 1
    return [start_seconds + i * resolution_seconds for i in range(num_steps)]



def non_FIFO_time_dependent_dijkstra(Gt, vs, ve, T, max_wait_time=1000, wait_step=100):
    """
    Optimized Time-dependent Dijkstra for non-FIFO graphs with limited wait times.
    
    Args:
    - Gt: The original graph (vertices, edges, weights).
    - vs: Start node.
    - ve: End node.
    - T: Time range for travel.
    - max_wait_time: Maximum allowable waiting time at each node (default 1,000 seconds).
    - wait_step: Interval to step through while waiting at a node (default 100 seconds).
    
    Returns:
    - opt_start_time: Optimal start time.
    - best_path: Best path (sequence of nodes).
    - total_traverse_time: Total travel time.
    """
    # Priority queue for selecting the node with the smallest cost
    Q = PriorityQueue()
    
    # Initialize arrival times to infinity
    arrival_times = {v: {t: np.inf for t in T} for v in Gt.vertices}
    arrival_times[vs][T[0]] = T[0]  # Start node has arrival time of T[0]
    
    # For storing the best path
    predecessors = {v: None for v in Gt.vertices}
    
    # Push the start node into the priority queue
    Q.put((T[0], vs, T[0]))  # (cost, node, time)
    
    while not Q.empty():
        current_time, current_node, arrival_time_at_current = Q.get()

        if current_node == ve:
            break  # Stop when we reach the destination

        for edge in Gt.out_adj[current_node]:
            u, v = edge  # (current_node -> neighbor)
            
            # Get the weight for the current time
            travel_time = Gt.weights[(u, v)](arrival_time_at_current)
            if travel_time == np.inf:
                continue  # Skip this edge if it's not traversable at this time
            
            new_arrival_time = arrival_time_at_current + travel_time
            
            # Check if this arrival time improves on the known best time
            if new_arrival_time < arrival_times[v].get(current_time, np.inf):
                arrival_times[v][current_time] = new_arrival_time
                predecessors[v] = u  # Update the predecessor of v
                
                # Push the new state into the queue
                Q.put((new_arrival_time, v, new_arrival_time))
                
            # Consider limited waiting at the node to improve travel time
            for wait_time in range(0, max_wait_time + 1, wait_step):  # Step through limited wait times
                future_time = arrival_time_at_current + wait_time
                future_travel_time = Gt.weights[(u, v)](future_time)
                
                if future_travel_time == np.inf:
                    continue  # Skip if waiting doesn't help
                
                future_arrival_time = future_time + future_travel_time
                
                if future_arrival_time < arrival_times[v].get(future_time, np.inf):
                    arrival_times[v][future_time] = future_arrival_time
                    predecessors[v] = u
                    Q.put((future_arrival_time, v, future_arrival_time))
    
    # Reconstruct the best path
    if arrival_times[ve][current_time] == np.inf:
        return None  # No valid path found

    path = []
    current = ve
    while current != vs:
        path.append(current)
        current = predecessors[current]
    path.append(vs)
    
    return arrival_times[ve][current_time], list(reversed(path)), arrival_times[ve][current_time] - T[0]




def TDD(start, end, slope_dem, roots, T, consider_wait_time=True):
    """
    Main function to execute Time-Dependent Dijkstra (TDD) algorithm.
    """
    vs = (start[0] * slope_dem.shape[1]) + start[1]
    ve = (end[0] * slope_dem.shape[1]) + end[1]

    # Generate the graph with weights
    vertices, edges, weights = generate_graph_with_weights(slope_dem, roots, T)
    Gt = Graph(vertices, edges, weights)
    
    print(f"Total vertices created: {len(vertices)}")
    print('The Graph has been correctly generated')

    # Run the main algorithm
    start_time = time.time()
    result = algorithm(Gt, vs, ve, T, consider_wait_time)

    # Check if a valid path was found
    if result:
        t_star, p_star, total_traverse_time, path_times = result
        start_time_str, formatted_path, total_time_str = format_path(vertices, p_star, total_traverse_time, slope_dem.shape, t_star)
        
        print(f"Optimal Departure Time: {start_time_str}")
        print(f"Path Taken: {formatted_path}")
        print(f"Total Traverse Time: {total_time_str}")
        return start_time_str, formatted_path, total_time_str, path_times
    else:
        print("No valid path found.")
        return None
    


def TDD_non_FIFO(start, end, slope_dem, roots, T, max_wait_time=1000, wait_step=100):
    """
    Time-dependent Dijkstra for non-FIFO graphs using dynamic relaxation with limited wait times.

    Args:
    - start: Starting point in the DEM (e.g., (i, j)).
    - end: End point in the DEM (e.g., (i, j)).
    - slope_dem: DEM containing the slope information.
    - roots: Dictionary containing illumination information (sunrises, sunsets).
    - T: Time range for travel.
    - max_wait_time: Maximum allowable waiting time at each node (default 1,000 seconds).
    - wait_step: Interval for stepping through waiting times (default 100 seconds).

    Returns:
    - opt_start_time: Optimal start time for the journey.
    - best_path: The best path (sequence of nodes).
    - total_traverse_time: Total time to travel the path.
    """
    vs = (start[0] * slope_dem.shape[1]) + start[1]
    ve = (end[0] * slope_dem.shape[1]) + end[1]

    # Generate the original graph with time-dependent weights
    vertices, edges, weights = generate_graph_with_weights(slope_dem, roots, T)
    Gt = Graph(vertices, edges, weights)

    # Run the optimized non-FIFO time-dependent Dijkstra algorithm
    start_time = time.time()
    result = non_FIFO_time_dependent_dijkstra(Gt, vs, ve, T, max_wait_time, wait_step)
    
    if result:
        opt_start_time, best_path, total_traverse_time = result
        formatted_start_time, formatted_path, total_time = format_path(Gt, best_path, total_traverse_time, slope_dem.shape, opt_start_time)
        print(f"Optimal Departure Time: {formatted_start_time}, Path Taken: {formatted_path}, Total Traverse Time: {total_time}")
        return formatted_start_time, total_time, formatted_path
    else:
        print("No valid path found.")
        return None



def vertex_to_dem_coordinates(vertex_id, dem_shape):
    rows, cols = dem_shape
    i = vertex_id // cols
    j = vertex_id % cols
    return (i, j)

def seconds_to_hhmmss(seconds):
    return str(timedelta(seconds=int(seconds)))

def format_path(vertices, path, total_traverse_time, dem_shape, start_time):
    formatted_path = []
    current_time = start_time

    for start, end in path:
        start_coords = vertex_to_dem_coordinates(start, dem_shape)
        formatted_path.append(start_coords)
        current_time += total_traverse_time / len(path)
    
    end_coords = vertex_to_dem_coordinates(path[-1][1], dem_shape)
    formatted_path.append(end_coords)

    total_time_str = int(total_traverse_time)
    start_time_str = start_time
    
    return start_time_str, formatted_path, total_time_str

def generate_time_range(start, end, resolution):
    values = []
    current = start
    tolerance = abs(resolution) * 1e-9

    while current <= end + tolerance:
        values.append(round(current, 12))
        current += resolution

    return values

def parse_input_file(file_path):
    params = {}
    with open(file_path, 'r') as f:
        for line in f:
            if '=' in line:
                key, value = line.strip().split('=', 1)
                if value:  # If the value is not empty
                    try:
                        params[key] = ast.literal_eval(value)
                    except ValueError:
                        params[key] = value  # If it's a string, keep it as is
                else:
                    params[key] = None  # Handle empty value
            else:
                continue
    return params
