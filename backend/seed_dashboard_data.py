from __future__ import annotations

import math
from datetime import datetime

from sqlalchemy import delete, select

from . import orm_models as dbm
from .database import SessionLocal
from .osm_pole_data import CSV_PATH, GEOJSON_PATH, iter_osm_poles


USERS = [
    {"id": "user-001", "initials": "ZM", "name": "Z. Metiva", "role": "Field ops lead"},
    {"id": "tech-jc", "initials": "JC", "name": "J. Chen", "role": "Field tech"},
    {"id": "tech-dk", "initials": "DK", "name": "D. Kim", "role": "Field tech"},
    {"id": "tech-as", "initials": "AS", "name": "A. Singh", "role": "Field tech"},
    {"id": "tech-mr", "initials": "MR", "name": "M. Reyes", "role": "Field tech"},
    {"id": "tech-tb", "initials": "TB", "name": "T. Brown", "role": "Field tech"},
    {"id": "tech-lw", "initials": "LW", "name": "L. Williams", "role": "Field tech"},
    {"id": "tech-ng", "initials": "NG", "name": "N. Garcia", "role": "Field tech"},
    {"id": "tech-ho", "initials": "HO", "name": "H. Ortiz", "role": "Field tech"},
    {"id": "user-rp", "initials": "RP", "name": "R. Patel", "role": "Crew coordinator"},
    {"id": "user-jl", "initials": "JL", "name": "J. Liu", "role": "Safety reviewer"},
]

