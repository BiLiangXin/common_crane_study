"""Paper-aligned migration corridor and ALAN exposure pipeline.

All metric operations use Asia North Albers Equal Area Conic (ESRI:102025).
"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

from pyproj import CRS, datadir

# Some Windows/Conda combinations do not expose PROJ's database to GDAL.
os.environ.setdefault("PROJ_LIB", datadir.get_data_dir())
os.environ.setdefault("PROJ_DATA", datadir.get_data_dir())

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib.colors import LogNorm
from rasterio.enums import Resampling
from rasterio.features import geometry_mask, shapes
from rasterio.transform import from_origin
from rasterio.warp import reproject
from scipy.signal import fftconvolve
from scipy.stats import mannwhitneyu
from shapely.geometry import LineString, Polygon, shape

WORK_CRS = CRS.from_user_input("ESRI:102025")
WGS84 = CRS.from_epsg(4326)
LIGHT_BINS = np.array([0.0, 0.5, 1.0, 5.0, 10.0, np.inf])
LIGHT_LABELS = ["0-0.5", "0.5-1", "1-5", "5-10", ">10"]
LIGHT_SCORES = np.arange(5, dtype=float)


def read_points(path: Path) -> gpd.GeoDataFrame:
    df = pd.read_csv(path, low_memory=False)
    required = {"lon", "lat", "segment_id", "cluster_id", "is_habitat"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns in {path}: {sorted(missing)}")
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df["is_habitat"] = df["is_habitat"].astype(str).str.lower().eq("true")
    return gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.lon, df.lat), crs=WGS84
    ).to_crs(WORK_CRS)


def build_flight_lines(points: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    flight = points.loc[~points.is_habitat].sort_values(
        ["bird_id", "segment_id", "datetime"]
    )
    records = []
    for (_, segment_id), group in flight.groupby(["bird_id", "segment_id"]):
        group = group.sort_values("datetime")
        rows = list(group.itertuples())
        for left, right in zip(rows, rows[1:]):
            gap_h = (right.datetime - left.datetime).total_seconds() / 3600
            if 0 < gap_h <= 6:
                line = LineString([left.geometry, right.geometry])
                if line.length > 0:
                    records.append({"segment_id": segment_id, "gap_h": gap_h, "geometry": line})
    if not records:
        raise ValueError("No consecutive flight lines could be constructed")
    return gpd.GeoDataFrame(records, crs=WORK_CRS)


def grid_for_lines(lines: gpd.GeoDataFrame, cell_size: float, bandwidth: float):
    xmin, ymin, xmax, ymax = lines.total_bounds
    xmin = math.floor((xmin - bandwidth) / cell_size) * cell_size
    ymin = math.floor((ymin - bandwidth) / cell_size) * cell_size
    xmax = math.ceil((xmax + bandwidth) / cell_size) * cell_size
    ymax = math.ceil((ymax + bandwidth) / cell_size) * cell_size
    width = int(round((xmax - xmin) / cell_size))
    height = int(round((ymax - ymin) / cell_size))
    return from_origin(xmin, ymax, cell_size, cell_size), width, height


def rasterize_line_lengths(lines, transform, width, height, cell_size):
    """Approximate the line integral using regular along-line quadrature."""
    out = np.zeros((height, width), dtype=np.float32)
    xmin, ymax = transform.c, transform.f
    for geom in lines.geometry:
        n = max(1, int(math.ceil(geom.length / (cell_size / 2))))
        step = geom.length / n
        for index in range(n):
            point = geom.interpolate((index + 0.5) * step)
            col = int((point.x - xmin) // cell_size)
            row = int((ymax - point.y) // cell_size)
            if 0 <= row < height and 0 <= col < width:
                out[row, col] += step
    return out


def quartic_kernel(cell_size: float, bandwidth: float) -> np.ndarray:
    radius = int(math.ceil(bandwidth / cell_size))
    offsets = np.arange(-radius, radius + 1) * cell_size
    xx, yy = np.meshgrid(offsets, offsets)
    u = np.hypot(xx, yy) / bandwidth
    kernel = np.zeros_like(u, dtype=np.float64)
    inside = u < 1
    kernel[inside] = (3.0 / np.pi) * (1.0 - u[inside] ** 2) ** 2 / bandwidth**2
    return kernel


def line_kde(lines, transform, width, height, cell_size, bandwidth):
    lengths = rasterize_line_lengths(lines, transform, width, height, cell_size)
    density = fftconvolve(lengths, quartic_kernel(cell_size, bandwidth), mode="same")
    density[density < np.finfo(np.float32).eps] = 0
    return density.astype(np.float32)


def volume_masks(density: np.ndarray, percentiles=(50, 75, 95)):
    values = density[density > 0]
    order = np.sort(values)[::-1]
    cumulative = np.cumsum(order, dtype=np.float64)
    total = cumulative[-1]
    masks, thresholds = {}, {}
    for p in percentiles:
        idx = min(np.searchsorted(cumulative, total * p / 100.0), len(order) - 1)
        threshold = float(order[idx])
        thresholds[p] = threshold
        masks[p] = density >= threshold
    return masks, thresholds


def mask_polygons(mask, transform, crs, percentile):
    geoms = [shape(g) for g, value in shapes(mask.astype("uint8"), mask=mask, transform=transform) if value == 1]
    return gpd.GeoDataFrame({"percentile": percentile, "geometry": geoms}, crs=crs)


def habitat_polygons(points: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    habitat = points.loc[points.is_habitat & (points.cluster_id >= 0)].copy()
    records = []
    for cluster_id, group in habitat.groupby("cluster_id"):
        geom = group.geometry.union_all().convex_hull
        if geom.geom_type != "Polygon" or geom.area == 0:
            geom = geom.buffer(250)
        records.append({
            "site_id": int(cluster_id),
            "event_type": group.event_type.mode().iat[0] if "event_type" in group else "",
            "n_points": len(group),
            "start_time": group.datetime.min(),
            "end_time": group.datetime.max(),
            "duration_days": (group.datetime.max() - group.datetime.min()).total_seconds() / 86400,
            "geometry": geom,
        })
    return gpd.GeoDataFrame(records, crs=WORK_CRS)


def align_night_lights(path, transform, width, height):
    dst = np.full((height, width), np.nan, dtype=np.float32)
    with rasterio.open(path) as src:
        source = src.read(1)
        source = np.where(source == src.nodata, np.nan, source)
        reproject(
            source=source,
            destination=dst,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=np.nan,
            dst_transform=transform,
            dst_crs=WORK_CRS,
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )
    dst[dst < 0] = 0
    return dst


def raster_values_in_geometry(array, geom, transform):
    inside = geometry_mask([geom], array.shape, transform, invert=True, all_touched=False)
    return array[inside & np.isfinite(array)]


def habitat_exposure(habitats, radiance, transform, cell_area):
    rows = []
    for site in habitats.itertuples():
        values = raster_values_in_geometry(radiance, site.geometry, transform)
        if not values.size:
            continue
        classes = np.digitize(values, LIGHT_BINS[1:-1], right=False)
        counts = np.bincount(classes, minlength=5).astype(float)
        proportions = counts / counts.sum()
        hnlpi = float(np.dot(LIGHT_SCORES, proportions))
        pcr = float(proportions[1:].sum())
        her = float(proportions[3:].sum())
        els = float(np.dot(LIGHT_SCORES[1:], counts[1:]) / (4 * counts[1:].sum())) if counts[1:].sum() else 0.0
        row = {
            "site_id": site.site_id, "event_type": site.event_type,
            "area_km2": site.geometry.area / 1e6,
            "rasterized_valid_area_km2": counts.sum() * cell_area / 1e6,
            "mean_radiance": float(np.mean(values)), "median_radiance": float(np.median(values)),
            "p75": float(np.percentile(values, 75)), "p90": float(np.percentile(values, 90)),
            "p95": float(np.percentile(values, 95)), "HNLPI": hnlpi,
            "STDHNLPI": hnlpi / 4, "PCR": pcr, "HER": her, "ELS": els,
        }
        for label, count, prop in zip(LIGHT_LABELS, counts, proportions):
            row[f"area_{label}_km2"] = count * cell_area / 1e6
            row[f"prop_{label}"] = prop
        rows.append(row)
    return pd.DataFrame(rows)


def corridor_exposure(masks, density, radiance, cell_area):
    rows = []
    for p, mask in masks.items():
        valid = mask & np.isfinite(radiance) & (density > 0)
        weights = density[valid].astype(np.float64) * cell_area
        ce = np.average(radiance[valid], weights=weights) if weights.size else np.nan
        rows.append({"corridor_percentile": p, "area_km2": mask.sum() * cell_area / 1e6,
                     "valid_light_area_km2": valid.sum() * cell_area / 1e6,
                     "CE_q": ce, "captured_volume": density[mask].sum() / density.sum()})
    result = pd.DataFrame(rows).sort_values("corridor_percentile")
    base_area, base_ce = result.iloc[0][["area_km2", "CE_q"]]
    result["relative_area_change_pct"] = (result.area_km2 / base_area - 1) * 100
    result["relative_exposure_change_pct"] = (result.CE_q / base_ce - 1) * 100
    return result


def statistical_tests(site_metrics):
    metrics = ["PCR", "STDHNLPI", "ELS", "mean_radiance", "p90", "HER"]
    key = site_metrics[site_metrics.event_type == "关键停留地"]
    temporary = site_metrics[site_metrics.event_type == "临时停留地"]
    rows = []
    for metric in metrics:
        if len(key) and len(temporary):
            test = mannwhitneyu(key[metric], temporary[metric], alternative="two-sided")
            rows.append({"metric": metric, "key_n": len(key), "temporary_n": len(temporary),
                         "U": test.statistic, "p_value": test.pvalue})
    return pd.DataFrame(rows)


def write_raster(path, array, transform, nodata=-9999.0):
    data = np.where(np.isfinite(array), array, nodata).astype("float32")
    with rasterio.open(path, "w", driver="GTiff", height=data.shape[0], width=data.shape[1],
                       count=1, dtype="float32", crs=WORK_CRS, transform=transform,
                       nodata=nodata, compress="deflate", tiled=True, BIGTIFF="IF_SAFER") as dst:
        dst.write(data, 1)


def make_figures(output, density, radiance, transform, masks, habitats, corridor_metrics=None):
    extent = [transform.c, transform.c + density.shape[1] * transform.a,
              transform.f + density.shape[0] * transform.e, transform.f]
    fig, ax = plt.subplots(figsize=(9, 9), constrained_layout=True)
    shown = np.ma.masked_less_equal(density, 0)
    im = ax.imshow(shown, extent=extent, cmap="YlOrRd", norm=LogNorm(), origin="upper")
    colors = {95: "#2b8cbe", 75: "#7b3294", 50: "#d7191c"}
    for p in (95, 75, 50):
        ax.contour(masks[p], levels=[0.5], colors=[colors[p]], linewidths=1.2,
                   extent=extent, origin="upper")
    habitats.boundary.plot(ax=ax, color="black", linewidth=0.6)
    ax.set_title("Migration intensity and volume-percentile corridors")
    ax.set_xlabel("Easting (m), Asia North Albers Equal Area Conic")
    ax.set_ylabel("Northing (m)")
    fig.colorbar(im, ax=ax, label="Line KDE intensity")
    fig.savefig(output / "fig3_kde_corridors.png", dpi=240)
    plt.close(fig)
    if radiance is not None:
        fig, ax = plt.subplots(figsize=(9, 9), constrained_layout=True)
        im = ax.imshow(np.ma.masked_invalid(radiance), extent=extent, cmap="magma", origin="upper", vmin=0, vmax=5)
        habitats.boundary.plot(ax=ax, color="#00ffff", linewidth=0.8)
        ax.set_title("Habitat-use units and 2023 nighttime radiance")
        fig.colorbar(im, ax=ax, label="nW cm$^{-2}$ sr$^{-1}$")
        fig.savefig(output / "fig4_habitat_alan.png", dpi=240)
        plt.close(fig)
    if corridor_metrics is not None:
        fig, ax = plt.subplots(figsize=(6, 4), constrained_layout=True)
        ax.plot(corridor_metrics.corridor_percentile, corridor_metrics.CE_q, marker="o", color="#c51b7d")
        ax.set(xlabel="Corridor volume percentile (%)", ylabel="Expected ALAN exposure (CEq)")
        ax.grid(alpha=0.25)
        fig.savefig(output / "fig7_corridor_exposure.png", dpi=240)
        plt.close(fig)


def run(args):
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    points = read_points(Path(args.points))
    lines = build_flight_lines(points)
    habitats = habitat_polygons(points)
    transform, width, height = grid_for_lines(lines, args.cell_size, args.bandwidth)
    density = line_kde(lines, transform, width, height, args.cell_size, args.bandwidth)
    masks, thresholds = volume_masks(density)
    cell_area = args.cell_size**2

    lines.to_file(output / "flight_lines.geojson", driver="GeoJSON")
    habitats.to_file(output / "habitat_convex_hulls.geojson", driver="GeoJSON")
    for p, mask in masks.items():
        mask_polygons(mask, transform, WORK_CRS, p).to_file(output / f"corridor_{p}.geojson", driver="GeoJSON")
    write_raster(output / "migration_line_kde.tif", density, transform)
    pd.DataFrame([{"corridor_percentile": p, "density_threshold": thresholds[p],
                   "area_km2": masks[p].sum() * cell_area / 1e6,
                   "captured_volume": density[masks[p]].sum() / density.sum()} for p in masks]).to_csv(
                       output / "corridor_summary.csv", index=False)

    radiance = None
    corridor_metrics = None
    if args.night_lights:
        radiance = align_night_lights(Path(args.night_lights), transform, width, height)
        write_raster(output / "night_lights_albers_500m.tif", radiance, transform)
        site_metrics = habitat_exposure(habitats, radiance, transform, cell_area)
        site_metrics.to_csv(output / "habitat_alan_metrics.csv", index=False)
        corridor_metrics = corridor_exposure(masks, density, radiance, cell_area)
        corridor_metrics.to_csv(output / "corridor_alan_metrics.csv", index=False)
        statistical_tests(site_metrics).to_csv(output / "mann_whitney_tests.csv", index=False)
        site_metrics.groupby("event_type", as_index=False).mean(numeric_only=True).to_csv(
            output / "habitat_type_summary.csv", index=False)
    make_figures(output, density, radiance, transform, masks, habitats, corridor_metrics)
    metadata = {"work_crs": WORK_CRS.to_string(), "work_crs_name": WORK_CRS.name,
                "cell_size_m": args.cell_size, "bandwidth_m": args.bandwidth,
                "grid_width": width, "grid_height": height, "flight_line_count": len(lines),
                "habitat_count": len(habitats), "night_lights": args.night_lights}
    metadata["quality_checks"] = {
        "density_is_finite_and_nonnegative": bool(np.isfinite(density).all() and (density >= 0).all()),
        "corridors_are_nested": bool(
            np.all(~masks[50] | masks[75]) and np.all(~masks[75] | masks[95])
        ),
        "volume_tolerance_max": float(max(abs(density[masks[p]].sum() / density.sum() - p / 100) for p in masks)),
    }
    if corridor_metrics is not None:
        metadata["quality_checks"]["corridor_exposure_is_finite"] = bool(
            np.isfinite(corridor_metrics.CE_q).all()
        )
    (output / "run_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--points", default="outputs/gps_points_with_cluster.csv")
    p.add_argument("--night-lights", default="VNP46A4_2023_allangle_snowfree_qmask.tif")
    p.add_argument("--output", default="flight_and_night/results")
    p.add_argument("--cell-size", type=float, default=500.0)
    p.add_argument("--bandwidth", type=float, default=10000.0)
    return p


if __name__ == "__main__":
    run(parser().parse_args())
