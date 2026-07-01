import numpy as np
#import richdem as rd
import rasterio as rio
from rasterio.plot import show
from rasterio.transform import rowcol
import matplotlib.pyplot as plt
import elevation 
import pyproj
from rasterio.warp import transform
import BORAS_v1

filename = "plateau_2m_slope_1m.tif"
#filename = "lunargem_4to5_slope.tif"
#filename = 'plateau_2m_slope_1m_fixed.tif'
#filename = 'Wp2_3_slope.tif'
#filename = 'aarls4_slope.tif'
#filename = "lunargem_4to5_slope.tif"
#filename = "DEM-1.tif"
#filename = "DEM-Moon.tif"
#filename = "sfs_slope_200m.tif"
filename='aarls4_50x50_slope.tif'

#filename ="test_case_A.tif"
#BORAS_v1.crop_grid((2655, 1078),(2666, 1366),filename,new_filename)
# convert to a numpy array
dem = rio.open(filename)
print(dem.shape[0])
print(dem.shape[1])
print(dem.count)
dem_array = dem.read(1).astype('float64')
#slope = dem.read(2).astype('float64')
print(dem.transform*(0,0))
print(dem.crs)
print(rowcol(dem.transform,-5008199.5, 566179.5))
# plot DEM 
fig2, ax = plt.subplots(1, figsize=(5, 6))
plt.imshow(dem_array, cmap='Greys_r',interpolation='none')
plt.colorbar()
plt.title('Slope Map (in Degrees)')
plt.xlabel('Column Index')
plt.ylabel('Row Index')
#plt.contour(dem_array, origin='lower', linewidths=0.7)
plt.axis("on")
plt.show()

# Define CRS
moon_geographic_crs = "GEOGCS['GCS_Moon',DATUM['D_Moon',SPHEROID['Moon_localRadius',1737400,0]],PRIMEM['Reference_Meridian',0],UNIT['degree',0.0174532925199433]]"


transformer = pyproj.Transformer.from_crs(moon_geographic_crs, dem.crs, always_xy=True)


waypoints = [(5.3404, 18.6970),(5.3341, 18.6916), (5.3293,18.6873), (5.3297,18.6778),(5.3230,18.6714),(5.3299,18.6666),(5.3249,18.6531),(5.3265,18.6433),(5.3299,18.6385),(5.3413,18.6359),(5.3454,18.6223)]
for point in waypoints:
    trans_point = transformer.transform(point[0],point[1])
    print(rowcol(dem.transform,trans_point[0],trans_point[1]))
# Now use these transformed coordinates

