from __future__ import annotations

from datetime import datetime
from functools import lru_cache

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session, joinedload

from . import orm_models as dbm
from .dashboard_models import (
    DashboardFilterOptions,
    DashboardSummary,
    FieldPhoto,
    FilterOption,
    HistoryEvent,
    MapPole,
    Note,
    PoleDetail,
    PoleHistory,
    Report,
    ReportAuthor,
    ReportStatus,
    SelectedReport,
    Severity,
    User,
)

from .osm_pole_data import iter_osm_poles

DEFAULT_CURRENT_USER_ID = "user-001"
DEFAULT_SECTOR = "Detroit"
MAX_MAP_POLES = 7500


class DashboardFilters:
    def __init__(
        self,
        severities: list[dbm.Severity] | None = None,
        classifications: list[str] | None = None,
        circuits: list[str] | None = None,
        owners: list[str] | None = None,
        violation_families: list[str] | None = None,
        violation_type_ids: list[str] | None = None,
        search: str | None = None,
    ) -> None:
        self.severities = severities or []
        self.classifications = classifications or []
        self.circuits = circuits or []
        self.owners = owners or []
        self.violation_families = violation_families or []
        self.violation_type_ids = violation_type_ids or []
        self.search = search.strip() if search else None


def _apply_pole_filters(stmt, filters: DashboardFilters):
    if filters.severities:
        stmt = stmt.where(dbm.Pole.severity.in_(filters.severities))
    if filters.classifications:
        stmt = stmt.where(dbm.Pole.classification.in_(filters.classifications))
    if filters.circuits:
        stmt = stmt.where(dbm.Pole.circuit.in_(filters.circuits))
    if filters.owners:
        stmt = stmt.where(dbm.Pole.owner.in_(filters.owners))
    if filters.search:
        term = f"%{filters.search}%"
        stmt = stmt.where(
            dbm.Pole.id.ilike(term)
            | dbm.Pole.classification.ilike(term)
            | dbm.Pole.address.ilike(term)
            | dbm.Pole.owner.ilike(term)
            | dbm.Pole.circuit.ilike(term)
            | dbm.Pole.recommendation.ilike(term)
        )
    return stmt


def _apply_detroit_map_scope(stmt):
    return stmt.where(
        dbm.Pole.latitude >= 42.20,
        dbm.Pole.latitude <= 42.55,
        dbm.Pole.longitude >= -83.35,
        dbm.Pole.longitude <= -82.85,
    )


def _has_active_filters(filters: DashboardFilters) -> bool:
    return bool(
        filters.severities
        or filters.classifications
        or filters.circuits
        or filters.owners
        or filters.violation_families
        or filters.violation_type_ids
        or filters.search
    )


@lru_cache(maxsize=4)
def _cached_csv_map_poles(limit: int = MAX_MAP_POLES) -> tuple[MapPole, ...]:
    rows: list[MapPole] = []
    for pole in iter_osm_poles(detroit_only=True):
        rows.append(
            MapPole(
                id=pole["id"],
                severity=Severity(pole["severity"].value),
                lat=pole["latitude"],
                lon=pole["longitude"],
            )
        )
        if len(rows) >= limit:
            break
    return tuple(rows)


def _csv_map_poles(limit: int = MAX_MAP_POLES, offset: int = 0) -> list[MapPole]:
    return list(_cached_csv_map_poles(MAX_MAP_POLES)[offset : offset + limit])


@lru_cache(maxsize=1)
def _csv_map_pole_count() -> int:
    return sum(1 for _ in iter_osm_poles(detroit_only=True))


def _has_seeded_osm_poles(db: Session) -> bool:
    stmt = (
        _apply_detroit_map_scope(select(func.count()).select_from(dbm.Pole))
        .where(dbm.Pole.id.like("OSM-%"))
    )
    return (db.scalar(stmt) or 0) > 0


