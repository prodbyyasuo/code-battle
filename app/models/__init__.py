"""SQLAlchemy models registered in the shared metadata."""

from app.db.base import Base
from app.models.problem import Problem
from app.models.submission import Submission
from app.models.submission_case import SubmissionCase
from app.models.user import User

__all__ = [
    "Base",
    "Problem",
    "Submission",
    "SubmissionCase",
    "User",
]
