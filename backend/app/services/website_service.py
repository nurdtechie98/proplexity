from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.website import Website
from app.core.config import settings
from app.utils.response import ServiceResponse
from app.utils.logger import ServiceLogger


logger = ServiceLogger()


def serialize_website(website: Website) -> Dict[str, Any]:
    """Convert a Website model to a dictionary."""
    return {
        "id": website.id,
        "url": website.url,
        "max_urls": website.max_urls,
        "scrape_interval_days": website.scrape_interval_days,
        "last_scraped_at": (
            website.last_scraped_at.isoformat()
            if website.last_scraped_at else None
        ),
        "is_active": website.is_active
    }


def get_website_by_url(db: Session, url: str) -> Optional[Website]:
    """Get a website by its URL."""
    logger.info("website", f"Fetching website for URL: {url}")
    try:
        return db.query(Website).filter(Website.url == url).first()
    except Exception as e:
        logger.error("website", f"Error fetching website: {str(e)}")
        return None


def create_website(
    db: Session,
    url: str,
    max_urls: Optional[int] = None,
    scrape_interval_days: Optional[int] = None,
    last_scraped_at: Optional[datetime] = None
) -> Dict[str, Any]:
    """Create a new website entry."""
    logger.info("website", f"Creating website: {url}")
    try:
        website = Website(
            url=url,
            max_urls=max_urls or settings.DEFAULT_MAX_URLS,
            scrape_interval_days=(
                scrape_interval_days or
                settings.DEFAULT_SCRAPE_INTERVAL_DAYS
            ),
            last_scraped_at=last_scraped_at,
            is_active=True
        )
        db.add(website)
        db.commit()
        db.refresh(website)
        return ServiceResponse.success(
            data={
                "website": serialize_website(website)
            }
        )
    except Exception as e:
        logger.error("website", f"Error creating website: {str(e)}")
        db.rollback()
        return ServiceResponse.error(
            message=f"Failed to create website: {str(e)}",
            error_code="WEBSITE_CREATE_ERROR"
        )


def update_last_scraped(db: Session, website_id: int) -> Dict[str, Any]:
    """Update the last_scraped_at timestamp for a website."""
    logger.info("website", f"Updating website ID: {website_id}")
    try:
        website = db.query(Website).filter(Website.id == website_id).first()
        if website:
            website.last_scraped_at = datetime.utcnow()
            db.commit()
            db.refresh(website)
            logger.info("website", "Successfully updated last_scraped")
            return ServiceResponse.success(
                data={
                    "website": serialize_website(website)
                }
            )
        else:
            logger.error("website", f"Website not found: {website_id}")
            return ServiceResponse.error(
                message=f"Website not found: {website_id}",
                error_code="WEBSITE_NOT_FOUND"
            )
    except Exception as e:
        logger.error("website", f"Error updating last_scraped: {str(e)}")
        db.rollback()
        return ServiceResponse.error(
            message=f"Failed to update last_scraped: {str(e)}",
            error_code="WEBSITE_UPDATE_ERROR"
        )


def get_all_websites(db: Session) -> Dict[str, Any]:
    """Get all websites."""
    logger.info("website", "Fetching all websites")
    try:
        websites = db.query(Website).all()
        website_list = [
            serialize_website(website) for website in websites
        ]
        return ServiceResponse.success(
            data={
                "websites": website_list
            }
        )
    except Exception as e:
        logger.error("website", f"Error fetching websites: {str(e)}")
        return ServiceResponse.error(
            message=f"Failed to fetch websites: {str(e)}",
            error_code="WEBSITE_FETCH_ERROR"
        )


def get_stale_websites(db: Session) -> Dict[str, Any]:
    """Get websites that need to be re-scraped."""
    logger.info("website", "Fetching stale websites")
    try:
        websites = (
            db.query(Website)
            .filter(Website.is_active.is_(True))
            .filter(
                (Website.last_scraped_at.is_(None)) |  # Never scraped
                (
                    Website.last_scraped_at <
                    func.datetime(
                        'now',
                        '-' + func.cast(
                            Website.scrape_interval_days, 'text'
                        ) + ' days'
                    )
                )
            )
            .all()
        )
        website_list = [serialize_website(website) for website in websites]
        return ServiceResponse.success(
            data={
                "websites": website_list
            }
        )
    except Exception as e:
        logger.error("website", f"Error fetching stale websites: {str(e)}")
        return ServiceResponse.error(
            message=f"Failed to fetch stale websites: {str(e)}",
            error_code="WEBSITE_FETCH_ERROR"
        )
