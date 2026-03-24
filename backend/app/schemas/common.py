from typing import Any

from pydantic import BaseModel


class ErrorPayload(BaseModel):
    message: str
    details: Any | None = None


class ApiResponse(BaseModel):
    success: bool
    data: Any | None = None
    error: ErrorPayload | None = None
