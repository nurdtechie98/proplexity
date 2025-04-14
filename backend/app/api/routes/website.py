from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.schemas.website import WebsiteCreate
from app.db.session import get_db
from app.services import website_service


router = APIRouter(prefix="/websites", tags=["websites"])


@router.post("/")
async def create_website(
    website: WebsiteCreate,
    db: Session = Depends(get_db)
):
    """Create a new website entry for tracking and scraping.

    This endpoint registers a new website for periodic scraping and tracking.
    It checks for duplicate entries before creating a new website record.

    Args:
        website (WebsiteCreate): The website creation request containing:
            - url: Website's base URL to track
            - max_urls: Maximum number of URLs to scrape per run
            - scrape_interval_days: Days between scraping runs
        db (Session): Database session dependency injection

    Returns:
        Website: The created website object with:
            - id: Unique identifier
            - url: Website's base URL
            - max_urls: Maximum URLs setting
            - scrape_interval_days: Scraping interval
            - last_scraped_at: Initial scrape timestamp (null)
            - created_at: Creation timestamp

    Raises:
        HTTPException:
            - 400: If website is already registered
    """
    # Check if website already exists
    db_website = website_service.get_website_by_url(db, str(website.url))
    if db_website:
        raise HTTPException(
            status_code=400,
            detail="Website already registered"
        )

    return website_service.create_website(
        db=db,
        url=str(website.url),
        max_urls=website.max_urls,
        scrape_interval_days=website.scrape_interval_days,
    )


@router.get("/")
async def list_websites(db: Session = Depends(get_db)):
    """List all websites being tracked in the system.

    This endpoint retrieves all registered websites and their current
    tracking status.

    Args:
        db (Session): Database session dependency injection

    Returns:
        List[Website]: List of all tracked websites, each containing:
            - id: Unique identifier
            - url: Website's base URL
            - max_urls: Maximum URLs setting
            - scrape_interval_days: Scraping interval
            - last_scraped_at: Last successful scrape timestamp
            - created_at: Registration timestamp
    """
    return website_service.get_all_websites(db)


@router.get("/stale")
async def list_stale_websites(db: Session = Depends(get_db)):
    """List websites that are due for re-scraping based on their interval.

    This endpoint identifies websites that haven't been scraped within their
    configured interval period and need to be updated.

    Args:
        db (Session): Database session dependency injection

    Returns:
        List[Website]: List of stale websites that need re-scraping,
        each containing:
            - id: Unique identifier
            - url: Website's base URL
            - max_urls: Maximum URLs setting
            - scrape_interval_days: Scraping interval
            - last_scraped_at: Last successful scrape timestamp
            - created_at: Registration timestamp
    """
    return website_service.get_stale_websites(db)
