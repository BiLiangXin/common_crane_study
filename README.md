# common_crane_study
# Common Crane Migration, Habitat, and ALAN Analysis

![img](data:image/jpeg;base64,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)

This project analyzes GPS tracking data from Common Cranes (*Grus grus*) to identify habitats and stopover sites along migration routes, extract migratory flight corridors, and assess exposure of habitats and migration corridors to artificial light at night (ALAN).

The project consists of two consecutive stages:

1. `st-dbscan/`: Cleans GPS trajectories, identifies nighttime locations, and detects habitats and stopover sites using T-DBSCAN with spatiotemporal constraints.
2. `alan analysis/`: Constructs flight lines from flight points, generates 50%, 75%, and 95% volume corridors using line kernel density estimation (line KDE), overlays the results with NASA Black Marble VNP46A4 nighttime light rasters, and calculates ALAN exposure metrics.

## Project Structure

```text
.
├── data/
│   ├── Common_Crane_Dataset2.csv       # One year of GPS data provided with the project
│   ├── land use and land cover.md      # Dynamic World data download information
│   ├── NASA Black Marble VNP46A4.md    # VNP46A4 data download information
│   └── README.md
├── st-dbscan/
│   ├── run_pipeline.py                 # Main program for GPS cleaning, nighttime detection, and T-DBSCAN
│   ├── config.py                       # Input, output, and analysis parameters
│   ├── preprocessing.py
│   ├── night.py
│   ├── clustering_tdbscan.py
│   ├── site_classification.py
│   ├── io_utils.py
│   └── requirements.txt
├── alan analysis/
│   ├── pipeline.py                     # Main program for migration corridor and ALAN analysis
│   └── requirements.txt
└── README.md
```

## Data

### GPS Tracking Data

`data/Common_Crane_Dataset2.csv` contains GPS tracking data for Common Cranes.

The T-DBSCAN stage requires the following fields:

| Field        | Description                                                  |
| ------------ | ------------------------------------------------------------ |
| `bird_id`    | Individual bird identifier                                   |
| `time`       | GPS timestamp                                                |
| `lon`, `lat` | Longitude and latitude                                       |
| `Available`  | Indicates whether the GPS record is valid; by default, records with the value `Available` are retained |

### External Public Datasets

Download instructions and links for the public datasets are provided in the `data/` directory:

- [Dynamic World land-use and land-cover data](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1): Google Earth Engine dataset `GOOGLE/DYNAMICWORLD/V1`.
- [NASA Black Marble VNP46A4](https://ladsweb.modaps.eosdis.nasa.gov/search/order/2/VNP46A4--5200): NASA LAADS DAAC download page.

The ALAN analysis currently requires a VNP46A4 GeoTIFF matching the study area and analysis year. After downloading the file, provide its path through the `--night-lights` argument. Large external raster files should not be committed directly to the repository.

## Environment Setup

Python 3.9 or later is recommended. Create a virtual environment in the project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install the dependencies for the first stage:

```powershell
python -m pip install -r st-dbscan/requirements.txt
```

Install the dependencies for the second stage:

```powershell
python -m pip install -r "alan analysis/requirements.txt"
```

When using Conda, Linux, or macOS, replace the virtual environment activation command with the appropriate command for your platform.

## Quick Start

### 1. Run T-DBSCAN Habitat Identification

By default, `st-dbscan/config.py` reads input data from `st-dbscan/Common_Crane_Dataset2.csv`. Before the first run, copy the example dataset into that directory:

```powershell
Copy-Item data/Common_Crane_Dataset2.csv st-dbscan/Common_Crane_Dataset2.csv
Set-Location st-dbscan
python run_pipeline.py
```

The program generates results in `st-dbscan/outputs_10000.0/`.

When using your own dataset, make sure that the field names match those listed above, or update the column names and `INPUT_CSV` setting in `config.py`.

### 2. Run Migration Corridor and ALAN Analysis

After downloading the VNP46A4 GeoTIFF, run the second-stage pipeline from the corresponding directory:

```powershell
Set-Location "alan analysis"
python pipeline.py `
  --points "..\st-dbscan\outputs_10000.0\gps_points_with_cluster_10000.0.csv" `
  --night-lights "..\data\VNP46A4_2023_allangle_snowfree_qmask.tif" `
  --output "results"
```

The default settings use a 500 m grid, a 10 km quartic-kernel bandwidth, and 50%, 75%, and 95% volume corridors.

These settings can be adjusted according to the study design:

```powershell
python pipeline.py --help
python pipeline.py --points <points.csv> --night-lights <VNP46A4.tif> --output <output_dir> --cell-size 500 --bandwidth 10000
```

All distance calculations and raster analyses are performed using the Asia North Albers Equal Area Conic projected coordinate system (`ESRI:102025`).

## Main Workflow

### GPS Processing and T-DBSCAN

- Parse timestamps and remove invalid GPS fixes, invalid coordinates, and records with unparseable timestamps.
- Calculate distance, time interval, and movement speed between consecutive points for each individual; by default, points with speeds exceeding 120 km/h are removed.
- Split trajectories into separate segments when the interval between consecutive records exceeds 6 hours.
- Identify nighttime points based on solar elevation, using a default threshold of `-6°`; a fixed-time-window method is also available.
- Perform spatiotemporal clustering using T-DBSCAN, with a default spatial threshold of 10,000 m, a maximum time interval of 6 hours, and a minimum residence duration of 48 hours.
- Classify clusters as breeding sites, wintering sites, key stopover sites, temporary stopover sites, or non-habitat flight trajectories based on residence duration and seasonal timing.

### Migration Corridor and ALAN Analysis

- Construct continuous flight lines from non-habitat GPS points.
- Rasterize flight-line length onto a regular grid and apply quartic kernel density estimation.
- Generate 50%, 75%, and 95% volume corridors based on cumulative density.
- Reproject and align the nighttime light raster with the analysis grid.
- Calculate radiance, light-level proportions, HNLPI, STDHNLPI, PCR, HER, ELS, and other ALAN exposure metrics for habitats and migration corridors.
- Perform Mann–Whitney U tests to compare metrics between key stopover sites and temporary stopover sites.

## Output Files

The main outputs from the first stage are:

| File                            | Description                                                  |
| ------------------------------- | ------------------------------------------------------------ |
| `gps_points_with_cluster_*.csv` | Cleaning results, nighttime attributes, cluster IDs, and event types for each GPS point |
| `flight_points_*.csv`           | GPS points classified as non-habitat flight points for subsequent corridor analysis |
| `sites_all_*.csv`               | Temporal, spatial, and site-type statistics for all detected clusters |
| `sites_*.csv`                   | Filtered results containing wintering sites, breeding sites, and key stopover sites |
| `removed_invalid_points.csv`    | Original GPS points identified as invalid                    |
| `removed_speed_outliers.csv`    | GPS points removed because of unrealistic movement speeds    |

The main outputs from the second stage are:

| File                                                         | Description                                                  |
| ------------------------------------------------------------ | ------------------------------------------------------------ |
| `flight_lines.geojson`                                       | Vector flight-line data                                      |
| `habitat_convex_hulls.geojson`                               | Habitat convex hulls                                         |
| `corridor_50.geojson`, `corridor_75.geojson`, `corridor_95.geojson` | Migration corridors at different volume percentages          |
| `migration_line_kde.tif`                                     | Line KDE raster for migration flights                        |
| `night_lights_albers_500m.tif`                               | Reprojected and aligned nighttime light raster               |
| `habitat_alan_metrics.csv`                                   | Habitat-level ALAN metrics                                   |
| `corridor_alan_metrics.csv`                                  | Corridor-level ALAN metrics                                  |
| `mann_whitney_tests.csv`                                     | Results of between-group statistical tests                   |
| `habitat_type_summary.csv`                                   | Metrics summarized by habitat type                           |
| `fig3_kde_corridors.png`, `fig4_habitat_alan.png`, `fig7_corridor_exposure.png` | Analysis figures                                             |
| `run_metadata.json`                                          | Metadata for the coordinate reference system, grid, bandwidth, and quality-control checks |

## Parameters and Reproducibility

All core parameters for the first stage are defined in `st-dbscan/config.py`, including data-cleaning thresholds, time-zone settings, nighttime detection methods, T-DBSCAN spatial and temporal parameters, and habitat-classification rules.

After parameter values are changed, the spatial threshold is included in the output directory and filenames, making it easier to preserve and compare results from different parameter combinations.

For the second stage, the grid size, KDE bandwidth, input point table, nighttime light raster, and output directory can be configured through command-line arguments.

The parameters used in the final analysis, together with the external raster version and download date, should be documented in the result directory or research records.

## Important Notes

- The GPS dataset contains spatial locations of wild animals. Before publishing or redistributing the complete dataset, comply with the licensing, privacy, and data-sharing requirements of the data provider.
- VNP46A4 is an external dataset. Download permissions, product versions, and quality-mask processing may affect the final results.
- Before running the second stage, the input point table must contain the following columns: `lon`, `lat`, `datetime`, `bird_id`, `segment_id`, `cluster_id`, and `is_habitat`.
- This repository provides analysis code and example data. Numerically identical results are not guaranteed across different versions of Python, GDAL, PROJ, or the external raster datasets.