def _apply_report_filters(stmt, filters: DashboardFilters):
    if filters.severities:
        stmt = stmt.where(dbm.Report.severity.in_(filters.severities))
    if filters.classifications:
        stmt = stmt.where(dbm.Pole.classification.in_(filters.classifications))
    if filters.circuits:
        stmt = stmt.where(dbm.Pole.circuit.in_(filters.circuits))
    if filters.owners:
        stmt = stmt.where(dbm.Pole.owner.in_(filters.owners))
    if filters.violation_families:
        stmt = stmt.where(dbm.ViolationType.violation_family.in_(filters.violation_families))
    if filters.violation_type_ids:
        stmt = stmt.where(dbm.Report.violation_type_id.in_(filters.violation_type_ids))
    if filters.search:
        term = f"%{filters.search}%"
        stmt = stmt.where(
            dbm.Report.id.ilike(term)
            | dbm.Report.title.ilike(term)
            | dbm.Report.location.ilike(term)
            | dbm.Report.description.ilike(term)
            | dbm.Pole.id.ilike(term)
            | dbm.Pole.classification.ilike(term)
            | dbm.Pole.address.ilike(term)
            | dbm.Pole.owner.ilike(term)
            | dbm.Pole.circuit.ilike(term)
            | dbm.ViolationType.name.ilike(term)
            | dbm.ViolationType.code.ilike(term)
            | dbm.ViolationType.violation_family.ilike(term)
        )
    return stmt


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _severity(value: dbm.Severity | None) -> Severity | None:
    return Severity(value.value) if value else None


def _report_status(value: dbm.ReportStatus) -> ReportStatus:
    return ReportStatus(value.value)


def _history_type(value: dbm.HistoryEventType):
    from .dashboard_models import HistoryEventType

    return HistoryEventType(value.value)


def _user(user: dbm.User) -> User:
    return User(id=user.id, initials=user.initials, name=user.name, role=user.role)


def _author(user: dbm.User | None) -> ReportAuthor | None:
    if not user:
        return None
    return ReportAuthor(initials=user.initials, name=user.name)


def get_current_user(db: Session) -> User:
    user = db.get(dbm.User, DEFAULT_CURRENT_USER_ID)
    if not user:
        user = db.scalars(select(dbm.User).order_by(dbm.User.created_at, dbm.User.id).limit(1)).first()
    if user:
        return _user(user)
    return User(id=DEFAULT_CURRENT_USER_ID, initials="ZM", name="Z. Metiva", role="Field ops lead")


def get_current_user_record(db: Session) -> dbm.User | None:
    user = db.get(dbm.User, DEFAULT_CURRENT_USER_ID)
    if user:
        return user
    return db.scalars(select(dbm.User).order_by(dbm.User.created_at, dbm.User.id).limit(1)).first()


def get_summary(db: Session, filters: DashboardFilters | None = None, sector: str = DEFAULT_SECTOR) -> DashboardSummary:
    filters = filters or DashboardFilters()
    total_poles_stmt = _apply_pole_filters(select(func.count()).select_from(dbm.Pole), filters)
    total_poles = db.scalar(total_poles_stmt) or 0

    open_reports_stmt = (
        select(func.count())
        .select_from(dbm.Report)
        .join(dbm.Pole)
        .outerjoin(dbm.ViolationType)
        .where(dbm.Report.status == dbm.ReportStatus.OPEN)
    )
    open_reports = db.scalar(_apply_report_filters(open_reports_stmt, filters)) or 0

    severity_stmt = _apply_pole_filters(
        select(dbm.Pole.severity, func.count())
        .select_from(dbm.Pole)
        .group_by(dbm.Pole.severity),
        filters,
    )
    severity_counts = dict(db.execute(severity_stmt).all())

    return DashboardSummary(
        total_poles=total_poles,
        new_since_last_scan=0,
        critical=severity_counts.get(dbm.Severity.CRITICAL, 0),
        high=severity_counts.get(dbm.Severity.HIGH, 0),
        medium=severity_counts.get(dbm.Severity.MEDIUM, 0),
        low=severity_counts.get(dbm.Severity.LOW, 0),
        open_reports=open_reports,
        sector=sector,
        date=datetime.now().date().isoformat(),
    )


