from fastapi import APIRouter, HTTPException

from app.models.schemas.retrieval import RetrievalRequest
from app.services.retrieval_service import retrieve_answer

router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/")
async def get_retrieval_answer(request: RetrievalRequest):
    """
    Get an answer for a query using retrieval-augmented generation.

    Args:
        request: RetrievalRequest containing query and optional parameters

    Returns:
        JSON response with answer, sources, and follow-up questions
    """
    try:
        result = await retrieve_answer(
            query=request.query,
            num_results=request.num_results,
            url_prefix=request.url_prefix,
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing request: {str(e)}"
        )