# ---------------------------------------------------------------------------
# DETAILED_POLE_TARGETS
# Each entry locates the nearest real OSM pole in the DB, applies rich
# metadata to it, and seeds the associated report, photos, and history events.
# ---------------------------------------------------------------------------
DETAILED_POLE_TARGETS = [
    {
        # Corktown — Michigan Ave & Trumbull Ave
        "target_lat": 42.3321,
        "target_lon": -83.0478,
        "classification": "Class 3 Southern Pine",
        "severity": dbm.Severity.CRITICAL,
        "height_ft": 45,
        "above_grade_ft": 38,
        "owner": "DTE Energy - Joint use with Comcast",
        "circuit": "Feeder F-407 - 13.2 kV",
        "lean_degrees": 12.4,
        "lean_status": "spec <= 5 degrees",
        "ai_score": 94,
        "ai_confidence": "high confidence",
        "recommendation": "Replace within 7 days",
        "report": {
            "id": "RPT-D01",
            "title": "Lean exceeds 12 degrees, crossarm rot",
            "severity": dbm.Severity.CRITICAL,
            "user_id": "tech-jc",
            "submitted_at": "2026-05-14T11:48:00",
            "location": "Michigan Ave & Trumbull Ave",
        },
        "photos": [
            ("photo-1", "01 - Overview, west", dbm.Severity.CRITICAL, "12 degree lean"),
            ("photo-2", "02 - Crossarm closeup", dbm.Severity.CRITICAL, "Rot"),
            ("photo-3", "03 - Transformer base", dbm.Severity.MEDIUM, "Oil staining"),
        ],
        "history_extra": [
            {
                "id": "evt-d01-c1",
                "type": dbm.HistoryEventType.COMMENT,
                "title": "R. Patel - Comment on report UP-2026-04891",
                "event_date": "2026-05-14T15:42:00",
                "author_user_id": "user-rp",
                "comment": "Crew 14 dispatched for tomorrow 7 AM. Bringing a 45 ft Class 3 replacement and the lift truck. Traffic permit cleared with the city.",
                "pin_color": "#475569",
            },
            {
                "id": "evt-d01-c2",
                "type": dbm.HistoryEventType.COMMENT,
                "title": "J. Liu - Comment on report UP-2026-04891",
                "event_date": "2026-05-14T13:08:00",
                "author_user_id": "user-jl",
                "comment": "De-energize feeder F-407 before approach. Comcast fiber attached at 23 ft, coordinate with their NOC ticket 88421.",
                "pin_color": "#475569",
            },
            {
                "id": "evt-d01-i1",
                "type": dbm.HistoryEventType.INSPECTION,
                "title": "Routine inspection - drone",
                "event_date": "2025-11-02",
                "description": "Last manual check. Minor lean noted (4.8 degrees). Vegetation trimmed.",
                "pin_color": "#FBBF24",
            },
            {
                "id": "evt-d01-u1",
                "type": dbm.HistoryEventType.UPGRADE,
                "title": "Hardware upgrade",
                "event_date": "2022-08-19",
                "description": "Transformer swapped from 25 kVA to 50 kVA. Polymer insulators installed.",
                "pin_color": "#60A5FA",
            },
            {
                "id": "evt-d01-j1",
                "type": dbm.HistoryEventType.JOINT_USE,
                "title": "Joint use added",
                "event_date": "2019-03-04",
                "description": "Comcast fiber attachment permitted at 23 ft above grade.",
                "pin_color": "#60A5FA",
            },
            {
                "id": "evt-d01-t1",
                "type": dbm.HistoryEventType.TREATMENT,
                "title": "Treatment cycle",
                "event_date": "2014-06-12",
                "description": "CCA pressure-treatment refresh. Estimated remaining life 22 years.",
                "pin_color": "#10B981",
            },
            {
                "id": "evt-d01-in1",
                "type": dbm.HistoryEventType.INSTALL,
                "title": "Pole installed",
                "event_date": "2008-04-27",
                "description": "Class 3 Southern Pine, 45 ft. Original contractor Quanta Services.",
                "pin_color": "#6B7280",
            },
        ],
    },
    {
        # Corktown — W. Vernor Hwy & Rosa Parks Blvd
        "target_lat": 42.3298,
        "target_lon": -83.0456,
        "classification": "Class 2 Southern Pine",
        "severity": dbm.Severity.CRITICAL,
        "height_ft": 40,
        "above_grade_ft": 34,
        "owner": "DTE Energy",
        "circuit": "Feeder F-312 - 13.2 kV",
        "ai_score": 88,
        "ai_confidence": "high confidence",
        "recommendation": "Dispatch hazmat and replace transformer",
        "report": {
            "id": "RPT-D02",
            "title": "Transformer leak, oil stains",
            "severity": dbm.Severity.CRITICAL,
            "user_id": "tech-dk",
            "submitted_at": "2026-05-14T08:30:00",
            "location": "W. Vernor Hwy & Rosa Parks Blvd",
        },
        "photos": [
            ("photo-4", "01 - Overview, north", dbm.Severity.CRITICAL, "Oil leak"),
            ("photo-5", "02 - Transformer base", dbm.Severity.CRITICAL, "Staining"),
        ],
        "history_extra": [
            {
                "id": "evt-d02-in1",
                "type": dbm.HistoryEventType.INSTALL,
                "title": "Pole installed",
                "event_date": None,
                "pin_color": "#6B7280",
            },
        ],
    },
    {
        # Corktown — W. Willis St & 13th St
        "target_lat": 42.3339,
        "target_lon": -83.0462,
        "classification": "Class 3 Southern Pine",
        "severity": dbm.Severity.HIGH,
        "height_ft": 45,
        "above_grade_ft": 37,
        "owner": "DTE Energy",
        "circuit": "Feeder F-501 - 13.2 kV",
        "ai_score": 76,
        "ai_confidence": "medium confidence",
        "recommendation": "Inspect and treat within 30 days",
        "report": {
            "id": "RPT-D03",
            "title": "Woodpecker damage, upper third",
            "severity": dbm.Severity.HIGH,
            "user_id": "tech-as",
            "submitted_at": "2026-05-13T09:15:00",
            "location": "W. Willis St & 13th St",
        },
        "photos": [],
        "history_extra": [],
    },
    {
        # Corktown — Michigan Ave & 15th St
        "target_lat": 42.3315,
        "target_lon": -83.0510,
        "classification": "Class 4 Southern Pine",
        "severity": dbm.Severity.HIGH,
        "height_ft": 35,
        "above_grade_ft": 28,
        "owner": "DTE Energy",
        "circuit": "Feeder F-407 - 13.2 kV",
        "ai_score": 71,
        "ai_confidence": "medium confidence",
        "recommendation": "Replace insulator within 30 days",
        "report": {
            "id": "RPT-D04",
            "title": "Insulator cracked, phase B",
            "severity": dbm.Severity.HIGH,
            "user_id": "tech-mr",
            "submitted_at": "2026-05-13T14:22:00",
            "location": "Michigan Ave & 15th St",
        },
        "photos": [],
        "history_extra": [],
    },
    {
        # Corktown — Temple St & Trumbull Ave
        "target_lat": 42.3352,
        "target_lon": -83.0481,
        "classification": "Class 3 Southern Pine",
        "severity": dbm.Severity.MEDIUM,
        "height_ft": 45,
        "above_grade_ft": 38,
        "owner": "DTE Energy",
        "circuit": "Feeder F-501 - 13.2 kV",
        "ai_score": 54,
        "ai_confidence": "medium confidence",
        "recommendation": "Schedule vegetation trim within 90 days",
        "report": {
            "id": "RPT-D05",
            "title": "Vegetation contact, secondary",
            "severity": dbm.Severity.MEDIUM,
            "user_id": "tech-tb",
            "submitted_at": "2026-05-12T16:05:00",
            "location": "Temple St & Trumbull Ave",
        },
        "photos": [],
        "history_extra": [],
    },
    {
        # Corktown — W. Grand Blvd & 14th St
        "target_lat": 42.3374,
        "target_lon": -83.0498,
        "classification": "Class 3 Steel",
        "severity": dbm.Severity.MEDIUM,
        "height_ft": 50,
        "above_grade_ft": 43,
        "owner": "DTE Energy",
        "circuit": "Feeder F-312 - 13.2 kV",
        "ai_score": 58,
        "ai_confidence": "medium confidence",
        "recommendation": "Re-tension guy wire within 90 days",
        "report": {
            "id": "RPT-D06",
            "title": "Guy wire tension below spec",
            "severity": dbm.Severity.MEDIUM,
            "user_id": "tech-lw",
            "submitted_at": "2026-05-11T10:44:00",
            "location": "W. Grand Blvd & 14th St",
        },
        "photos": [],
        "history_extra": [],
    },
    {
        # Downtown — Woodward Ave & Campus Martius
        "target_lat": 42.3314,
        "target_lon": -83.0458,
        "severity": dbm.Severity.LOW,
        "report": {
            "id": "RPT-D07",
            "title": "Low priority surface weathering",
            "severity": dbm.Severity.LOW,
            "user_id": "tech-ng",
            "submitted_at": "2026-05-10T13:20:00",
            "location": "Woodward Ave & Campus Martius",
        },
        "photos": [],
        "history_extra": [],
    },
    {
        # Eastern Market — Russell St & Adelaide St
        "target_lat": 42.3482,
        "target_lon": -83.0418,
        "severity": dbm.Severity.LOW,
        "report": {
            "id": "RPT-D08",
            "title": "Faded pole tag, routine re-stencil",
            "severity": dbm.Severity.LOW,
            "user_id": "tech-ho",
            "submitted_at": "2026-05-10T09:05:00",
            "location": "Russell St & Adelaide St",
        },
        "photos": [],
        "history_extra": [],
    },
]

