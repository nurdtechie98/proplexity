from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class QueryRequest(BaseModel):
    query: str
    num_results: int = 3
    url_prefix: str = None


class RetrievalResult(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    query_time_seconds: float
    follow_up_questions: List[str]


class RetrievalRequest(BaseModel):
    query: str
    num_results: int = 3
    url_prefix: Optional[str] = None