def get_reports(db: Session, filters: DashboardFilters | None = None, open_only: bool = False) -> list[Report]:
    filters = filters or DashboardFilters()
    status_rank = case(
        (dbm.Report.status == dbm.ReportStatus.OPEN, 0),
        (dbm.Report.status == dbm.ReportStatus.SNOOZED, 1),
        (dbm.Report.status == dbm.ReportStatus.APPROVED, 2),
        (dbm.Report.status == dbm.ReportStatus.DISMISSED, 3),
        else_=4,
    )
    stmt = (
        select(dbm.Report)
        .options(joinedload(dbm.Report.submitted_by), joinedload(dbm.Report.pole))
        .join(dbm.Pole)
        .outerjoin(dbm.ViolationType)
        .order_by(status_rank, dbm.Report.submitted_at.desc(), dbm.Report.id)
    )
    if open_only:
        stmt = stmt.where(dbm.Report.status == dbm.ReportStatus.OPEN)
    rows = db.scalars(_apply_report_filters(stmt, filters)).all()

    return [
        Report(
            id=row.id,
            pole_id=row.pole_id,
            title=row.title,
            severity=Severity(row.severity.value),
            submitted_by=ReportAuthor(initials=row.submitted_by.initials, name=row.submitted_by.name),
            submitted_at=row.submitted_at.isoformat(),
            location=row.location,
            status=_report_status(row.status),
            map_node=MapPole(
                id=row.pole.id,
                severity=Severity(row.pole.severity.value),
                lat=row.pole.latitude,
                lon=row.pole.longitude,
            ) if row.pole else None,
        )
        for row in rows
    ]


def get_open_reports(db: Session, filters: DashboardFilters | None = None) -> list[Report]:
    return get_reports(db, filters, open_only=True)


def get_selected_report(db: Session, report_id: str) -> SelectedReport | None:
    row = db.scalars(
        select(dbm.Report)
        .options(joinedload(dbm.Report.submitted_by))
        .where(dbm.Report.id == report_id)
    ).first()
    if not row:
        return None

    return SelectedReport(
        id=row.id,
        pole_id=row.pole_id,
        title=row.title,
        severity=Severity(row.severity.value),
        submitted_by=_user(row.submitted_by),
        submitted_at=row.submitted_at.isoformat(),
    )


def get_pole_detail(db: Session, pole_id: str) -> PoleDetail | None:
    pole = db.get(dbm.Pole, pole_id)
    if not pole:
        return None

    height = "Unknown"
    if pole.height_ft is not None and pole.above_grade_ft is not None:
        height = f"{pole.height_ft:g} ft (above grade {pole.above_grade_ft:g} ft)"
    elif pole.height_ft is not None:
        height = f"{pole.height_ft:g} ft"

    lean = None
    if pole.lean_degrees is not None:
        lean = f"{pole.lean_degrees:g} degrees"
        if pole.lean_status:
            lean = f"{lean} ({pole.lean_status})"

    return PoleDetail(
        id=pole.id,
        classification=pole.classification,
        severity=Severity(pole.severity.value),
        address=pole.address,
        lat=pole.latitude,
        lon=pole.longitude,
        height=height,
        owner=pole.owner,
        circuit=pole.circuit,
        lean=lean,
        ai_score=pole.ai_score or 0,
        ai_confidence=pole.ai_confidence or "unknown confidence",
        recommendation=pole.recommendation or "No recommendation recorded",
    )


def get_photos(db: Session, pole_id: str) -> list[FieldPhoto]:
    rows = db.scalars(
        select(dbm.FieldPhoto)
        .where(dbm.FieldPhoto.pole_id == pole_id)
        .order_by(dbm.FieldPhoto.uploaded_at.desc(), dbm.FieldPhoto.id)
    ).all()

    return [
        FieldPhoto(
            id=row.id,
            label=row.label,
            image_url=row.image_url,
            severity=_severity(row.severity),
            severity_label=row.severity_label,
        )
        for row in rows
    ]


