"""Geography repository (Product layer persistence).

Functions are PostgreSQL-targeted (ON CONFLICT) and idempotent. All inserts
are application-validated BEFORE hitting the DB; the ORM unique constraints are
the final safety net. The scientific `cells` table is only referenced by FK from
`geography_grid_mapping` and never written here.
"""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.database.models import (Block, District, GeographyGridMapping, State,
                                 Village)
from src.geography.constants import GEOGRAPHY_TYPES, HIERARCHY

# entity table per geography type
_MODELS = {
    "state": State,
    "district": District,
    "block": Block,
    "village": Village,
}
_ID_COLS = {
    "state": "state_id",
    "district": "district_id",
    "block": "block_id",
    "village": "village_id",
}

# parent FK column per child type
_PARENT_COL = {
    "district": "state_id",
    "block": "district_id",
    "village": "block_id",
}


class GeographyIntegrityError(ValueError):
    """Raised when geography references are inconsistent (fail loud)."""


def upsert_entity(session: Session, geography_type: str, record: dict) -> None:
    """Idempotently insert/refresh one administrative entity.

    `record` uses the registry vocabulary (geography_id / parent_geography_id);
    this maps it onto the per-type table columns (state_id/district_id/... and
    the parent FK column).
    """
    col = _ID_COLS[geography_type]
    table = _MODELS[geography_type].__table__
    vals: dict = {col: record["geography_id"]}
    for k in ("name", "latitude", "longitude", "geometry_ref", "source",
              "source_version"):
        if k in record and record[k] is not None:
            vals[k] = record[k]
    fk_cols = [c.name for c in table.columns if c.foreign_keys and c.name != "id"]
    if len(fk_cols) == 1 and record.get("parent_geography_id") is not None:
        vals[fk_cols[0]] = record["parent_geography_id"]
    vals = {k: v for k, v in vals.items() if k in table.columns}
    stmt = insert(table).values(**vals).on_conflict_do_update(
        index_elements=[col],
        set_={k: vals[k] for k in vals if k != col},
    )
    session.execute(stmt)


def upsert_mapping(session: Session, record: dict) -> None:
    """Idempotently insert a grid->admin mapping row (ON CONFLICT DO NOTHING)."""
    table = GeographyGridMapping.__table__
    vals = {k: v for k, v in record.items()
            if k in table.columns and k != "id" and v is not None}
    stmt = insert(table).values(**vals).on_conflict_do_nothing(
        index_elements=["grid_cell_id", "geography_type", "geography_id"],
    )
    session.execute(stmt)


def assert_mapping_references(session: Session, record: dict) -> None:
    """Application-layer integrity: mapped geography must exist in its table
    and every mapped grid cell must exist in the scientific cells registry."""
    geo_type = record["geography_type"]
    table = _MODELS[geo_type]
    col = _ID_COLS[geo_type]
    exists = session.execute(
        select(table.id).where(getattr(table, col) == record["geography_id"])
    ).scalar_one_or_none() is not None
    if not exists:
        raise GeographyIntegrityError(
            f"mapping references unknown {geo_type} {record['geography_id']!r}")
    from src.database.models import Cell
    cell_exists = session.execute(
        select(Cell.cell_id).where(Cell.cell_id == record["grid_cell_id"])
    ).scalar_one_or_none() is not None
    if not cell_exists:
        raise GeographyIntegrityError(
            f"mapping references unknown grid cell {record['grid_cell_id']!r}")


def import_boundaries(session: Session, registry) -> dict:
    """Import a GeographyRegistry bundle into the DB in one transaction.

    Idempotent: same bundle -> same rows. Records counts per table.
    """
    ents_by_type = {t: [] for t in GEOGRAPHY_TYPES}
    for level in GEOGRAPHY_TYPES:
        for rec in registry._entities(level):
            ents_by_type[level].append(rec)
    counts = {t: len(recs) for t, recs in ents_by_type.items()}

    for level, recs in ents_by_type.items():
        for rec in recs:
            upsert_entity(session, level, rec)

    inserted = 0
    for rec in registry.mappings():
        mapping = dict(rec)
        assert_mapping_references(session, mapping)
        upsert_mapping(session, mapping)
        inserted += 1

    session.commit()
    return {
        "entities": counts,
        "mappings_inserted": inserted,
        "available": registry.boundaries_available,
    }


# ------------------------------------------------------------------- queries
def _norm_entity(geography_type: str, row: dict) -> dict:
    """Map a DB row onto the registry vocabulary (geography_id / parent)."""
    row = dict(row)
    id_col = _ID_COLS[geography_type]
    parent_col = _PARENT_COL.get(geography_type)
    return {
        "geography_type": geography_type,
        "geography_id": row[id_col],
        "name": row.get("name"),
        "parent_geography_id": row.get(parent_col) if parent_col else None,
        "latitude": row.get("latitude"),
        "longitude": row.get("longitude"),
        "geometry_ref": row.get("geometry_ref"),
        "source": row.get("source"),
        "source_version": row.get("source_version"),
        "agricultural_metadata": row.get("agricultural_metadata"),
    }


def count_geography(session: Session, geography_type: str) -> int:
    return int(session.execute(select(func.count())
                               .select_from(_MODELS[geography_type])).scalar_one())


def count_mappings(session: Session) -> int:
    return int(session.execute(select(func.count())
                               .select_from(GeographyGridMapping)).scalar_one())


def list_geography(session: Session, geography_type: str) -> list[dict]:
    table = _MODELS[geography_type].__table__
    rows = session.execute(
        select(table).order_by(_ID_COLS[geography_type])).mappings()
    return [_norm_entity(geography_type, dict(r)) for r in rows]


def children(session: Session, geography_type: str, geography_id: str) -> list[dict]:
    if geography_type not in HIERARCHY.values():
        return []
    child = next(c for c, parent in HIERARCHY.items() if parent == geography_type)
    child_table = _MODELS[child].__table__
    parent_col = _PARENT_COL[child]
    rows = session.execute(
        select(child_table).where(
            getattr(child_table.c, parent_col) == geography_id)
        .order_by(_ID_COLS[child])).mappings()
    return [_norm_entity(child, dict(r)) for r in rows]


def mappings_for_geography(session: Session, geography_type: str,
                           geography_id: str) -> list[dict]:
    return [dict(r) for r in session.execute(
        select(GeographyGridMapping).where(
            GeographyGridMapping.geography_type == geography_type,
            GeographyGridMapping.geography_id == geography_id)
        .order_by("grid_cell_id")).mappings()]


def mappings_for_cell(session: Session, grid_cell_id: str) -> list[dict]:
    return [dict(r) for r in session.execute(
        select(GeographyGridMapping).where(
            GeographyGridMapping.grid_cell_id == grid_cell_id)
        .order_by("geography_type", "geography_id")).mappings()]


def geography_availability(session: Session) -> dict:
    return {t: count_geography(session, t) for t in GEOGRAPHY_TYPES}