"""Geography domain tests (offline, no database).

Covers the §16 checklist: hierarchy, mapping, integrity, determinism,
existing-scientific-grid compatibility, scientific separation, and the
no-fabrication rule (missing boundaries -> explicit unavailable).

Boundaries used here are SYNTHETIC test fixtures only (prefixed FIXTURE-*),
never real administrative data, so nothing is implied about actual geography.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.geography.agriculture import AgricultureError
from src.geography.mapper import map_grid_to_admin
from src.geography.registry import GeographyRegistry
from src.serving.registry import default_registry

MATRIX = Path(__file__).resolve().parents[1] / "data" / "processed" / "phase_h_matrix.parquet"

FROZEN_MATRIX_DIGEST = "a87c5d239f7a6b9a"
FROZEN_FREEZE_DIGEST = "4f122044f8710b53"


@pytest.fixture(scope="session")
def cells() -> pd.DataFrame:
    matrix = pd.read_parquet(MATRIX)
    return default_registry(matrix).cells


def _seam_lon(cells: pd.DataFrame) -> float:
    lons = sorted(float(v) for v in cells["lon"].unique())
    return min(lons, key=lambda v: abs(v - 78.0))


def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


def _state_polygon() -> dict:
    return {"type": "Polygon",
            "coordinates": [[[76.5, 8.0], [80.5, 8.0], [80.5, 13.5],
                             [76.5, 13.5], [76.5, 8.0]]]}


def _block_a(seam: float) -> dict:
    return {"type": "Polygon",
            "coordinates": [[[76.5, 8.0], [seam, 8.0], [seam, 13.5],
                             [76.5, 13.5], [76.5, 8.0]]]}


def _block_b(seam: float) -> dict:
    return {"type": "Polygon",
            "coordinates": [[[seam, 8.0], [80.5, 8.0], [80.5, 13.5],
                             [seam, 13.5], [seam, 8.0]]]}


def _meta():
    return {
        "dataset_name": "FIXTURE-boundaries",
        "provider": "FIXTURE-provider",
        "version": "0.0.1-fixture",
        "release_date": "2026-01-01",
        "resolution": "synthetic",
        "license": "fixture-only",
        "url": "https://example.invalid/fixture",
        "crs": "EPSG:4326",
        "geometry_quality": "synthetic-test-ground-truth",
    }


def make_ready_bundle(dirpath: Path, cells: pd.DataFrame) -> Path:
    """Build a synthetic state+district+block bundle and return ready_root."""
    ready = dirpath / "ready"
    ready.mkdir(parents=True, exist_ok=True)
    _write_json(ready / "source.json", _meta())

    seam = _seam_lon(cells)
    _write_json(ready / "state.geojson", {
        "type": "FeatureCollection",
        "features": [{"type": "Feature",
                      "properties": {"level": "state", "id": "FIXTURE-ST",
                                     "name": "FIXTURE State", "parent_id": None},
                      "geometry": _state_polygon()}]})
    _write_json(ready / "district.geojson", {
        "type": "FeatureCollection",
        "features": [{"type": "Feature",
                      "properties": {"level": "district", "id": "FIXTURE-D1",
                                     "name": "FIXTURE District",
                                     "parent_id": "FIXTURE-ST"},
                      "geometry": _state_polygon()}]})
    _write_json(ready / "block.geojson", {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature",
             "properties": {"level": "block", "id": "FIXTURE-BA",
                            "name": "FIXTURE Block A", "parent_id": "FIXTURE-D1"},
             "geometry": _block_a(seam)},
            {"type": "Feature",
             "properties": {"level": "block", "id": "FIXTURE-BB",
                            "name": "FIXTURE Block B", "parent_id": "FIXTURE-D1"},
             "geometry": _block_b(seam)},
        ]})
    return ready


@pytest.fixture()
def empty_registry(tmp_path, cells):
    root = tmp_path / "sources"
    root.mkdir(exist_ok=True)
    return GeographyRegistry(source_root=root, ready_root=tmp_path / "ready",
                             agri_root=tmp_path / "agri", cells=cells)


@pytest.fixture()
def ready_registry(tmp_path, cells):
    ready = make_ready_bundle(tmp_path, cells)
    return GeographyRegistry(source_root=tmp_path / "sources",
                             ready_root=ready, agri_root=tmp_path / "agri",
                             cells=cells)


# ---------------------------------------------------------------- hierarchy
def test_registry_without_sources_is_unavailable(empty_registry):
    a = empty_registry.availability()
    assert a["status"] == "unavailable"
    assert all(v == "unavailable" for v in a["levels"].values())
    assert empty_registry.states() == []
    assert empty_registry.districts() == []
    assert empty_registry.blocks() == []
    assert empty_registry.villages() == []
    assert empty_registry.mappings() == []
    assert empty_registry.unavailable_reason()  # explicit, non-empty


def test_hierarchy_state_district_block(ready_registry, cells):
    states = ready_registry.states()
    assert [s["geography_id"] for s in states] == ["FIXTURE-ST"]
    state_id = states[0]["geography_id"]

    districts = ready_registry.districts(state_id)
    assert [d["geography_id"] for d in districts] == ["FIXTURE-D1"]
    assert districts[0]["parent_geography_id"] == state_id

    blocks = ready_registry.blocks(districts[0]["geography_id"])
    assert [b["geography_id"] for b in blocks] == ["FIXTURE-BA", "FIXTURE-BB"]
    assert all(b["parent_geography_id"] == "FIXTURE-D1" for b in blocks)

    # children() navigation
    child_blocks = ready_registry.children("district", "FIXTURE-D1")
    assert child_blocks == blocks


def test_ready_bundle_keeps_grid_untouched(ready_registry):
    assert ready_registry.n_grid_cells == 304
    ids = {c["grid_cell_id"] for c in ready_registry.grid_cells()}
    assert len(ids) == 304
    assert all("_" in cid and float(cid.split("_")[0]) for cid in ids)


# ---------------------------------------------------------------- mapping
def test_mapping_only_references_real_cells(ready_registry, cells):
    valid = set(cells["cell_id"])
    maps = ready_registry.mappings()
    assert maps
    for m in maps:
        assert m["grid_cell_id"] in valid
        assert 0.0 < m["intersection_fraction"] <= 1.0
        assert m["mapping_method"] == "area_weighted_intersection"


def test_mapping_conservation_within_cell(ready_registry):
    per_cell = {}
    for m in ready_registry.mappings():
        per_cell.setdefault(m["grid_cell_id"], 0.0)
        per_cell[m["grid_cell_id"]] += m["intersection_fraction"]
    for cid, total in per_cell.items():
        assert total <= 1.0 + 1e-9, f"cell {cid} overstated coverage {total}"


def test_cell_spanning_two_blocks_splits_deterministically(ready_registry, cells):
    seam = _seam_lon(cells)
    split_cells = [c for c in ready_registry.grid_cells()
                   if abs(float(c["longitude"]) - seam) < 0.126]
    assert split_cells, "seam must bisect at least one cell"
    per_cell = {}
    for m in ready_registry.mappings():
        per_cell.setdefault(m["grid_cell_id"], []).append(m)

    # an interior, fully-cut cell is bisected into two equal halves
    candidates = [c["grid_cell_id"] for c in ready_registry.grid_cells()
                  if abs(float(c["longitude"]) - seam) < 1e-9
                  and 8.5 < float(c["latitude"]) < 13.0]
    assert candidates
    interior = candidates[0]
    per = per_cell[interior]
    assert sorted(m["geography_id"] for m in per) == ["FIXTURE-BA", "FIXTURE-BB"]
    total = sum(m["intersection_fraction"] for m in per)
    assert total == pytest.approx(1.0, abs=1e-9)
    assert abs(per[0]["intersection_fraction"] - 0.5) < 1e-9

    # cells on the cut are mapped to exactly both blocks, never more
    for c in split_cells:
        ms = per_cell.get(c["grid_cell_id"], [])
        geos = sorted(m["geography_id"] for m in ms)
        assert geos in (["FIXTURE-BA", "FIXTURE-BB"],), c["grid_cell_id"]
        assert sum(m["intersection_fraction"] for m in ms) <= 1.0 + 1e-9


def test_mapping_determinism(ready_registry, tmp_path, cells):
    m1 = ready_registry.mappings()
    reg2 = GeographyRegistry(source_root=tmp_path / "sources",
                             ready_root=ready_registry.ready_root,
                             agri_root=tmp_path / "agri", cells=cells)
    m2 = reg2.mappings()
    assert m1 == m2
    assert reg2.states() == ready_registry.states()


def test_invalid_ready_bundle_refused_and_unavailable(tmp_path, cells):
    ready = tmp_path / "ready"
    ready.mkdir(parents=True, exist_ok=True)
    _write_json(ready / "source.json", _meta())
    # bundle defines a district level that does NOT contain the block's parent
    _write_json(ready / "district.geojson", {
        "type": "FeatureCollection",
        "features": [{"type": "Feature",
                      "properties": {"level": "district", "id": "FIXTURE-OTHER",
                                     "name": "kept district",
                                     "parent_id": "FIXTURE-ST"},
                      "geometry": _block_a(77.0)}]})
    _write_json(ready / "bad.geojson", {
        "type": "FeatureCollection",
        "features": [{"type": "Feature",
                      "properties": {"level": "block", "id": "X",
                                     "name": "orphan", "parent_id": "NOPE"},
                      "geometry": _block_a(77.0)}]})
    reg = GeographyRegistry(source_root=tmp_path / "sources", ready_root=ready,
                            cells=cells)
    assert reg.boundaries_available is False
    assert reg.availability()["status"] == "unavailable"
    assert reg.mappings() == []
    assert reg.states() == []


def test_source_without_metadata_is_refused_not_loaded(tmp_path, cells):
    src = tmp_path / "sources"
    (src / "mystery").mkdir(parents=True, exist_ok=True)
    _write_json(src / "mystery" / "ghost.geojson",
                {"features": []})
    reg = GeographyRegistry(source_root=src, ready_root=tmp_path / "noready",
                            cells=cells)
    assert reg.boundaries_available is False
    assert len(reg.refused) == 1
    assert "source.json" in reg.unavailable_reason()


# ------------------------------------------------------- scientific integrity
def test_frozen_matrix_and_freeze_digests_unchanged():
    assert hashlib.sha256(
        MATRIX.read_bytes()).hexdigest()[:16] == FROZEN_MATRIX_DIGEST
    freeze = Path(__file__).resolve().parents[1] / "data" / "processed" / "FREEZE_H.json"
    assert hashlib.sha256(freeze.read_bytes()).hexdigest()[:16] == FROZEN_FREEZE_DIGEST


def test_mapping_does_not_write_any_artifact(ready_registry):
    # mapping is read-only over the cells frame; no product data file created
    before = set(Path("data").rglob("*")) if Path("data").exists() else set()
    _ = ready_registry.mappings()
    _ = map_grid_to_admin(ready_registry.cells, ready_registry.boundaries,
                          source="s", version="v")
    after = set(Path("data").rglob("*"))
    assert before == after


# ------------------------------------------------------------- no fabrication
def test_no_fabricated_grid_cells(ready_registry):
    for c in ready_registry.grid_cells():
        assert c["note"].startswith("scientific")
        assert c["grid_cell_id"] in set(ready_registry.cells["cell_id"])


def test_coverage_report_surfaces_unmapped_cells(ready_registry, cells):
    cov = ready_registry.coverage()
    assert cov["status"] == "available"
    unmapped = set(cov["unmapped_cells"])
    interior = set(cells["cell_id"]) - unmapped
    assert interior  # at least some cells fall inside the fixture polygons
    # no fabricated mapping: unmapped cells have zero coverage
    assert not any(m["grid_cell_id"] in unmapped for m in ready_registry.mappings())


# -------------------------------------------------------------- agriculture
def test_agriculture_unavailable_by_default(empty_registry):
    prof = empty_registry.agriculture("block", "FIXTURE-BA")
    assert prof["availability"] == "unavailable"
    assert prof["fields"] == {}
    assert prof["source"] is None


def test_agriculture_profile_loads_only_authoritative(tmp_path, cells):
    agri = tmp_path / "agri"
    agri.mkdir(exist_ok=True)
    (agri / "FIXTURE-BA.json").write_text(json.dumps({
        "source": "FIXTURE-agri-provider",
        "major_crop": "paddy",
        "cropping_season": "kharif",
        "irrigation_dependence": "delta-canals",
    }), encoding="utf-8")
    reg = GeographyRegistry(source_root=tmp_path / "no-sources",
                            ready_root=tmp_path / "no-ready",
                            agri_root=agri, cells=cells)
    prof = reg.agriculture("block", "FIXTURE-BA")
    assert prof["availability"] == "available"
    assert prof["fields"]["major_crop"] == "paddy"
    assert prof["source"] == "FIXTURE-agri-provider"


def test_agriculture_profile_rejects_unknown_fields(tmp_path, cells):
    agri = tmp_path / "agri"
    agri.mkdir(exist_ok=True)
    (agri / "BAD.json").write_text(json.dumps({
        "source": "x", "invented_value": 42,
    }), encoding="utf-8")
    reg = GeographyRegistry(source_root=tmp_path / "s", ready_root=tmp_path / "r",
                            agri_root=agri, cells=cells)
    with pytest.raises(AgricultureError):
        reg.agriculture("block", "BAD")


def test_agriculture_profile_rejects_blank_values(tmp_path, cells):
    agri = tmp_path / "agri"
    agri.mkdir(exist_ok=True)
    (agri / "B.json").write_text(json.dumps({
        "source": "x", "major_crop": " ",
    }), encoding="utf-8")
    reg = GeographyRegistry(source_root=tmp_path / "s", ready_root=tmp_path / "r",
                            agri_root=agri, cells=cells)
    with pytest.raises(AgricultureError):
        reg.agriculture("block", "B")


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))