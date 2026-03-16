from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class PatientBase(SQLModel):
    """Store the raw input features for a patient as JSON."""

    input_features: dict[str, Any] | None = Field(
        default=None, sa_column=sa.Column(sa.JSON())
    )
    # a denormalized, searchable display name for faster DB-side searches
    # NOTE: SQLModel Field does not allow `index=True` together with `sa_column`.
    # The index is created explicitly in the Alembic migration.
    display_name: str | None = Field(default=None, sa_column=sa.Column(sa.String()))


class Patient(PatientBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = Field(default=None)


class PatientCreate(PatientBase):
    pass


class PatientUpdate(SQLModel):
    """Model for updating patient data (all fields optional)."""

    input_features: dict[str, Any] | None = None
    display_name: str | None = None
