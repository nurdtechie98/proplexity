from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional


class WebsiteCreate(BaseModel):
    url: HttpUrl
    max_urls: int = 100
    scrape_interval_days: int = 7


class WebsiteResponse(BaseModel):
    id: int
    url: str
    last_scraped_at: Optional[datetime] = None
    created_at: datetime
    is_active: bool
    max_urls: int
    scrape_interval_days: int

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
