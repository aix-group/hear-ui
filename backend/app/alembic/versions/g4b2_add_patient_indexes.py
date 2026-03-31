"""Add indexes for patient display_name and input_features

Adds:
- btree index on patient.display_name for fast name search/sort
- GIN index on patient.input_features for fast JSON queries (e.g. Geburtsdatum lookup)

Revision ID: g4b2c3d4e5f6
Revises: f3a1b2c3d4e5
Create Date: 2026-03-31

"""

from alembic import op


# revision identifiers, used by Alembic
revision = "g4b2c3d4e5f6"
down_revision = "f3a1b2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "idx_patient_display_name",
        "patient",
        ["display_name"],
        unique=False,
    )
    # Cast json → jsonb to support GIN indexing for fast JSON queries
    op.execute(
        "ALTER TABLE patient ALTER COLUMN input_features TYPE jsonb "
        "USING input_features::text::jsonb"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_patient_input_features "
        "ON patient USING GIN(input_features jsonb_path_ops)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_patient_input_features")
    op.execute(
        "ALTER TABLE patient ALTER COLUMN input_features TYPE json "
        "USING input_features::text::json"
    )
    op.drop_index("idx_patient_display_name", table_name="patient")