# ---------------------------------------------------------------------------
# MAP_ONLY_TARGETS
# Find the nearest OSM pole to each location and apply minimal metadata so
# these poles appear across the map without seeding full report data.
# ---------------------------------------------------------------------------
MAP_ONLY_TARGETS = [
    {"target_lat": 42.3379, "target_lon": -83.0188, "severity": dbm.Severity.MEDIUM, "neighborhood": "Rivertown"},
    {"target_lat": 42.3671, "target_lon": -83.0752, "severity": dbm.Severity.LOW, "neighborhood": "New Center"},
    {"target_lat": 42.3795, "target_lon": -83.0966, "severity": dbm.Severity.LOW, "neighborhood": "Boston-Edison"},
    {"target_lat": 42.3003, "target_lon": -83.1032, "severity": dbm.Severity.LOW, "neighborhood": "Southwest Detroit"},
    {"target_lat": 42.4027, "target_lon": -82.9348, "severity": dbm.Severity.LOW, "neighborhood": "East English Village"},
    {"target_lat": 42.3517, "target_lon": -83.0601, "severity": dbm.Severity.LOW, "neighborhood": "Midtown"},
    {"target_lat": 42.3209, "target_lon": -83.0792, "severity": dbm.Severity.LOW, "neighborhood": "Mexicantown"},
]

