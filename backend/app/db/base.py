# Import all SQLModel table classes so Alembic's target_metadata
# includes them for migration autogeneration.

from sqlmodel import SQLModel  # noqa: F401

from app.models.feedback import Feedback  # noqa: F401
from app.models.patient_record import Patient  # noqa: F401
from app.models.prediction import Prediction  # noqa: F401
