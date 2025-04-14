from typing import Any, Optional, Dict
from fastapi import status
from pydantic import BaseModel


class ServiceResponseModel(BaseModel):
    status: str
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error_code: Optional[str] = None
    progress: Optional[float] = None


class ServiceResponse:
    """Standardized service response utility."""

    @staticmethod
    def success(
        data: Any,
        status_code: int = status.HTTP_200_OK
    ) -> Dict[str, Any]:
        """Create a success response."""
        return ServiceResponseModel(status="success", data=data).model_dump()

    @staticmethod
    def error(
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        error_code: Optional[str] = None,
        data: Any = None,
    ) -> Dict[str, Any]:
        """Create an error response."""
        return ServiceResponseModel(
            status="error", message=message, error_code=error_code, data=data
        ).model_dump()

    @staticmethod
    def in_progress(
        message: str = "Task in progress", progress: Optional[float] = None
    ) -> Dict[str, Any]:
        """Create an in-progress response."""
        return ServiceResponseModel(
            status="in_progress", message=message, progress=progress
        ).model_dump()