DETROIT_PLACES = [
    ("Downtown", "Woodward Ave & Campus Martius", 42.3314, -83.0458, "DTE Downtown Network - 13.2 kV"),
    ("Corktown", "Michigan Ave & Trumbull Ave", 42.3319, -83.0479, "DTE Corktown 407 - 13.2 kV"),
    ("Mexicantown", "W. Vernor Hwy & Bagley St", 42.3209, -83.0792, "DTE Vernor 312 - 13.2 kV"),
    ("Midtown", "Woodward Ave & W. Willis St", 42.3517, -83.0601, "DTE Midtown 501 - 13.2 kV"),
    ("New Center", "W. Grand Blvd & Woodward Ave", 42.3671, -83.0752, "DTE New Center 622 - 13.2 kV"),
    ("Eastern Market", "Russell St & Adelaide St", 42.3482, -83.0418, "DTE Eastern Market 214 - 13.2 kV"),
    ("Rivertown", "Jefferson Ave & Chene St", 42.3379, -83.0188, "DTE Rivertown 118 - 13.2 kV"),
    ("Southwest Detroit", "Fort St & Livernois Ave", 42.3003, -83.1032, "DTE Southwest 730 - 13.2 kV"),
    ("Boston-Edison", "Chicago Blvd & 2nd Ave", 42.3795, -83.0966, "DTE Boston Edison 455 - 13.2 kV"),
    ("East English Village", "E. Warren Ave & Cadieux Rd", 42.4027, -82.9348, "DTE East English 884 - 13.2 kV"),
    ("Palmer Woods", "Seven Mile Rd & Woodward Ave", 42.4311, -83.1242, "DTE Palmer Park 761 - 13.2 kV"),
    ("Grandmont Rosedale", "Grand River Ave & Evergreen Rd", 42.3918, -83.2350, "DTE Grandmont 690 - 13.2 kV"),
    ("North End", "Oakland Ave & Holbrook Ave", 42.3788, -83.0655, "DTE North End 338 - 13.2 kV"),
    ("Jefferson Chalmers", "Jefferson Ave & Chalmers St", 42.3708, -82.9402, "DTE Jefferson 920 - 13.2 kV"),
]

OSM_REPORT_TEMPLATES = [
    ("RPT-OSM-001", "Crossarm hardware flagged from street-level sweep", dbm.Severity.CRITICAL, "tech-jc", "2026-05-16T15:40:00"),
    ("RPT-OSM-002", "Vegetation encroachment near primary conductor", dbm.Severity.HIGH, "tech-as", "2026-05-16T14:25:00"),
    ("RPT-OSM-003", "Pole tag missing, confirm asset identity", dbm.Severity.MEDIUM, "tech-tb", "2026-05-16T13:05:00"),
    ("RPT-OSM-004", "Guy attachment requires field verification", dbm.Severity.HIGH, "tech-mr", "2026-05-16T12:35:00"),
    ("RPT-OSM-005", "Leaning pole candidate from OSM corridor pass", dbm.Severity.CRITICAL, "tech-dk", "2026-05-16T11:20:00"),
    ("RPT-OSM-006", "Low priority weathering, monitor on next patrol", dbm.Severity.LOW, "tech-ng", "2026-05-16T10:10:00"),
    ("RPT-OSM-007", "Transformer clearance review needed", dbm.Severity.HIGH, "tech-lw", "2026-05-16T09:30:00"),
    ("RPT-OSM-008", "Routine OSM inventory validation", dbm.Severity.MEDIUM, "tech-ho", "2026-05-16T08:55:00"),
]

_SEV_PIN_COLOR: dict[dbm.Severity, str] = {
    dbm.Severity.CRITICAL: "#EF4444",
    dbm.Severity.HIGH: "#F97316",
    dbm.Severity.MEDIUM: "#FBBF24",
    dbm.Severity.LOW: "#10B981",
}


