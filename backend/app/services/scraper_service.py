from datetime import datetime
from typing import Dict, Any
from sqlalchemy.orm import Session

from ..utils.response import ServiceResponse
from ..utils.modal_spider import ModalSpider
from ..utils.logger import ServiceLogger
from ..models.schemas.website import WebsiteCreate
from ..services.website_service import (
    get_website_by_url,
    create_website,
    update_last_scraped
)

logger = ServiceLogger()


async def start_spider(
    db: Session,
    start_url: str,
    max_urls: int = 10,
    batch_size: int = 20
) -> Dict[str, Any]:
    """
    Start a spider scraping job using Modal's spider_master function.
    Creates or updates website entry in database.
    """
    logger.info("scraper", f"Starting spider for URL: {start_url}")

    try:
        website = get_website_by_url(db, start_url)

        if website:
            logger.info(
                "scraper",
                f"Updating existing website: {start_url}"
            )
            update_result = update_last_scraped(db, website.id)
            if update_result["status"] == "error":
                return update_result
        else:
            logger.info(
                "scraper",
                f"Creating new website: {start_url}"
            )
            website_data = WebsiteCreate(
                url=start_url,
                max_urls=max_urls,
                scrape_interval_days=7
            )
            create_result = create_website(
                db=db,
                url=start_url,
                max_urls=website_data.max_urls,
                scrape_interval_days=website_data.scrape_interval_days,
                last_scraped_at=datetime.utcnow()
            )
            if create_result["status"] == "error":
                return create_result

        return await ModalSpider.start_job(
            start_url=start_url,
            max_urls=max_urls,
            batch_size=batch_size
        )

    except Exception as e:
        logger.error("scraper", f"Error starting spider: {str(e)}")
        return ServiceResponse.error(
            message=f"Failed to start spider: {str(e)}",
            error_code="SPIDER_START_ERROR"
        )


async def get_spider_status(job_id: str) -> Dict[str, Any]:
    """Get the status of a spider scraping job."""
    return await ModalSpider.get_status(job_id)
