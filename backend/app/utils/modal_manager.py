from typing import Optional, Dict, Any
import modal
from functools import lru_cache


class ModalFunctionRegistry:
    """Centralized registry for Modal functions."""

    _functions: Dict[str, modal.Function] = {}

    @classmethod
    def register(
        cls,
        app_name: str,
        function_name: str,
        function: Optional[modal.Function] = None,
    ) -> None:
        """Register a Modal function."""
        key = f"{app_name}:{function_name}"
        if function:
            cls._functions[key] = function

    @classmethod
    @lru_cache(maxsize=None)
    def get_function(cls, app_name: str, function_name: str) -> modal.Function:
        """Get a Modal function by app and function name."""
        key = f"{app_name}:{function_name}"
        if key not in cls._functions:
            cls._functions[key] = modal.Function.from_name(
                app_name,
                function_name
            )
        return cls._functions[key]

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the function cache."""
        cls._functions.clear()
        cls.get_function.cache_clear()


class ModalJobManager:
    """Manager for Modal job operations."""

    @staticmethod
    async def get_job_status(job_id: str) -> Dict[str, Any]:
        """Get the status of a Modal job."""
        function_call = modal.FunctionCall.from_id(job_id)
        try:
            function_call.get(timeout=0)
            return {"status": "completed", "progress": 100}
        except modal.exception.OutputExpiredError:
            return {"status": "failed", "error": "Job not found"}
        except TimeoutError:
            return {"status": "in_progress", "progress": None}