def _parse_dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _upsert(db, model, key: str, values: dict) -> None:
    row = db.get(model, key)
    if row is None:
        db.add(model(**values))
        return
    for field, value in values.items():
        setattr(row, field, value)


def _nearest_detroit_place(lat: float, lon: float) -> tuple[str, str, str]:
    neighborhood, intersection, _place_lat, _place_lon, circuit = min(
        DETROIT_PLACES,
        key=lambda place: (lat - place[2]) ** 2 + (lon - place[3]) ** 2,
    )
    return neighborhood, intersection, circuit


def _location_label(pole: dict) -> str:
    neighborhood, intersection, _circuit = _nearest_detroit_place(pole["latitude"], pole["longitude"])
    return f"{intersection}, {neighborhood}, Detroit"


def _nearest_osm_pole(db, lat: float, lon: float, exclude_ids: set[str]) -> dbm.Pole | None:
    """Return the closest OSM pole from the DB that is not already claimed."""
    cos_lat = math.cos(math.radians(lat))
    stmt = select(dbm.Pole).where(dbm.Pole.id.like("OSM-%"))
    if exclude_ids:
        stmt = stmt.where(dbm.Pole.id.notin_(exclude_ids))
    stmt = stmt.order_by(
        (dbm.Pole.latitude - lat) * (dbm.Pole.latitude - lat)
        + (dbm.Pole.longitude - lon) * (dbm.Pole.longitude - lon) * cos_lat * cos_lat
    ).limit(1)
    return db.scalars(stmt).first()


def _apply_pole_metadata(pole: dbm.Pole, target: dict) -> None:
    """Write rich metadata fields from a target dict onto an ORM Pole row."""
    for field in (
        "classification", "height_ft", "above_grade_ft", "owner", "circuit",
        "lean_degrees", "lean_status", "ai_score", "ai_confidence", "recommendation",
    ):
        if field in target:
            setattr(pole, field, target[field])
    pole.severity = target["severity"]


