from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.utils.response import ServiceResponseModel


class SpiderStartRequest(BaseModel):
    start_url: str
    max_urls: Optional[int] = 100
    batch_size: Optional[int] = 10


class SpiderStartResponse(ServiceResponseModel):
    data: Dict[str, Any]


class SpiderStatusResponse(ServiceResponseModel):
    data: Optional[Dict[str, Any]] = None
