"""product decision-support layer: risk_assessments, agri_context, deliveries, monsoon events

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-13

Adds traceability tables for the agricultural decision engine (master build
prompt sections 18-19). Structure only - demo data is seeded by scripts, never
inside migrations.
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

_DECISIONS = "'SOW', 'WAIT', 'MONITOR', 'PREPARE', 'IRRIGATION_PREPARE'"
_LOC_TYPES = "'state', 'district', 'block', 'village', 'cell'"
_RISKS = "'low', 'medium', 'high'"


def upgrade() -> None:
    op.create_table(
        "risk_assessments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("forecast_id", sa.Integer(), nullable=True),
        sa.Column("location_type", sa.String(16), nullable=False),
        sa.Column("location_id", sa.String(64), nullable=False),
        sa.Column("cell_id", sa.String(32), nullable=True),
        sa.Column("decision", sa.String(24), nullable=False),
        sa.Column("confidence", sa.String(8), nullable=False, server_default="medium"),
        sa.Column("monsoon_status", sa.String(24), nullable=False),
        sa.Column("false_onset_risk", sa.String(8), nullable=False),
        sa.Column("onset_probability", sa.Numeric(6, 4), nullable=False),
        sa.Column("dry_spell_probability", sa.Numeric(6, 4), nullable=False),
        sa.Column("break_probability", sa.Numeric(6, 4), nullable=False),
        sa.Column("risk_summary", sa.JSON(), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("thresholds_version", sa.String(16), nullable=False),
        sa.Column("mode", sa.String(32), nullable=False, server_default="prototype/demo"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.CheckConstraint(f"decision IN ({_DECISIONS})", name="ck_risk_assessments_decision"),
        sa.CheckConstraint(f"location_type IN ({_LOC_TYPES})",
                           name="ck_risk_assessments_location_type"),
        sa.CheckConstraint(f"false_onset_risk IN ({_RISKS})",
                           name="ck_risk_assessments_false_onset_risk"),
        sa.ForeignKeyConstraint(["forecast_id"], ["forecasts.id"],
                                name="fk_risk_assessments_forecast", ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cell_id"], ["cells.cell_id"],
                                name="fk_risk_assessments_cell", ondelete="RESTRICT"),
    )
    op.create_index("ix_risk_assessments_loc_time", "risk_assessments",
                    ["location_type", "location_id", "created_at"])
    op.create_index("ix_risk_assessments_forecast", "risk_assessments", ["forecast_id"])

    op.create_table(
        "agricultural_context",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("location_type", sa.String(16), nullable=False),
        sa.Column("location_id", sa.String(64), nullable=False),
        sa.Column("crop", sa.String(32), nullable=False),
        sa.Column("season", sa.String(16), nullable=False),
        sa.Column("sowing_window_start", sa.String(16), nullable=False),
        sa.Column("sowing_window_end", sa.String(16), nullable=False),
        sa.Column("sow_confidence_needed", sa.Numeric(4, 2), nullable=False),
        sa.Column("dry_spell_sensitivity", sa.String(16), nullable=False),
        sa.Column("irrigation_availability", sa.String(32), nullable=False),
        sa.Column("rainfall_requirement_mm", sa.Float(), nullable=True),
        sa.Column("soil", sa.String(32), nullable=True),
        sa.Column("source", sa.String(64), nullable=False, server_default="demo/prototype"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.CheckConstraint(f"location_type IN ({_LOC_TYPES})",
                           name="ck_agri_ctx_location_type"),
        sa.UniqueConstraint("location_type", "location_id", "crop", "season",
                            name="uq_agri_ctx_loc_crop_season"),
    )

    op.create_table(
        "advisory_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("risk_assessment_id", sa.Integer(), nullable=False),
        sa.Column("location_type", sa.String(16), nullable=False),
        sa.Column("location_id", sa.String(64), nullable=False),
        sa.Column("decision", sa.String(24), nullable=False),
        sa.Column("channel", sa.String(24), nullable=False),
        sa.Column("language", sa.String(8), nullable=False, server_default="en"),
        sa.Column("status", sa.String(16), nullable=False, server_default="generated"),
        sa.Column("recipient_scope", sa.String(64), nullable=True),
        sa.Column("issued_by", sa.String(64), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("mock_notice", sa.Text(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.CheckConstraint(
            "channel IN ('field_worker', 'panchayat', 'notice_print', 'sms', "
            "'ivr', 'whatsapp', 'fpo')",
            name="ck_advisory_deliveries_channel"),
        sa.CheckConstraint("language IN ('en', 'ta', 'en,ta')",
                           name="ck_advisory_deliveries_language"),
        sa.CheckConstraint("status IN ('generated', 'sent', 'failed', 'pending')",
                           name="ck_advisory_deliveries_status"),
        sa.ForeignKeyConstraint(["risk_assessment_id"], ["risk_assessments.id"],
                                name="fk_advisory_deliveries_risk", ondelete="CASCADE"),
    )
    op.create_index("ix_advisory_deliveries_risk", "advisory_deliveries",
                    ["risk_assessment_id"])
    op.create_index("ix_advisory_deliveries_loc_time", "advisory_deliveries",
                    ["location_type", "location_id", "created_at"])

    op.create_table(
        "monsoon_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("location_type", sa.String(16), nullable=False),
        sa.Column("location_id", sa.String(64), nullable=False),
        sa.Column("cell_id", sa.String(32), nullable=True),
        sa.Column("event_type", sa.String(16), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=False), nullable=False),
        sa.Column("end_date", sa.DateTime(timezone=False), nullable=True),
        sa.Column("risk_level", sa.String(8), nullable=False, server_default="medium"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("source", sa.String(64), nullable=False, server_default="decision-engine"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.CheckConstraint(
            "event_type IN ('onset', 'false_onset', 'dry_spell', 'break', 'recovery')",
            name="ck_monsoon_events_type"),
        sa.CheckConstraint(f"location_type IN ({_LOC_TYPES})",
                           name="ck_monsoon_events_location_type"),
        sa.ForeignKeyConstraint(["cell_id"], ["cells.cell_id"],
                                name="fk_monsoon_events_cell", ondelete="RESTRICT"),
    )
    op.create_index("ix_monsoon_events_loc_time", "monsoon_events",
                    ["location_type", "location_id", "start_date"])


def downgrade() -> None:
    op.drop_table("monsoon_events")
    op.drop_table("advisory_deliveries")
    op.drop_table("agricultural_context")
    op.drop_table("risk_assessments")