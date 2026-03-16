from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class FeedbackBase(SQLModel):
    input_features: dict[str, Any] | None = Field(
        default=None, sa_column=sa.Column(sa.JSON())
    )
    prediction: float | None = None
    explanation: dict[str, Any] | None = Field(
        default=None, sa_column=sa.Column(sa.JSON())
    )
    accepted: bool | None = None
    comment: str | None = None
    rating: int | None = Field(default=None, ge=1, le=5, description="Rating from 1-5")


class Feedback(FeedbackBase, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FeedbackCreate(FeedbackBase):
    pass
