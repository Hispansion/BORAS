import numpy as np
import rasterio
from rasterio.transform import from_origin

def create_dem_from_array(array, dem_value, output_filename, pixel_size=1.0, origin=(0.0, 0.0), crs='EPSG:4326'):
    """
    Create a DEM GeoTIFF file from a 2D array of 0s and 1s.
    
    Parameters:
    array (2D list or numpy array): Input 2D array of 0s and 1s.
    dem_value (float): Value to use in the DEM for cells with a value of 1.
    output_filename (str): Output filename for the GeoTIFF file.
    pixel_size (float): Size of each pixel in the DEM.
    origin (tuple): Origin (upper-left corner) of the DEM (x, y).
    crs (str): Coordinate Reference System in EPSG code (default is 'EPSG:4326').
    """
    # Convert the input array to a numpy array if it's not already
    array = np.array(array)
    
    # Create the DEM array with the specified value for cells with a value of 1
    dem_array = np.where(array == 1, dem_value, 0)

    # Define the transform for the GeoTIFF file
    transform = from_origin(origin[0], origin[1], pixel_size, pixel_size)

    # Define the metadata for the GeoTIFF file
    meta = {
        'driver': 'GTiff',
        'height': dem_array.shape[0],
        'width': dem_array.shape[1],
        'count': 1,  # Number of bands
        'dtype': dem_array.dtype,
        'crs': crs,
        'transform': transform
    }

    # Save the DEM array as a GeoTIFF file
    with rasterio.open(output_filename, 'w', **meta) as dst:
        dst.write(dem_array, 1)

    print(f"DEM saved as {output_filename}")

# Example usage
example_array = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
    [0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0 ],
    [0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1 ],
    [0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1 ],
    [0, 0, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1 ],
    [0, 0, 0, 1, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0 ],
    [0, 0, 0, 1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0 ],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0 ],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0 ],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0 ],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 ],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0 ],
    [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 0, 0 ]
]

create_dem_from_array(example_array, dem_value=20, output_filename='test_case_B.tif')
