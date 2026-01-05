# las-filter

Small package to filter and downsample LAS/LAZ point clouds.

Installation (from GitHub branch via pip):

```bash
pip install "git+https://github.com/AlexeyKozhakin/las-filter.git@feature/packaging-cli#egg=las-filter"
```

Basic CLI usage:


- Force final output to ~1M points (random downsampling used when needed):
```
las-filter input.las cleaned.las --downsample 1000000
```

```bash
las-filter INPUT_PATH OUTPUT_PATH --M 100 --K 10 --sigma 2
```

Core API is in the `las_filter` package.

Overview
--------
`las-filter` provides tools to clean LiDAR point clouds (LAS/LAZ):
- remove Z outliers using Z‑score rejection (ZOR)
- perform local surface interpolation and remove points that deviate from the surface
- optionally downsample output to a target number of points

Key parameters (CLI options)
----------------------------
- `--M` — grid size per axis for local surface approximation (creates M×M grid). Default: `100`.
  - Larger `M` → finer surface resolution, higher memory/CPU cost. Typical: 50–300.
- `--K` — number of nearest neighbors used to compute mean height at each grid node. Default: `10`.
  - Small `K` → sensitive to noise; large `K` → more smoothing. Typical: 5–30.
- `--sigma` — sigma multiplier for local filtering. Points with |z - z_pred| > sigma * std are removed. Default: `2.0`.
  - Lower values remove more points (more aggressive).
- `--downsample N` — target number of points to keep after processing. Default: not set (no forced downsample).
  - Current package logic: when using the high-level `full_filter_las` routine it will downsample to `2*N` before filtering if source >> N, run filters, then final downsample to `N` (so filtering is performed on a reduced but still representative subset). Filters themselves can remove extra points — `--downsample` sets a target upper bound rather than the only removal mechanism.

Examples
--------
- Process a single file, keep defaults:
```
las-filter input.las output.las
```
- Process a directory, set local filter and sigma:
```
las-filter /path/to/las_dir /path/to/out_dir --M 150 --K 12 --sigma 2.5
```

Dependencies
------------
- `laspy==2.5.4`
- `numpy==2.2.4`
- `scipy` (used for `cKDTree` and interpolation)
- `PyQt6` (only required if you use the GUI scripts)

Notes & recommendations
-----------------------
- The default parameters are conservative for general LiDAR datasets; tune `--sigma`, `--M`, and `--K` for your sensor/terrain.
- For very large files: prefer running on a machine with enough RAM and/or use `--downsample` to constrain memory use.
- The package exposes `las_filter.core` functions for programmatic use if you need finer control.

# LASTools comands

```
laszip -i L_453_3974.laz L_453_3974.las
```
```
las2las -i L_453_3974.las -o L_453_3974_f.las -keep_every_nth 5
```