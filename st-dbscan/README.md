# Common Crane Habitat Identification and Nighttime Light Exposure Quantification (T-DBSCAN)

This project is designed to:

- Clean Common Crane (*Grus grus*) GPS tracking data, including missing values, outliers, and abnormal movement speeds
- Identify nighttime GPS points, with the option to use only nighttime points for clustering
- Identify habitats and stopover sites using T-DBSCAN, a spatiotemporal clustering method based on minimum residence duration
- Generate the following outputs:
  - **Point-level table:** Includes `cluster_id`, `is_habitat`, and `event_type` for each GPS point
  - **Site-level table:** Includes statistics for each site, such as start time, end time, duration in days, mean center coordinates, and site type
  - **Flight-point table:** Can be used for kernel density estimation, contour generation, and corridor probability surface analysis

## How to Run

1. Place your CSV file in the project root directory and update `INPUT_CSV` in `config.py`.

2. Install the required dependencies. Python 3.9 or later is recommended:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the pipeline:

   ```bash
   python run_pipeline.py
   ```

The generated files will be saved in the `outputs/` directory.

## Key Parameters

All parameters are configured in `config.py`:

- `MAX_SPEED_KMH`: Threshold for detecting abnormal movement speeds
- `SEGMENT_GAP_HOURS`: Time-gap threshold used to split trajectories into segments
- `NIGHT_METHOD` and `NIGHT_SUN_ELEV_THRESHOLD_DEG`: Parameters used to determine whether a GPS point was recorded at night
- `TDBSCAN_EPS_METERS`, `TDBSCAN_MAX_INTERVAL_HOURS`, and `TDBSCAN_MIN_STAY_HOURS`: Core T-DBSCAN parameters
- `KEY_STOP_DAYS=14` and `MIN_STOP_DAYS=2`: Thresholds used to classify stopover-site importance

## Output Files

- `gps_points_with_cluster.csv`
- `flight_points.csv`
- `sites_all.csv`
- `sites.csv` — includes only wintering sites, breeding sites, and key stopover sites
