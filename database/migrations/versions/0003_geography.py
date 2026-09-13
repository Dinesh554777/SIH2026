"""administrative geography tables + grid->admin mapping (Product layer)

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-12

Extends the schema WITHOUT touching the scientific `cells` registry or any
Phase I-B / J2 table. Geography rows are ONLY populated by the authoritative
GIS import (src.geography) -- this migration creates structure, no data.
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "states",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("state_id", sa.String(16), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("geometry_ref", sa.String(256), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_version", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.UniqueConstraint("state_id", name="uq_states_state_id"),
    )
    op.create_index("ix_states_state_id", "states", ["state_id"])

    op.create_table(
        "districts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("district_id", sa.String(24), nullable=False),
        sa.Column("state_id", sa.String(16), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("geometry_ref", sa.String(256), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_version", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["state_id"], ["states.state_id"],
                                name="fk_districts_state_id", ondelete="RESTRICT"),
        sa.UniqueConstraint("district_id", name="uq_districts_district_id"),
    )
    op.create_index("ix_districts_state", "districts", ["state_id"])

    op.create_table(
        "blocks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("block_id", sa.String(32), nullable=False),
        sa.Column("district_id", sa.String(24), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("agricultural_metadata", sa.JSON(), nullable=True),
        sa.Column("geometry_ref", sa.String(256), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_version", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["district_id"], ["districts.district_id"],
                                name="fk_blocks_district_id", ondelete="RESTRICT"),
        sa.UniqueConstraint("block_id", name="uq_blocks_block_id"),
    )
    op.create_index("ix_blocks_district", "blocks", ["district_id"])

    op.create_table(
        "villages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("village_id", sa.String(32), nullable=False),
        sa.Column("block_id", sa.String(32), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("agricultural_metadata", sa.JSON(), nullable=True),
        sa.Column("geometry_ref", sa.String(256), nullable=True),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("source_version", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["block_id"], ["blocks.block_id"],
                                name="fk_villages_block_id", ondelete="RESTRICT"),
        sa.UniqueConstraint("village_id", name="uq_villages_village_id"),
    )
    op.create_index("ix_villages_block", "villages", ["block_id"])

    op.create_table(
        "geography_grid_mapping",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("grid_cell_id", sa.String(32), nullable=False),
        sa.Column("geography_type", sa.String(16), nullable=False),
        sa.Column("geography_id", sa.String(32), nullable=False),
        sa.Column("intersection_fraction", sa.Float(), nullable=False),
        sa.Column("mapping_method", sa.String(48), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("version", sa.String(32), nullable=False),
        sa.Column("cell_area_deg2", sa.Float(), nullable=True),
        sa.Column("intersection_area_deg2", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["grid_cell_id"], ["cells.cell_id"],
                                name="fk_geography_mapping_cell_id",
                                ondelete="RESTRICT"),
        sa.UniqueConstraint("grid_cell_id", "geography_type", "geography_id",
                            name="uq_geography_grid_mapping_cell_type_geo"),
        sa.CheckConstraint(
            "geography_type IN ('state', 'district', 'block', 'village')",
            name="ck_geography_grid_mapping_type"),
        sa.CheckConstraint(
            "intersection_fraction >= 0 AND intersection_fraction <= 1",
            name="ck_geography_grid_mapping_fraction"),
    )
    op.create_index("ix_geography_grid_mapping_geo",
                    "geography_grid_mapping", ["geography_type", "geography_id"])
    op.create_index("ix_geography_grid_mapping_cell",
                    "geography_grid_mapping", ["grid_cell_id"])


def downgrade() -> None:
    op.drop_table("geography_grid_mapping")
    op.drop_table("villages")
    op.drop_table("blocks")
    op.drop_table("districts")
    op.drop_table("states")