def _osm_report_rows() -> list[tuple[str, str, str, dbm.Severity, str, str, str]]:
    poles = list(iter_osm_poles(detroit_only=True))
    if not poles:
        return []

    # Pick well-spaced nodes so reports visibly land across the map.
    step = max(1, len(poles) // len(OSM_REPORT_TEMPLATES))
    selected = [poles[index * step] for index in range(len(OSM_REPORT_TEMPLATES))]

    return [
        (
            report_id,
            pole["id"],
            title,
            severity,
            user_id,
            submitted_at,
            _location_label(pole),
        )
        for pole, (report_id, title, severity, user_id, submitted_at) in zip(selected, OSM_REPORT_TEMPLATES)
    ]


def _severity_rank(severity: dbm.Severity) -> int:
    return {
        dbm.Severity.LOW: 0,
        dbm.Severity.MEDIUM: 1,
        dbm.Severity.HIGH: 2,
        dbm.Severity.CRITICAL: 3,
    }[severity]


def _promote_pole_for_report(db, pole_id: str, severity: dbm.Severity, title: str) -> None:
    pole = db.get(dbm.Pole, pole_id)
    if not pole:
        return
    if _severity_rank(severity) >= _severity_rank(pole.severity):
        pole.severity = severity
        pole.ai_score = {
            dbm.Severity.CRITICAL: 92,
            dbm.Severity.HIGH: 76,
            dbm.Severity.MEDIUM: 54,
            dbm.Severity.LOW: 24,
        }[severity]
        pole.ai_confidence = "seeded from OSM report"
        pole.recommendation = title


def _osm_history_events(report_rows: list[tuple[str, str, str, dbm.Severity, str, str, str]]) -> list[dict]:
    return [
        {
            "id": f"evt-{report_id.lower()}",
            "pole_id": pole_id,
            "report_id": report_id,
            "type": dbm.HistoryEventType.REPORT,
            "title": f"Report {report_id} submitted from DTE OSM map node",
            "event_date": submitted_at,
            "author_user_id": user_id,
            "description": title,
            "severity": severity,
            "pin_color": _SEV_PIN_COLOR[severity],
        }
        for report_id, pole_id, title, severity, user_id, submitted_at, _location in report_rows
    ]


def _purge_synthetic_poles(db) -> int:
    """Delete any leftover P-XXXX synthetic poles (and their cascading data) from prior seed runs."""
    result = db.execute(delete(dbm.Pole).where(dbm.Pole.id.like("P-%")))
    return result.rowcount


def _seed_osm_poles(db, batch_size: int = 2500) -> tuple[int, int]:
    if not CSV_PATH.exists() and not GEOJSON_PATH.exists():
        return 0, 0

    inserted = 0
    updated = 0
    batch: list[dict] = []

    def flush_batch() -> None:
        nonlocal inserted, updated, batch
        if not batch:
            return
        ids = [row["id"] for row in batch]
        existing = set(db.scalars(select(dbm.Pole.id).where(dbm.Pole.id.in_(ids))).all())
        new_rows = [row for row in batch if row["id"] not in existing]
        existing_rows = [row for row in batch if row["id"] in existing]
        if new_rows:
            db.bulk_insert_mappings(dbm.Pole, new_rows)
            inserted += len(new_rows)
        if existing_rows:
            db.bulk_update_mappings(dbm.Pole, existing_rows)
            updated += len(existing_rows)
        batch = []

    for pole in iter_osm_poles(detroit_only=True):
        neighborhood, intersection, circuit = _nearest_detroit_place(pole["latitude"], pole["longitude"])
        pole = {
            **pole,
            "address": f"{intersection} area, {neighborhood}, Detroit, MI - OSM node {pole['id'].replace('OSM-', '')}",
            "circuit": circuit,
            "sector": neighborhood,
        }
        batch.append(pole)
        if len(batch) >= batch_size:
            flush_batch()
    flush_batch()
    return inserted, updated


def seed_dashboard_data() -> None:
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not set")

    with SessionLocal() as db:
        # ── 1. Users ──────────────────────────────────────────────────────────
        for values in USERS:
            _upsert(db, dbm.User, values["id"], values)

        # ── 2. Remove any stale P-XXXX synthetic poles from prior seed runs ──
        purged = _purge_synthetic_poles(db)
        if purged:
            print(f"Purged {purged} synthetic P-XXXX pole(s) and their cascaded data.")

        # ── 3. OSM pole bulk-load from CSV ────────────────────────────────────
        osm_poles_inserted, osm_poles_updated = _seed_osm_poles(db)
        db.flush()

        # ── 4. Resolve nearest OSM pole for each detailed target ──────────────
        used_ids: set[str] = set()
        resolved_targets: list[tuple[dbm.Pole, dict]] = []

        for target in DETAILED_POLE_TARGETS:
            pole = _nearest_osm_pole(db, target["target_lat"], target["target_lon"], used_ids)
            if pole is None:
                print(
                    f"Warning: no OSM pole found near "
                    f"({target['target_lat']}, {target['target_lon']}) — skipping"
                )
                continue
            used_ids.add(pole.id)
            _apply_pole_metadata(pole, target)
            resolved_targets.append((pole, target))

        # ── 5. Resolve nearest OSM pole for each map-only target ──────────────
        for target in MAP_ONLY_TARGETS:
            pole = _nearest_osm_pole(db, target["target_lat"], target["target_lon"], used_ids)
            if pole is None:
                continue
            used_ids.add(pole.id)
            pole.severity = target["severity"]
            pole.recommendation = "No action currently recommended"

        db.flush()

        # ── 6. Reports, photos, and history events for detailed targets ────────
        all_reports = 0
        all_photos = 0
        all_events = 0

        for pole, target in resolved_targets:
            rpt = target["report"]
            report_id: str = rpt["id"]
            rpt_severity: dbm.Severity = rpt["severity"]
            neighborhood, intersection, _circuit = _nearest_detroit_place(pole.latitude, pole.longitude)
            location = rpt.get("location") or f"{intersection}, {neighborhood}, Detroit"

            _upsert(
                db,
                dbm.Report,
                report_id,
                {
                    "id": report_id,
                    "pole_id": pole.id,
                    "title": rpt["title"],
                    "severity": rpt_severity,
                    "status": dbm.ReportStatus.OPEN,
                    "submitted_by_user_id": rpt["user_id"],
                    "submitted_at": _parse_dt(rpt["submitted_at"]),
                    "location": location,
                },
            )
            all_reports += 1

            # Auto-generate the REPORT-type history event for this submission
            _upsert(
                db,
                dbm.PoleHistoryEvent,
                f"evt-{report_id.lower()}",
                {
                    "id": f"evt-{report_id.lower()}",
                    "pole_id": pole.id,
                    "report_id": report_id,
                    "type": dbm.HistoryEventType.REPORT,
                    "title": f"Report {report_id} submitted",
                    "event_date": _parse_dt(rpt["submitted_at"]),
                    "author_user_id": rpt["user_id"],
                    "description": rpt["title"],
                    "severity": rpt_severity,
                    "pin_color": _SEV_PIN_COLOR[rpt_severity],
                },
            )
            all_events += 1

            # Photos
            for photo_id, label, severity, severity_label in target.get("photos", []):
                _upsert(
                    db,
                    dbm.FieldPhoto,
                    photo_id,
                    {
                        "id": photo_id,
                        "pole_id": pole.id,
                        "report_id": report_id,
                        "label": label,
                        "severity": severity,
                        "severity_label": severity_label,
                    },
                )
                all_photos += 1

            # Extra history events (comments, inspections, upgrades, …)
            for event in target.get("history_extra", []):
                evt_type: dbm.HistoryEventType = event["type"]
                # COMMENT events belong to this pole's report unless overridden
                evt_report_id = event.get("report_id") or (
                    report_id if evt_type == dbm.HistoryEventType.COMMENT else None
                )
                _upsert(
                    db,
                    dbm.PoleHistoryEvent,
                    event["id"],
                    {
                        "id": event["id"],
                        "pole_id": pole.id,
                        "report_id": evt_report_id,
                        "type": evt_type,
                        "title": event["title"],
                        "event_date": _parse_dt(event.get("event_date")),
                        "author_user_id": event.get("author_user_id"),
                        "description": event.get("description"),
                        "comment": event.get("comment"),
                        "severity": event.get("severity"),
                        "pin_color": event["pin_color"],
                    },
                )
                all_events += 1

        db.flush()

        # ── 7. Dynamically-selected OSM reports (spread across the city) ───────
        osm_report_rows = _osm_report_rows()
        for report_id, pole_id, title, severity, user_id, submitted_at, location in osm_report_rows:
            _promote_pole_for_report(db, pole_id, severity, title)
            _upsert(
                db,
                dbm.Report,
                report_id,
                {
                    "id": report_id,
                    "pole_id": pole_id,
                    "title": title,
                    "severity": severity,
                    "status": dbm.ReportStatus.OPEN,
                    "submitted_by_user_id": user_id,
                    "submitted_at": _parse_dt(submitted_at),
                    "location": location,
                },
            )

        osm_history = _osm_history_events(osm_report_rows)
        for event in osm_history:
            _upsert(
                db,
                dbm.PoleHistoryEvent,
                event["id"],
                {
                    "id": event["id"],
                    "pole_id": event["pole_id"],
                    "report_id": event.get("report_id"),
                    "type": event["type"],
                    "title": event["title"],
                    "event_date": _parse_dt(event.get("event_date")),
                    "author_user_id": event.get("author_user_id"),
                    "description": event.get("description"),
                    "comment": event.get("comment"),
                    "severity": event.get("severity"),
                    "pin_color": event["pin_color"],
                },
            )

        db.commit()

        print(
            {
                "users_seeded": len(USERS),
                "osm_poles_inserted": osm_poles_inserted,
                "osm_poles_updated": osm_poles_updated,
                "detailed_targets_resolved": len(resolved_targets),
                "map_only_targets": len(MAP_ONLY_TARGETS),
                "reports_seeded": all_reports + len(osm_report_rows),
                "photos_seeded": all_photos,
                "history_events_seeded": all_events + len(osm_history),
            }
        )


if __name__ == "__main__":
    seed_dashboard_data()
