# Data Layout

BORAS input assets are organized here for easier access.

## Folders

- `data/dems/`: primary DEM and slope raster inputs used by configs and notebooks.
- `data/illumination/`: CBOR illumination inputs used by time-dependent runs.
- `data/reference_dems/`: additional reference raster files that were previously stored in `Files/`.

## Notes

- The large `.tif` and `.cbor` files remain ignored by Git, but this folder structure keeps them in one predictable place locally.
- Config files in `configs/` now point to these `data/` locations.
- Most notebook references were updated to use the same paths, so the assets are easier to find and reuse.
