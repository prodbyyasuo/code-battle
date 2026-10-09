"""Enums shared by persistence, service, and API layers."""

from enum import StrEnum


class UserRole(StrEnum):
    """Roles controlling access to administrative operations."""

    USER = "user"
    ADMIN = "admin"


class ProblemDifficulty(StrEnum):
    """Difficulty displayed in the problem catalogue."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class SubmissionStatus(StrEnum):
    """Lifecycle states of a submitted solution."""

    QUEUED = "queued"
    RUNNING = "running"
    ACCEPTED = "accepted"
    WRONG_ANSWER = "wrong_answer"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"
    MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"
    RUNTIME_ERROR = "runtime_error"
    SYSTEM_ERROR = "system_error"


class SubmissionCaseVerdict(StrEnum):
    """Verdict for one test case in a submission."""

    PASSED = "passed"
    WRONG_ANSWER = "wrong_answer"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"
    MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"
    RUNTIME_ERROR = "runtime_error"
    SYSTEM_ERROR = "system_error"
    SKIPPED = "skipped"
