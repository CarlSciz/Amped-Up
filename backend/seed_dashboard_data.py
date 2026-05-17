from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

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

POLES = [
    {
        "id": "P-1147",
        "classification": "Class 3 Southern Pine",
        "severity": dbm.Severity.CRITICAL,
        "address": "Michigan Ave & Trumbull Ave, Detroit, MI",
        "latitude": 42.3321,
        "longitude": -83.0478,
        "height_ft": 45,
        "above_grade_ft": 38,
        "owner": "DTE Energy - Joint use with Comcast",
        "circuit": "Feeder F-407 - 13.2 kV",
        "lean_degrees": 12.4,
        "lean_status": "spec <= 5 degrees",
        "ai_score": 94,
        "ai_confidence": "high confidence",
        "recommendation": "Replace within 7 days",
        "sector": "7",
    },
    {
        "id": "P-1192",
        "classification": "Class 2 Southern Pine",
        "severity": dbm.Severity.CRITICAL,
        "address": "W. Vernor Hwy & Rosa Parks Blvd, Detroit, MI",
        "latitude": 42.3298,
        "longitude": -83.0456,
        "height_ft": 40,
        "above_grade_ft": 34,
        "owner": "DTE Energy",
        "circuit": "Feeder F-312 - 13.2 kV",
        "ai_score": 88,
        "ai_confidence": "high confidence",
        "recommendation": "Dispatch hazmat and replace transformer",
        "sector": "7",
    },
    {
        "id": "P-1062",
        "classification": "Class 3 Southern Pine",
        "severity": dbm.Severity.HIGH,
        "address": "W. Willis St & 13th St, Detroit, MI",
        "latitude": 42.3339,
        "longitude": -83.0462,
        "height_ft": 45,
        "above_grade_ft": 37,
        "owner": "DTE Energy",
        "circuit": "Feeder F-501 - 13.2 kV",
        "ai_score": 76,
        "ai_confidence": "medium confidence",
        "recommendation": "Inspect and treat within 30 days",
        "sector": "7",
    },
    {
        "id": "P-1078",
        "classification": "Class 4 Southern Pine",
        "severity": dbm.Severity.HIGH,
        "address": "Michigan Ave & 15th St, Detroit, MI",
        "latitude": 42.3315,
        "longitude": -83.0510,
        "height_ft": 35,
        "above_grade_ft": 28,
        "owner": "DTE Energy",
        "circuit": "Feeder F-407 - 13.2 kV",
        "ai_score": 71,
        "ai_confidence": "medium confidence",
        "recommendation": "Replace insulator within 30 days",
        "sector": "7",
    },
    {
        "id": "P-1023",
        "classification": "Class 3 Southern Pine",
        "severity": dbm.Severity.MEDIUM,
        "address": "Temple St & Trumbull Ave, Detroit, MI",
        "latitude": 42.3352,
        "longitude": -83.0481,
        "height_ft": 45,
        "above_grade_ft": 38,
        "owner": "DTE Energy",
        "circuit": "Feeder F-501 - 13.2 kV",
        "ai_score": 54,
        "ai_confidence": "medium confidence",
        "recommendation": "Schedule vegetation trim within 90 days",
        "sector": "7",
    },
    {
        "id": "P-1131",
        "classification": "Class 3 Steel",
        "severity": dbm.Severity.MEDIUM,
        "address": "W. Grand Blvd & 14th St, Detroit, MI",
        "latitude": 42.3374,
        "longitude": -83.0498,
        "height_ft": 50,
        "above_grade_ft": 43,
        "owner": "DTE Energy",
        "circuit": "Feeder F-312 - 13.2 kV",
        "ai_score": 58,
        "ai_confidence": "medium confidence",
        "recommendation": "Re-tension guy wire within 90 days",
        "sector": "7",
    },
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

MAP_ONLY_POLES = [
    ("P-1001", dbm.Severity.LOW, 42.3314, -83.0458, "Woodward Ave & Campus Martius, Downtown Detroit, MI", "DTE Downtown Network - 13.2 kV", "Downtown"),
    ("P-1002", dbm.Severity.LOW, 42.3482, -83.0418, "Russell St & Adelaide St, Eastern Market, Detroit, MI", "DTE Eastern Market 214 - 13.2 kV", "Eastern Market"),
    ("P-1003", dbm.Severity.LOW, 42.3517, -83.0601, "Woodward Ave & W. Willis St, Midtown Detroit, MI", "DTE Midtown 501 - 13.2 kV", "Midtown"),
    ("P-1004", dbm.Severity.LOW, 42.3209, -83.0792, "W. Vernor Hwy & Bagley St, Mexicantown, Detroit, MI", "DTE Vernor 312 - 13.2 kV", "Mexicantown"),
    ("P-1005", dbm.Severity.MEDIUM, 42.3379, -83.0188, "Jefferson Ave & Chene St, Rivertown, Detroit, MI", "DTE Rivertown 118 - 13.2 kV", "Rivertown"),
    ("P-1006", dbm.Severity.LOW, 42.3671, -83.0752, "W. Grand Blvd & Woodward Ave, New Center, Detroit, MI", "DTE New Center 622 - 13.2 kV", "New Center"),
    ("P-1007", dbm.Severity.LOW, 42.3795, -83.0966, "Chicago Blvd & 2nd Ave, Boston-Edison, Detroit, MI", "DTE Boston Edison 455 - 13.2 kV", "Boston-Edison"),
    ("P-1008", dbm.Severity.LOW, 42.3003, -83.1032, "Fort St & Livernois Ave, Southwest Detroit, MI", "DTE Southwest 730 - 13.2 kV", "Southwest Detroit"),
    ("P-1009", dbm.Severity.LOW, 42.4027, -82.9348, "E. Warren Ave & Cadieux Rd, East English Village, Detroit, MI", "DTE East English 884 - 13.2 kV", "East English Village"),
]

REPORTS = [
    ("RPT-1147", "P-1147", "Lean exceeds 12 degrees, crossarm rot", dbm.Severity.CRITICAL, "tech-jc", "2026-05-14T11:48:00", "Michigan Ave & Trumbull Ave"),
    ("RPT-1192", "P-1192", "Transformer leak, oil stains", dbm.Severity.CRITICAL, "tech-dk", "2026-05-14T08:30:00", "W. Vernor Hwy & Rosa Parks Blvd"),
    ("RPT-1062", "P-1062", "Woodpecker damage, upper third", dbm.Severity.HIGH, "tech-as", "2026-05-13T09:15:00", "W. Willis St & 13th St"),
    ("RPT-1078", "P-1078", "Insulator cracked, phase B", dbm.Severity.HIGH, "tech-mr", "2026-05-13T14:22:00", "Michigan Ave & 15th St"),
    ("RPT-1023", "P-1023", "Vegetation contact, secondary", dbm.Severity.MEDIUM, "tech-tb", "2026-05-12T16:05:00", "Temple St & Trumbull Ave"),
    ("RPT-1131", "P-1131", "Guy wire tension below spec", dbm.Severity.MEDIUM, "tech-lw", "2026-05-11T10:44:00", "W. Grand Blvd & 14th St"),
    ("RPT-1001", "P-1001", "Low priority surface weathering", dbm.Severity.LOW, "tech-ng", "2026-05-10T13:20:00", "Woodward Ave & Campus Martius"),
    ("RPT-1002", "P-1002", "Faded pole tag, routine re-stencil", dbm.Severity.LOW, "tech-ho", "2026-05-10T09:05:00", "Russell St & Adelaide St"),
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

PHOTOS = [
    ("photo-1", "P-1147", "RPT-1147", "01 - Overview, west", dbm.Severity.CRITICAL, "12 degree lean"),
    ("photo-2", "P-1147", "RPT-1147", "02 - Crossarm closeup", dbm.Severity.CRITICAL, "Rot"),
    ("photo-3", "P-1147", "RPT-1147", "03 - Transformer base", dbm.Severity.MEDIUM, "Oil staining"),
    ("photo-4", "P-1192", "RPT-1192", "01 - Overview, north", dbm.Severity.CRITICAL, "Oil leak"),
    ("photo-5", "P-1192", "RPT-1192", "02 - Transformer base", dbm.Severity.CRITICAL, "Staining"),
]

HISTORY_EVENTS = [
    {
        "id": "evt-1",
        "pole_id": "P-1147",
        "report_id": "RPT-1147",
        "type": dbm.HistoryEventType.REPORT,
        "title": "Report RPT-1147 submitted by J. Chen",
        "event_date": "2026-05-14T11:48:00",
        "author_user_id": "tech-jc",
        "description": "3 photos uploaded. 12 degree lean and crossarm rot called out. AI scored 94, classified Critical. Pending crew assignment.",
        "severity": dbm.Severity.CRITICAL,
        "pin_color": "#EF4444",
    },
    {
        "id": "evt-2",
        "pole_id": "P-1147",
        "report_id": "RPT-1147",
        "type": dbm.HistoryEventType.COMMENT,
        "title": "R. Patel - Comment on report UP-2026-04891",
        "event_date": "2026-05-14T15:42:00",
        "author_user_id": "user-rp",
        "comment": "Crew 14 dispatched for tomorrow 7 AM. Bringing a 45 ft Class 3 replacement and the lift truck. Traffic permit cleared with the city.",
        "pin_color": "#475569",
    },
    {
        "id": "evt-3",
        "pole_id": "P-1147",
        "report_id": "RPT-1147",
        "type": dbm.HistoryEventType.COMMENT,
        "title": "J. Liu - Comment on report UP-2026-04891",
        "event_date": "2026-05-14T13:08:00",
        "author_user_id": "user-jl",
        "comment": "De-energize feeder F-407 before approach. Comcast fiber attached at 23 ft, coordinate with their NOC ticket 88421.",
        "pin_color": "#475569",
    },
    {
        "id": "evt-4",
        "pole_id": "P-1147",
        "type": dbm.HistoryEventType.INSPECTION,
        "title": "Routine inspection - drone",
        "event_date": "2025-11-02",
        "description": "Last manual check. Minor lean noted (4.8 degrees). Vegetation trimmed.",
        "pin_color": "#FBBF24",
    },
    {
        "id": "evt-5",
        "pole_id": "P-1147",
        "type": dbm.HistoryEventType.UPGRADE,
        "title": "Hardware upgrade",
        "event_date": "2022-08-19",
        "description": "Transformer swapped from 25 kVA to 50 kVA. Polymer insulators installed.",
        "pin_color": "#60A5FA",
    },
    {
        "id": "evt-6",
        "pole_id": "P-1147",
        "type": dbm.HistoryEventType.JOINT_USE,
        "title": "Joint use added",
        "event_date": "2019-03-04",
        "description": "Comcast fiber attachment permitted at 23 ft above grade.",
        "pin_color": "#60A5FA",
    },
    {
        "id": "evt-7",
        "pole_id": "P-1147",
        "type": dbm.HistoryEventType.TREATMENT,
        "title": "Treatment cycle",
        "event_date": "2014-06-12",
        "description": "CCA pressure-treatment refresh. Estimated remaining life 22 years.",
        "pin_color": "#10B981",
    },
    {
        "id": "evt-8",
        "pole_id": "P-1147",
        "type": dbm.HistoryEventType.INSTALL,
        "title": "Pole installed",
        "event_date": "2008-04-27",
        "description": "Class 3 Southern Pine, 45 ft. Original contractor Quanta Services.",
        "pin_color": "#6B7280",
    },
    {
        "id": "evt-9",
        "pole_id": "P-1192",
        "report_id": "RPT-1192",
        "type": dbm.HistoryEventType.REPORT,
        "title": "Report RPT-1192 submitted by D. Kim",
        "event_date": "2026-05-14T08:30:00",
        "author_user_id": "tech-dk",
        "description": "Transformer oil leak observed. Significant staining on pole base and surrounding ground.",
        "severity": dbm.Severity.CRITICAL,
        "pin_color": "#EF4444",
    },
    {
        "id": "evt-10",
        "pole_id": "P-1192",
        "type": dbm.HistoryEventType.INSTALL,
        "title": "Pole installed",
        "event_date": None,
        "pin_color": "#6B7280",
    },
]


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


def _osm_report_rows() -> list[tuple[str, str, str, dbm.Severity, str, str, str]]:
    poles = list(iter_osm_poles(detroit_only=True))
    if not poles:
        return []

    # Pick well-spaced nodes from the rendered Detroit inventory so reports visibly land across the map.
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
            "pin_color": {
                dbm.Severity.CRITICAL: "#EF4444",
                dbm.Severity.HIGH: "#F97316",
                dbm.Severity.MEDIUM: "#FBBF24",
                dbm.Severity.LOW: "#10B981",
            }[severity],
        }
        for report_id, pole_id, title, severity, user_id, submitted_at, _location in report_rows
    ]


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
        for values in USERS:
            _upsert(db, dbm.User, values["id"], values)

        for values in POLES:
            _upsert(db, dbm.Pole, values["id"], values)

        for pole_id, severity, lat, lon, address, circuit, sector in MAP_ONLY_POLES:
            _upsert(
                db,
                dbm.Pole,
                pole_id,
                {
                    "id": pole_id,
                    "classification": "Unknown",
                    "severity": severity,
                    "address": address,
                    "latitude": lat,
                    "longitude": lon,
                    "owner": "DTE Energy",
                    "circuit": circuit,
                    "sector": sector,
                    "recommendation": "No action currently recommended",
                },
            )

        osm_poles_inserted, osm_poles_updated = _seed_osm_poles(db)

        db.flush()

        osm_report_rows = _osm_report_rows()
        report_rows = [*REPORTS, *osm_report_rows]

        for report_id, pole_id, title, severity, user_id, submitted_at, location in report_rows:
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

        db.flush()

        for photo_id, pole_id, report_id, label, severity, severity_label in PHOTOS:
            _upsert(
                db,
                dbm.FieldPhoto,
                photo_id,
                {
                    "id": photo_id,
                    "pole_id": pole_id,
                    "report_id": report_id,
                    "label": label,
                    "severity": severity,
                    "severity_label": severity_label,
                },
            )

        history_events = [*HISTORY_EVENTS, *_osm_history_events(osm_report_rows)]
        for event in history_events:
            values = {
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
            }
            _upsert(db, dbm.PoleHistoryEvent, values["id"], values)

        db.commit()

        print(
            {
            "users_seeded": len(USERS),
            "poles_seeded": len(POLES) + len(MAP_ONLY_POLES) + osm_poles_inserted,
            "osm_poles_inserted": osm_poles_inserted,
            "osm_poles_updated": osm_poles_updated,
            "reports_seeded": len(report_rows),
            "photos_seeded": len(PHOTOS),
            "history_events_seeded": len(history_events),
            }
        )


if __name__ == "__main__":
    seed_dashboard_data()
