from __future__ import annotations

import csv
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from . import orm_models as dbm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = PROJECT_ROOT / "dte_osm_poles.csv"
GEOJSON_PATH = PROJECT_ROOT / "dte_osm_poles.geojson"
DETROIT_CENTER = (42.3314, -83.0458)
DETROIT_BOUNDS = {
    "min_lat": 42.20,
    "max_lat": 42.55,
    "min_lon": -83.35,
    "max_lon": -82.85,
}


def is_detroit_coordinate(lat: float, lon: float) -> bool:
    return (
        DETROIT_BOUNDS["min_lat"] <= lat <= DETROIT_BOUNDS["max_lat"]
        and DETROIT_BOUNDS["min_lon"] <= lon <= DETROIT_BOUNDS["max_lon"]
    )


def _clean(value: str | None) -> str | None:
    value = value.strip() if value else ""
    return value or None


def _float(value: str | int | float | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _height_ft(value: str | None) -> float | None:
    raw = _clean(value)
    if not raw:
        return None
    normalized = raw.lower().replace("feet", "ft").replace("'", " ft")
    number = _float(normalized.split()[0])
    if number is None:
        return None
    return number * 3.28084 if "m" in normalized and "ft" not in normalized else number


def _classification(material: str | None, utility: str | None) -> str:
    material = (material or "").strip().title()
    if material:
        return f"OSM {material} Pole"
    utility = (utility or "").strip().title()
    return f"OSM {utility} Pole" if utility else "OSM Utility Pole"


def _severity(osm_id: str) -> dbm.Severity:
    # The source inventory has location/asset identity but no condition score.
    # Keep most poles low while adding a deterministic spread for visual scanning.
    try:
        value = int(osm_id)
    except ValueError:
        value = sum(ord(char) for char in osm_id)
    if value % 997 == 0:
        return dbm.Severity.HIGH
    if value % 89 == 0:
        return dbm.Severity.MEDIUM
    return dbm.Severity.LOW


def _circuit(osm_id: str, lon: float) -> str:
    bucket = (int(osm_id[-6:] or 0) + int(abs(lon) * 100)) % 64 + 1
    return f"DTE OSM Feeder {bucket:02d}"


def _row_to_pole(row: dict[str, Any]) -> dict[str, Any] | None:
    osm_id = str(row.get("osm_id") or "").strip()
    lat = _float(row.get("lat"))
    lon = _float(row.get("lon"))
    if not osm_id or lat is None or lon is None:
        return None

    material = _clean(row.get("material"))
    operator = _clean(row.get("operator"))
    ref = _clean(row.get("ref"))
    height_ft = _height_ft(row.get("height"))

    return {
        "id": f"OSM-{osm_id}",
        "classification": _classification(material, _clean(row.get("utility"))),
        "severity": _severity(osm_id),
        "address": f"OSM pole {osm_id} ({lat:.5f}, {lon:.5f})",
        "latitude": lat,
        "longitude": lon,
        "height_ft": height_ft,
        "above_grade_ft": round(height_ft * 0.85, 1) if height_ft else None,
        "owner": operator or "DTE Energy / OpenStreetMap",
        "circuit": ref or _circuit(osm_id, lon),
        "sector": "DTE OSM",
        "ai_score": 18 if _severity(osm_id) == dbm.Severity.LOW else 48,
        "ai_confidence": "source inventory only",
        "recommendation": "Imported from DTE OSM pole inventory; inspect when field evidence is available.",
    }


def iter_osm_poles(detroit_only: bool = False) -> Iterator[dict[str, Any]]:
    if CSV_PATH.exists():
        with CSV_PATH.open(newline="", encoding="utf-8") as file:
            for row in csv.DictReader(file):
                pole = _row_to_pole(row)
                if pole and (
                    not detroit_only or is_detroit_coordinate(pole["latitude"], pole["longitude"])
                ):
                    yield pole
        return

    if not GEOJSON_PATH.exists():
        return

    with GEOJSON_PATH.open(encoding="utf-8") as file:
        data = json.load(file)
    for feature in data.get("features", []):
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []
        properties = feature.get("properties") or {}
        if geometry.get("type") != "Point" or len(coordinates) < 2:
            continue
        row = {
            **properties,
            "lon": coordinates[0],
            "lat": coordinates[1],
        }
        pole = _row_to_pole(row)
        if pole and (
            not detroit_only or is_detroit_coordinate(pole["latitude"], pole["longitude"])
        ):
            yield pole
