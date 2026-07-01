import numpy as np
import cbor2
import matplotlib.pyplot as plt

# MAKE UP TEST CASE DATA

#design your grid here - set 0 for always dark, 1 for switching, 2 for always light
landscape = np.array([
    [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [ 2, 2, 1, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2],
    [ 1, 1, 1, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 1, 2],
    [ 1, 1, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 1, 1, 2],
    [ 1, 1, 2, 2, 1, 1, 1, 2, 2, 2, 2, 2, 1, 1, 2],
    [ 2, 1, 1, 2, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 2],
    [ 2, 2, 1, 2, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2],
    [ 2, 2, 2, 2, 2, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2],
    [ 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 2, 2, 2, 2, 2],
    [ 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 2, 2, 2, 2],
    [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [ 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [ 2, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2],
    [ 2, 2, 2, 2, 2, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2],

])

#save an image so you can check your map visually
plt.imshow(landscape, cmap = "gray")
plt.savefig("landscape.png")
plt.close()


#make up start and end of time interval
start = 11000.0
end =   11100.0

#make up sunrise and sunset times for each case
sunrises_always_down = []
sunsets_always_down = []

sunrises_switch = [11000.5463636,11001.83634786]
sunsets_switch =  [11001.0345436375343,11003.24757658658]

sunrises_always_up = [start]
sunsets_always_up = [end]


#make up fake latitudes and longitudes
lats=list(np.tile(np.array([-88.9, -88.8, -88.7, -88.6, -88.5, -88.4, -88.3, -88.2, -88.1, -88.0, -87.9, -87.8, -87.7, -87.6, -87.5]), 15))
lons=list(np.repeat(np.array([89.5, 89.6, 89.7, 89.8, 89.9, 90.0, 90.1, 90.2, 90.3, 90.4, 90.5, 90.6, 90.7, 90.8, 90.9]), 15))



#ASSEMBLE DATA INTO PYTHON DICT
sun_dict = {}

sun_dict["latitudes"] = lats
sun_dict["longitudes"] = lons
sun_dict["start_epoch"] = start
sun_dict["end_epoch"] = end

for i in np.arange(15):
    for j in np.arange(15):

        if landscape[i,j] == 0:
            sun_dict[str(15*i+j)]={"sunrises": sunrises_always_down, "sunsets": sunsets_always_down}
        elif landscape[i,j] == 1:
            sun_dict[str(15*i+j)]={"sunrises": sunrises_switch, "sunsets": sunsets_switch}
        elif landscape[i,j] == 2:
            sun_dict[str(15*i+j)]={"sunrises": sunrises_always_up, "sunsets": sunsets_always_up}

print(sun_dict)

# WRITE CBOR FILE
with open('test_case_B.cbor', 'wb') as f:
    f.write(cbor2.dumps(sun_dict))
            

# LOAD CBOR FILE
with open('test_case_B.cbor', 'rb') as f:
    loaded_dict = cbor2.loads(f.read())

print(loaded_dict.keys())