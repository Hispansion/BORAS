import numpy as np
#import richdem as rd
import rasterio as rio
from rasterio.plot import show
from rasterio.transform import Affine
import matplotlib.pyplot as plt

def calc_slope_point(position,dem):
    x =[]
    y=[]
    z=[]
    slope_point = 0
    out_grid_flag = 0
    flag_max_slope = 0
    for i in range(-1,2):
        for j in range(-1,2):
            if (position[0]+i) < (grid_size[0]-1) and (position[1]+j) < (grid_size[1]-1):
                if (position[0]-i) > 0 and (position[1]-j) > 0:
                    x.append(position[0]+i)
                    y.append(position[1]+j)
                    z.append(dem[position[0]+i][position[1]+j])
                else:
                    out_grid_flag = 1
                    break
            else:
                out_grid_flag = 1
                break
    if out_grid_flag == 0:
        x = np.array(x)
        y = np.array(y)
        z = np.array(z)
        a = np.array([[sum(np.multiply(x,x)),sum(np.multiply(x,y)),sum(x)],[sum(np.multiply(x,y)),sum(np.multiply(y,y)),sum(y)],[sum(x),sum(y),1]])
        b = np.array([[sum(np.multiply(x,z))],[sum(np.multiply(y,z))],[sum(z)]])
        a_0,a_1,a_2 = np.linalg.solve(a,b)
        slope_point = (180*np.arccos(1/np.sqrt((a_0*a_0)+(a_1*a_1)+1)))
    else:
        slope_point = 90

    return slope_point

grid_size = (200,200)

x = np.linspace(-4.0, 4.0, grid_size[0])
y = np.linspace(-4.0, 4.0, grid_size[1])
X, Y = np.meshgrid(x, y)
Z1 = np.exp(-2 * np.log(2) * ((X - 0.5) ** 2 + (Y - 0.5) ** 2) / 1 ** 2)
Z2 = np.exp(-3 * np.log(2) * ((X + 0.5) ** 2 + (Y + 0.5) ** 2) / 2.5 ** 2)
Z = 10.0 * (Z2 - Z1)
res_x = (x[-1] - x[0]) / grid_size[0]
res_y = (y[-1] - y[0]) / grid_size[1]
transform = Affine.translation(x[0] - res_x / 2, y[0] - res_y / 2) * Affine.scale(res_x, res_y)
transform

new_dataset = rio.open(
    'DEM-1.tif',
    'w',
    driver='GTiff',
    height=Z.shape[0],
    width=Z.shape[1],
    count=2,
    dtype=Z.dtype,
    crs='+proj=latlong',
    transform=transform,
) 

new_dataset.write(Z, 1)

print(Z.shape)


slope=np.zeros((grid_size[0],grid_size[1]))
for i in range(grid_size[0]):
    for j in range(grid_size[1]):
        position = (i,j)
        slope1 = calc_slope_point(position,Z)
        slope1= int(slope1)
        slope[i][j] = slope1
print(slope.shape)

new_dataset.write(slope, 2)


new_dataset.close()

