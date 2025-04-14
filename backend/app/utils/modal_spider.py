from typing import Dict, Any
import modal

from .modal_manager import ModalFunctionRegistry
from .response import ServiceResponse
from .logger import ServiceLogger

logger = ServiceLogger()
modal_registry = ModalFunctionRegistry()


class ModalSpider:
    """Manager for Modal spider operations."""

    APP_NAME = "markdown-scraper"
    SPIDER_FUNCTION = "spider_master"

    @classmethod
    async def start_job(
        cls, start_url: str, max_urls: int = 10, batch_size: int = 20
    ) -> Dict[str, Any]:
        """Start a new spider job."""
        try:
            spider_func = modal_registry.get_function(
                cls.APP_NAME,
                cls.SPIDER_FUNCTION
            )
            job = spider_func.spawn(
                start_url=start_url, max_urls=max_urls, batch_size=batch_size
            )

            logger.info(
                "spider",
                f"Spider job started with ID: {job.object_id}"
            )

            return ServiceResponse.success(
                {"job_id": str(job.object_id), "status": "started"}
            )
        except Exception as e:
            logger.error("spider", f"Error starting spider job: {str(e)}")
            return ServiceResponse.error(
                message=f"Failed to start spider: {str(e)}",
                error_code="SPIDER_START_ERROR",
            )

    @classmethod
    async def get_status(cls, job_id: str) -> Dict[str, Any]:
        """Get the status of a spider job."""
        logger.info("spider", f"Checking status for job: {job_id}")
        try:
            function_call = modal.FunctionCall.from_id(job_id)
            try:
                function_call.get(timeout=0)
                return ServiceResponse.success({
                    "status": "completed",
                    "progress": 100
                })
            except modal.exception.OutputExpiredError:
                return ServiceResponse.error(
                    message="Job not found", error_code="JOB_NOT_FOUND"
                )
            except TimeoutError:
                return ServiceResponse.in_progress(message="Spider job in progress")
        except Exception as e:
            logger.error("spider", f"Error checking spider status: {str(e)}")
            return ServiceResponse.error(
                message=f"Failed to check spider status: {str(e)}",
                error_code="SPIDER_STATUS_ERROR",
            )