def get_history(db: Session, pole_id: str) -> PoleHistory | None:
    if not db.get(dbm.Pole, pole_id):
        return None

    rows = db.scalars(
        select(dbm.PoleHistoryEvent)
        .options(joinedload(dbm.PoleHistoryEvent.author))
        .where(dbm.PoleHistoryEvent.pole_id == pole_id)
        .order_by(dbm.PoleHistoryEvent.event_date.desc().nullslast(), dbm.PoleHistoryEvent.created_at.desc())
    ).all()

    install_event = next((row for row in rows if row.type == dbm.HistoryEventType.INSTALL and row.event_date), None)
    lifecycle_years = None
    if install_event:
        lifecycle_years = (datetime.now(install_event.event_date.tzinfo) - install_event.event_date).days // 365

    comment_count = sum(1 for row in rows if row.type == dbm.HistoryEventType.COMMENT)

    return PoleHistory(
        pole_id=pole_id,
        lifecycle_years=lifecycle_years,
        event_count=len(rows),
        comment_count=comment_count,
        events=[
            HistoryEvent(
                id=row.id,
                type=_history_type(row.type),
                title=row.title,
                date=_iso(row.event_date),
                author=_author(row.author),
                description=row.description,
                comment=row.comment,
                severity=_severity(row.severity),
                pin_color=row.pin_color,
            )
            for row in rows
        ],
    )


def get_map_poles(
    db: Session,
    filters: DashboardFilters | None = None,
    limit: int = MAX_MAP_POLES,
    offset: int = 0,
) -> list[MapPole]:
    filters = filters or DashboardFilters()
    limit = max(0, min(limit, MAX_MAP_POLES))
    offset = max(0, offset)
    if not _has_active_filters(filters) and not _has_seeded_osm_poles(db):
        csv_poles = _csv_map_poles(limit=limit, offset=offset)
        if csv_poles:
            return csv_poles

    stmt = select(dbm.Pole)
    if filters.violation_families or filters.violation_type_ids:
        stmt = stmt.join(dbm.Report).outerjoin(dbm.ViolationType).distinct()
        if filters.violation_families:
            stmt = stmt.where(dbm.ViolationType.violation_family.in_(filters.violation_families))
        if filters.violation_type_ids:
            stmt = stmt.where(dbm.Report.violation_type_id.in_(filters.violation_type_ids))
    stmt = _apply_detroit_map_scope(stmt)
    severity_rank = case(
        (dbm.Pole.severity == dbm.Severity.CRITICAL, 0),
        (dbm.Pole.severity == dbm.Severity.HIGH, 1),
        (dbm.Pole.severity == dbm.Severity.MEDIUM, 2),
        (dbm.Pole.severity == dbm.Severity.LOW, 3),
        else_=4,
    )
    has_open_report = (
        select(dbm.Report.id)
        .where(dbm.Report.pole_id == dbm.Pole.id, dbm.Report.status == dbm.ReportStatus.OPEN)
        .exists()
    )
    has_any_report = select(dbm.Report.id).where(dbm.Report.pole_id == dbm.Pole.id).exists()
    report_rank = case((has_open_report, 0), (has_any_report, 1), else_=2)
    stmt = stmt.order_by(report_rank, severity_rank, dbm.Pole.id).offset(offset).limit(limit)
    rows = db.scalars(_apply_pole_filters(stmt, filters)).all()
    return [
        MapPole(
            id=row.id,
            severity=Severity(row.severity.value),
            lat=row.latitude,
            lon=row.longitude,
        )
        for row in rows
    ]


def get_map_pole_count(db: Session, filters: DashboardFilters | None = None) -> int:
    filters = filters or DashboardFilters()
    if not _has_active_filters(filters) and not _has_seeded_osm_poles(db):
        csv_count = _csv_map_pole_count()
        if csv_count:
            return csv_count

    stmt = select(func.count(dbm.Pole.id)).select_from(dbm.Pole)
    if filters.violation_families or filters.violation_type_ids:
        stmt = select(func.count(func.distinct(dbm.Pole.id))).select_from(dbm.Pole).join(dbm.Report).outerjoin(dbm.ViolationType)
        if filters.violation_families:
            stmt = stmt.where(dbm.ViolationType.violation_family.in_(filters.violation_families))
        if filters.violation_type_ids:
            stmt = stmt.where(dbm.Report.violation_type_id.in_(filters.violation_type_ids))
    return db.scalar(_apply_pole_filters(_apply_detroit_map_scope(stmt), filters)) or 0


