from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db

from app.services.scraper_service import (
    start_spider,
    get_spider_status
)
from app.models.schemas.scraper import (
    SpiderStartResponse,
    SpiderStatusResponse,
    SpiderStartRequest,
)

router = APIRouter(prefix="/scraper", tags=["scraper"])


@router.post("/spider/start", response_model=SpiderStartResponse)
async def post_start_spider(
    request: SpiderStartRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Start a new spider job to crawl and index website content.

    This endpoint initiates a new spider crawling job with the specified
    parameters.
    The spider will crawl the website starting from the given URL, respecting
    the maximum URL limit and batch size constraints.

    Args:
        request (SpiderStartRequest): The request object containing:
            - start_url: Initial URL to start crawling from
            - max_urls: Maximum number of URLs to crawl
            - batch_size: Number of URLs to process in each batch
        db (Session): Database session dependency injection

    Returns:
        Dict[str, Any]: A dictionary containing:
            - job_id: Unique identifier for the spider job
            - status: Current status of the job ("started")

    Raises:
        HTTPException: If there's an error starting the spider job
            - 500: Internal server error with error details
    """
    try:
        return await start_spider(
            db=db,
            start_url=request.start_url,
            max_urls=request.max_urls,
            batch_size=request.batch_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/spider/{job_id}/status", response_model=SpiderStatusResponse)
async def get_spider_status_route(
    job_id: str
) -> Dict[str, Any]:
    """Get the current status of a running or completed spider job.

    This endpoint retrieves the current status of a spider job using its ID.
    It provides information about the job's progress, including the number
    of URLs processed and any errors that may have occurred.

    Args:
        job_id (str): The unique identifier of the spider job

    Returns:
        Dict[str, Any]: A dictionary containing:
            - status: Current status of the job
                ("running", "completed", "failed")
            - progress: Optional progress information (URLs processed)
            - error: Optional error message if the job failed

    Raises:
        HTTPException: If there's an error retrieving the job status
            - 500: Internal server error with error details
    """
    try:
        return await get_spider_status(job_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
