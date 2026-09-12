"""live observation persistence: observations, ingestion_runs

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

OBSERVATION_QUALITIES = ("valid", "missing", "invalid", "stale", "future")
RUN_STATUSES = ("RUNNING", "SUCCESS", "PARTIAL", "FAILED", "BLOCKED")


def upgrade() -> None:
    op.create_table(
        "observations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("cell_id", sa.String(32), nullable=False),
        sa.Column("observation_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("rainfall_mm_day", sa.Float(), nullable=False),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("quality_flag", sa.String(16), nullable=False,
                  server_default=sa.text("'valid'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["cell_id"], ["cells.cell_id"],
                                name="fk_observations_cell_id", ondelete="RESTRICT"),
        sa.UniqueConstraint("cell_id", "observation_time", "source",
                            name="uq_observations_cell_time_source"),
        sa.CheckConstraint("rainfall_mm_day >= 0",
                           name="ck_observations_rainfall_nonnegative"),
        sa.CheckConstraint(
            "quality_flag IN ('valid', 'missing', 'invalid', 'stale', 'future')",
            name="ck_observations_quality_flag"),
    )
    op.create_index("ix_observations_cell_time", "observations",
                    ["cell_id", "observation_time"])
    op.create_index("ix_observations_time", "observations", ["observation_time"])
    op.create_index("ix_observations_source", "observations", ["source"])

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("source", sa.String(32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(16), nullable=False,
                  server_default=sa.text("'RUNNING'")),
        sa.Column("rows_received", sa.Integer(), nullable=False,
                  server_default=sa.text("0")),
        sa.Column("rows_inserted", sa.Integer(), nullable=False,
                  server_default=sa.text("0")),
        sa.Column("rows_rejected", sa.Integer(), nullable=False,
                  server_default=sa.text("0")),
        sa.Column("error_type", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.CheckConstraint(
            "status IN ('RUNNING', 'SUCCESS', 'PARTIAL', 'FAILED', 'BLOCKED')",
            name="ck_ingestion_runs_status"),
    )
    op.create_index("ix_ingestion_runs_started_at", "ingestion_runs", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_ingestion_runs_started_at", table_name="ingestion_runs")
    op.drop_table("ingestion_runs")
    op.drop_index("ix_observations_source", table_name="observations")
    op.drop_index("ix_observations_time", table_name="observations")
    op.drop_index("ix_observations_cell_time", table_name="observations")
    op.drop_table("observations")