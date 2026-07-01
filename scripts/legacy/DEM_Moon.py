import numpy as np
#import richdem as rd
import rasterio as rio
from rasterio.plot import show
import matplotlib.pyplot as plt
from rasterio.transform import Affine
import elevation 

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
        slope_point = np.degrees(np.arccos(1/np.sqrt((a_0*a_0)+(a_1*a_1)+1)))
    else:
        slope_point = 90

    return slope_point


filename = "sfs_dem_200m.tif"


# convert to a numpy array
new = rio.open(filename)
print(new.shape[0])
print(new.shape[1])

# SET GRID SIZE
grid_size=(new.shape[0],new.shape[1])
Z =new.read(1).astype('float64')
new.close()

slope=np.zeros((grid_size[0],grid_size[1]))
print(slope)
for i in range(grid_size[0]):
    for j in range(grid_size[1]):
        position = (i,j)
        slope1 = calc_slope_point(position,Z)
        slope1= int(slope1)
        slope[i][j] = slope1
print(slope.shape)
fig1, ax = plt.subplots(1, figsize=(5, 5))
plt.imshow(slope, origin='lower', cmap='Greys_r',interpolation='none')
plt.colorbar()
plt.axis("on")
plt.show
dem = rio.open(
    'DEM-Moon.tif',
    'w',
    driver='GTiff',
    height=Z.shape[0],
    width=Z.shape[1],
    count=2,
    tiled =True,
    dtype=Z.dtype,
    crs='+proj=latlong',
    transform=Affine.identity(),
) 

dem.write(Z, 1)
dem.write(slope, 2)

dem.close()

dem = rio.open('DEM-Moon.tif')

dem_array = dem.read(1).astype('float64')
slope = dem.read(2).astype('float64')

dem.close()
# plot DEM 

fig2, ax = plt.subplots(1, figsize=(5, 5))
plt.imshow(dem_array, origin='lower', cmap='Greys_r',interpolation='none')
plt.colorbar()
plt.contour(dem_array, origin='lower', linewidths=0.7)
plt.axis("on")
plt.show()
