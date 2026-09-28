# Data Layout

BORAS input assets are organized here for easier access.

## Folders

- `data/dems/`: primary DEM and slope raster inputs used by configs and notebooks.
- `data/illumination/`: CBOR illumination inputs used by time-dependent runs.
- `data/reference_dems/`: additional reference raster files that were previously stored in `Files/`.

## Notes

- Selected `.tif` and `.cbor` fixtures are tracked for clone-based tests and examples; other large inputs remain ignored by Git.
- Config files in `configs/` now point to these `data/` locations.
- Most notebook references were updated to use the same paths, so the assets are easier to locate for BORAS runs.
- These input datasets are not covered by the BORAS software license. No reuse or redistribution rights are granted for them; request separate permission from the copyright holder.
