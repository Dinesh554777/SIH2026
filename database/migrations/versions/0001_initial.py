"""initial schema: cells, model_metadata, forecasts, advisories

Revision ID: 0001
Revises: 
Create Date: 2026-09-12
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def _prob_check(column: str) -> sa.CheckConstraint:
    return sa.CheckConstraint(
        f"{column} >= 0 AND {column} <= 1", name=f"ck_forecasts_{column}_prob")


def upgrade() -> None:
    op.create_table(
        "cells",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("cell_id", sa.String(32), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("state", sa.String(64), nullable=True),
        sa.Column("region", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.UniqueConstraint("cell_id", name="uq_cells_cell_id"),
    )
    op.create_index("ix_cells_cell_id", "cells", ["cell_id"])

    op.create_table(
        "model_metadata",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("model_name", sa.String(32), nullable=False),
        sa.Column("target", sa.String(16), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("feature_group", sa.String(32), nullable=True),
        sa.Column("training_period", sa.String(32), nullable=False),
        sa.Column("validation_period", sa.String(32), nullable=False),
        sa.Column("test_period", sa.String(32), nullable=False),
        sa.Column("artifact_digest", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.UniqueConstraint("model_name", "target", "artifact_digest",
                            name="uq_model_metadata_name_target_digest"),
    )

    op.create_table(
        "forecasts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("cell_id", sa.String(32), nullable=False),
        sa.Column("forecast_date", sa.DateTime(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("onset_probability", sa.Numeric(6, 4), nullable=False),
        sa.Column("break_probability", sa.Numeric(6, 4), nullable=False),
        sa.Column("revival_probability", sa.Numeric(6, 4), nullable=False),
        sa.Column("dry_spell_probability", sa.Numeric(6, 4), nullable=False),
        sa.Column("model_version", sa.String(64), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False,
                  server_default=sa.text("'historical/demo'")),
        sa.ForeignKeyConstraint(["cell_id"], ["cells.cell_id"],
                                name="fk_forecasts_cell_id", ondelete="RESTRICT"),
        sa.UniqueConstraint("cell_id", "forecast_date", "model_version", "mode",
                            name="uq_forecasts_cell_date_version_mode"),
        _prob_check("onset_probability"),
        _prob_check("break_probability"),
        _prob_check("revival_probability"),
        _prob_check("dry_spell_probability"),
    )
    op.create_index("ix_forecasts_cell_date", "forecasts", ["cell_id", "forecast_date"])
    op.create_index("ix_forecasts_date", "forecasts", ["forecast_date"])

    op.create_table(
        "advisories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("forecast_id", sa.Integer(), nullable=False),
        sa.Column("advisory_type", sa.String(32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("language", sa.String(8), nullable=False,
                  server_default=sa.text("'en'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["forecast_id"], ["forecasts.id"],
                                name="fk_advisories_forecast_id", ondelete="CASCADE"),
        sa.UniqueConstraint("forecast_id", "advisory_type", "message",
                            name="uq_advisories_forecast_type_message"),
        sa.CheckConstraint("advisory_type IN ('summary', 'card')",
                           name="ck_advisories_type"),
    )
    op.create_index("ix_advisories_forecast", "advisories", ["forecast_id"])


def downgrade() -> None:
    op.drop_table("advisories")
    op.drop_table("forecasts")
    op.drop_table("model_metadata")
    op.drop_table("cells")