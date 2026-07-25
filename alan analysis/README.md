# Flight corridor and nighttime-light analysis

This folder paper Sections 3.3-3.5 of the manuscript. All metric
operations use **Asia North Albers Equal Area Conic (ESRI:102025)**.

Run from the project root:

```powershell
python -m flight_and_night.pipeline
```

Defaults settings: 500 m cells, 10 km quartic
line-kernel bandwidth, 50/75/95% volume corridors, and the 2023 VNP46A4
raster in the project root. Inputs and output locations can be overridden:

```powershell
python -m flight_and_night.pipeline --points outputs/gps_points_with_cluster.csv `
  --night-lights VNP46A4_2023_allangle_snowfree_qmask.tif `
  --output flight_and_night/results
```

The output contains projected KDE and night-light rasters, flight lines,
habitat convex hulls, nested corridor polygons, site/corridor ALAN metrics,
Mann-Whitney tests, summaries, figures, and run metadata.

The site table reports the five radiance-class areas and proportions plus
HNLPI, STDHNLPI, PCR, HER, and ELS. 

