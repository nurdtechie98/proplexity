from typing import List, Optional
import modal

from app.services.modal.config import (
    COLLECTION_NAME,
    MODAL_APP_NAME,
    MODAL_VOLUME_NAME,
    QDRANT_DB_PATH,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_MODEL_NORMALIZE,
    DEFAULT_SEARCH_LIMIT,
    DEFAULT_SCROLL_LIMIT,
)


app = modal.App(MODAL_APP_NAME)
storage = modal.Volume.from_name(MODAL_VOLUME_NAME)


@app.function(
    image=modal.Image.debian_slim(python_version="3.10").pip_install(
        "qdrant-client", "torch", "transformers", "sentence-transformers"
    ),
    volumes={"/storage": storage},
)
async def search_index(
    query: str, k: int = DEFAULT_SEARCH_LIMIT, url_prefix: Optional[str] = None
) -> List[dict]:
    """Search the Qdrant index for semantically similar content.

    This function performs semantic similarity search using the specified
    embedding model. It can optionally filter results by URL prefix.

    Args:
        query (str): The search query to find similar content for
        k (int): Maximum number of results to return (default: from config)
        url_prefix (Optional[str]): Only search content from URLs with prefix

    Returns:
        List[dict]: List of search results, each containing:
            - url: Source URL of the content
            - text: The matched content
            - score: Similarity score (0-1)
            - timestamp: When the content was indexed
    """
    from sentence_transformers import SentenceTransformer
    from qdrant_client import QdrantClient
    from qdrant_client.http import models

    client = QdrantClient(path=QDRANT_DB_PATH)

    collections = client.get_collections().collections
    if not any(col.name == COLLECTION_NAME for col in collections):
        return []

    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    query_embedding = model.encode(
        query, normalize_embeddings=EMBEDDING_MODEL_NORMALIZE
    )

    search_filter = None
    if url_prefix:
        search_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="url", match=models.MatchValue(value=url_prefix)
                )
            ]
        )

    search_results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding.tolist(),
        limit=k,
        query_filter=search_filter,
    )

    results = []
    for hit in search_results:
        result = hit.payload
        result["score"] = hit.score
        results.append(result)

    return results


@app.function(
    image=modal.Image.debian_slim(python_version="3.10").pip_install("qdrant-client"),
    volumes={"/storage": storage},
)
async def delete_by_url_prefix(url_prefix: str) -> int:
    """Delete all indexed content from URLs matching a prefix.

    This function removes all vector entries whose URLs start with the
    specified prefix. This is useful for removing content from specific
    domains or paths.

    Args:
        url_prefix (str): Remove all content where URL starts with this prefix

    Returns:
        int: Number of vector points deleted from the collection
    """
    from qdrant_client import QdrantClient
    from qdrant_client.http import models

    client = QdrantClient(path=QDRANT_DB_PATH)

    collections = client.get_collections().collections
    if not any(col.name == COLLECTION_NAME for col in collections):
        return 0

    url_filter = models.Filter(
        must=[
            models.FieldCondition(
                key="url",
                match=models.TextMatch(text=url_prefix)
            )
        ]
    )

    initial_count = client.count(
        collection_name=COLLECTION_NAME, count_filter=url_filter
    ).count

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.FilterSelector(filter=url_filter),
    )

    return initial_count


@app.function(
    image=modal.Image.debian_slim(python_version="3.10").pip_install("qdrant-client"),
    volumes={"/storage": storage},
)
async def get_unique_urls() -> List[str]:
    """Get a list of all unique URLs in the vector database.

    This function scrolls through all points in the collection and
    extracts unique URLs. This is useful for understanding what content
    has been indexed.

    Returns:
        List[str]: Sorted list of unique URLs found in the collection
    """
    from qdrant_client import QdrantClient

    client = QdrantClient(path=QDRANT_DB_PATH)

    collections = client.get_collections().collections
    if not any(col.name == COLLECTION_NAME for col in collections):
        return []

    unique_urls = set()
    offset = None

    while True:
        response = client.scroll(
            collection_name=COLLECTION_NAME,
            offset=offset,
            limit=DEFAULT_SCROLL_LIMIT,
            with_payload=True,
        )

        if not response[0]:
            break

        for point in response[0]:
            if "url" in point.payload:
                unique_urls.add(point.payload["url"])

        if not response[1]:
            break

        offset = response[1]

    return sorted(list(unique_urls))


@app.function(
    image=modal.Image.debian_slim(python_version="3.10").pip_install("qdrant-client"),
    volumes={"/storage": storage},
)
async def get_point_by_id(point_id: str) -> Optional[dict]:
    """Retrieve a specific vector entry by its ID.

    This function fetches complete information about a specific vector entry,
    including its payload and vector values. Useful for debugging and
    detailed analysis.

    Args:
        point_id (str): UUID of the vector point to retrieve

    Returns:
        Optional[dict]: If found, a dictionary containing:
            - id: Point UUID
            - payload: Associated metadata (URL, text, timestamp)
            - vector: The actual vector values
        Returns None if point not found or on error
    """
    from qdrant_client import QdrantClient

    client = QdrantClient(path=QDRANT_DB_PATH)

    collections = client.get_collections().collections
    if not any(col.name == COLLECTION_NAME for col in collections):
        return None

    try:
        points = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=[point_id],
            with_payload=True,
            with_vectors=True,
        )

        if points:
            point = points[0]
            return {
                "id": point.id,
                "payload": point.payload,
                "vector": point.vector
            }
        return None
    except Exception as e:
        print(f"Error retrieving point: {str(e)}")
        return None


@app.local_entrypoint()
def main(
    action: str = "stats",
    url: str = None,
    point_id: Optional[str] = None
):
    """Command-line interface for helper utilities.

    This function provides a CLI interface to the helper functions,
    making it easy to perform common operations from the command line.

    Args:
        action (str): The operation to perform:
            - "get": Retrieve details about a specific point
            - "delete": Remove content from URLs with prefix
            - "stats": Show statistics about indexed content
        url (str): URL prefix for delete operation
        point_id (Optional[str]): Point ID for get operation

    Example Usage:
        # Get statistics about indexed content
        modal run helper.py --action stats

        # Delete content from a domain
        modal run helper.py --action delete --url "https://example.com"

        # Get details about a specific point
        modal run helper.py --action get --point-id "123e4567-e89b"
    """
    if action == "get":
        if not point_id:
            print("Error: point_id is required for 'get' action")
            return
        result = get_point_by_id.remote(point_id)
        if result:
            print("\nPoint details:")
            print("-------------")
            print(f"ID: {result['id']}")
            print("\nPayload:")
            for key, value in result["payload"].items():
                print(f"{key}: {value}")
            print(f"\nVector dimension: {len(result['vector'])}")
        else:
            print(f"No point found with ID: {point_id}")
    elif action == "delete":
        if not url:
            print("Error: url is required for 'delete' action")
            return
        deleted_count = delete_by_url_prefix.remote(url)
        print(f"Deleted {deleted_count} points with URL prefix: {url}")
    elif action == "stats":
        urls = get_unique_urls.remote()
        print("\nCurrent indexed URLs:")
        print("--------------------")
        for i, url in enumerate(urls, 1):
            print(f"{i}. {url}")
        print(f"\nTotal unique URLs: {len(urls)}")
    else:
        print(f"Invalid action: {action}. Use 'get', 'delete', or 'stats'")
