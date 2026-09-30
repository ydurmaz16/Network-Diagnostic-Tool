"""Application-level errors that are safe to show to the user."""


class DiagnosticError(Exception):
    """An expected failure with a user-friendly message."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
