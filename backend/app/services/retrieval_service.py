from typing import Optional, Dict, Any, TypedDict, List
from app.utils.modal_manager import ModalFunctionRegistry
from app.utils.response import ServiceResponse
from app.utils.logger import ServiceLogger
from app.utils.serialization import serialize_model


class Source(TypedDict):
    url: str
    text: str


class RetrievalResponse(TypedDict):
    answer: str
    sources: List[Source]
    follow_up_questions: List[str]


logger = ServiceLogger()
modal_registry = ModalFunctionRegistry()


def ensure_retrieval_structure(data: Any) -> RetrievalResponse:
    """Ensure the response matches the expected structure."""
    if not isinstance(data, dict):
        data = {} if data is None else {"raw": str(data)}

    return {
        "answer": str(data.get("answer", "")),
        "sources": [
            {"url": str(s.get("url", "")), "text": str(s.get("text", ""))}
            for s in (data.get("sources", []) or [])
        ],
        "follow_up_questions": [
            str(q) for q in (data.get("follow_up_questions", []) or [])
        ],
    }


async def retrieve_answer(
    query: str, num_results: int = 3, url_prefix: Optional[str] = None
) -> Dict[str, Any]:
    """
    Retrieve an answer using Modal's retrieve_and_generate function.

    Args:
        query: The user's query
        num_results: Number of passages to retrieve
        url_prefix: Optional URL prefix to filter results

    Returns:
        Dict containing answer, sources, and follow-up questions
    """
    logger.info(
        "retrieval",
        f"Processing query: {query} (num_results={num_results})"
    )

    try:
        retrieval_func = modal_registry.get_function(
            "retrieval-augmented-llm", "retrieve_and_generate"
        )

        # Call the function and get result
        raw_result = await retrieval_func.remote.aio(
            query=query, num_results=num_results, url_prefix=url_prefix
        )

        # Ensure proper structure and serialization
        serialized_result = serialize_model(raw_result)
        structured_result = ensure_retrieval_structure(serialized_result)

        logger.info("retrieval", "Successfully retrieved answer")
        return ServiceResponse.success(structured_result)

    except Exception as e:
        logger.error("retrieval", f"Error retrieving answer: {str(e)}")
        error_response = ensure_retrieval_structure(
            {
                "answer": f"Error: {str(e)}",
                "sources": [], "follow_up_questions": []
            }
        )
        return ServiceResponse.error(
            message=f"Failed to retrieve answer: {str(e)}",
            error_code="RETRIEVAL_ERROR",
            data=error_response,
        )