def get_notes(db: Session, report_id: str) -> list[Note]:
    rows = db.scalars(
        select(dbm.ReportNote)
        .options(joinedload(dbm.ReportNote.author))
        .where(dbm.ReportNote.report_id == report_id)
        .order_by(dbm.ReportNote.created_at.asc(), dbm.ReportNote.id)
    ).all()

    return [
        Note(
            id=row.id,
            author=_user(row.author),
            content=row.content,
            created_at=row.created_at.isoformat(),
        )
        for row in rows
    ]


def get_note_count(db: Session, report_id: str) -> int:
    return db.scalar(
        select(func.count()).select_from(dbm.ReportNote).where(dbm.ReportNote.report_id == report_id)
    ) or 0


def _option_rows(db: Session, column, label_column=None) -> list[FilterOption]:
    label_column = label_column or column
    rows = db.execute(
        select(column, label_column, func.count())
        .select_from(dbm.Pole)
        .where(column.is_not(None))
        .group_by(column, label_column)
        .order_by(label_column)
    ).all()
    return [FilterOption(value=str(value), label=str(label), count=count) for value, label, count in rows]


def _matches_search(option: FilterOption, search: str | None) -> bool:
    if not search:
        return True
    term = search.lower()
    return term in option.value.lower() or term in option.label.lower()


def get_filter_options(db: Session, search: str | None = None) -> DashboardFilterOptions:
    severity_counts = dict(
        db.execute(select(dbm.Pole.severity, func.count()).select_from(dbm.Pole).group_by(dbm.Pole.severity)).all()
    )
    severities = [
        FilterOption(value=severity.value, label=severity.value.title(), count=severity_counts.get(severity, 0))
        for severity in [dbm.Severity.CRITICAL, dbm.Severity.HIGH, dbm.Severity.MEDIUM, dbm.Severity.LOW]
        if severity_counts.get(severity, 0) > 0
    ]

    violation_family_rows = db.execute(
        select(dbm.ViolationType.violation_family, func.count())
        .select_from(dbm.ViolationType)
        .where(dbm.ViolationType.is_active.is_(True))
        .group_by(dbm.ViolationType.violation_family)
        .order_by(dbm.ViolationType.violation_family)
    ).all()
    violation_families = [
        FilterOption(value=value, label=value.replace("_", " ").title(), count=count)
        for value, count in violation_family_rows
    ]

    violation_type_rows = db.execute(
        select(dbm.ViolationType.id, dbm.ViolationType.name, func.count(dbm.Report.id))
        .select_from(dbm.ViolationType)
        .outerjoin(dbm.Report)
        .where(dbm.ViolationType.is_active.is_(True))
        .group_by(dbm.ViolationType.id, dbm.ViolationType.name, dbm.ViolationType.sort_order)
        .order_by(dbm.ViolationType.sort_order, dbm.ViolationType.name)
    ).all()
    violation_types = [
        FilterOption(value=value, label=label, count=count)
        for value, label, count in violation_type_rows
    ]

    classifications = _option_rows(db, dbm.Pole.classification)
    circuits = _option_rows(db, dbm.Pole.circuit)
    owners = _option_rows(db, dbm.Pole.owner)

    return DashboardFilterOptions(
        severities=[option for option in severities if _matches_search(option, search)],
        classifications=[option for option in classifications if _matches_search(option, search)],
        circuits=[option for option in circuits if _matches_search(option, search)],
        owners=[option for option in owners if _matches_search(option, search)],
        violation_families=[option for option in violation_families if _matches_search(option, search)],
        violation_types=[option for option in violation_types if _matches_search(option, search)],
    )
