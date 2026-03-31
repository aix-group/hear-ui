import logging

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app import crud
from app.api.deps import SessionDep
from app.models import Feedback, FeedbackCreate

router = APIRouter(prefix="/feedback", tags=["feedback"])
logger = logging.getLogger(__name__)


class PaginatedFeedbackResponse(BaseModel):
    """Paginated response for feedback list."""

    items: list[Feedback]
    total: int
    limit: int
    offset: int
    has_more: bool


@router.get("/")
def list_feedbacks(
    session: SessionDep,
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of feedbacks to return"),
    offset: int = Query(default=0, ge=0, description="Number of feedbacks to skip"),
    paginated: bool = Query(default=False, description="Return paginated response with metadata"),
):
    """List all feedbacks with optional pagination."""
    feedbacks = crud.list_feedback(session=session, limit=limit, offset=offset)

    if paginated:
        total = crud.count_feedback(session=session)
        return PaginatedFeedbackResponse(
            items=feedbacks,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(feedbacks)) < total,
        )

    return feedbacks


@router.post("/", response_model=Feedback, status_code=status.HTTP_201_CREATED)
def create_feedback(feedback_in: FeedbackCreate, session: SessionDep):
    """Create feedback entry in the database. Authentication is disabled in demo mode,
    but current_user is provided for compatibility and auditing later.
    """
    try:
        db_obj = crud.create_feedback(session=session, feedback_in=feedback_in)
        return db_obj
    except Exception:  # pragma: no cover - defensive
        logger.exception("Failed to create feedback")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred. Please try again later.",
        )


@router.get("/{feedback_id}", response_model=Feedback)
def read_feedback(feedback_id: str, session: SessionDep):
    fb = crud.get_feedback(session=session, feedback_id=feedback_id)
    if not fb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Feedback not found"
        )
    return fb
