from modal import Image, App, Volume, Secret
import json
from app.models.schemas.retrieval import RetrievalResult

from app.services.modal.config import (
    COLLECTION_NAME,
    MODAL_VOLUME_NAME,
    QDRANT_DB_PATH,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_MODEL_NORMALIZE
)


# Create Modal app
app = App("retrieval-augmented-llm")

# Reuse the existing Qdrant storage volume
storage = Volume.from_name(MODAL_VOLUME_NAME)


# Build the image with all dependencies
image = (
    Image.debian_slim(python_version="3.10")
    .pip_install(
        "qdrant-client",
        "sentence-transformers",
        "openai>=1.12.0",
        "pydantic>=2.6.3",
    )
)


@app.function(
    image=image,
    volumes={"/storage": storage},
    secrets=[Secret.from_name("openai-credentials")]
)
async def retrieve_and_generate(
    query: str,
    num_results: int = 3,
    url_prefix: str = None
) -> RetrievalResult:
    """Retrieve relevant passages and generate an answer using OpenAI."""
    from sentence_transformers import SentenceTransformer
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from openai import OpenAI
    import time
    import os

    start_time = time.time()

    # Initialize Qdrant client
    client = QdrantClient(path=QDRANT_DB_PATH)

    # Initialize embedding model
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    # Create query embedding
    query_embedding = model.encode(
        query,
        normalize_embeddings=EMBEDDING_MODEL_NORMALIZE
    )

    # Prepare search filter for URL prefix if specified
    search_filter = None
    if url_prefix:
        search_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="url",
                    match=models.MatchValue(value=url_prefix)
                )
            ]
        )

    # Search for relevant passages
    search_results = client.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_embedding.tolist(),
        limit=num_results,
        query_filter=search_filter
    )

    # Format context from search results
    context_passages = []
    sources = []

    for hit in search_results:
        context_passages.append(hit.payload['text'])
        sources.append({
            'url': hit.payload['url'],
            'text': hit.payload['text'][:200] + "...",  # Preview of the text
            'score': hit.score
        })

    # Prepare prompt with retrieved context
    prompt = (
        "Based on the following passages, answer the question. "
        "Include only information that is supported by the passages.\n\n"
        f"Passages:\n{json.dumps(context_passages, indent=2)}\n\n"
        f"Question: {query}\n\nAnswer:"
    )

    # Initialize OpenAI client with credentials from secrets
    openai_client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    )

    # First, get the answer
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that answers questions based "
                    "on the provided passages. Only use information from the "
                    "passages to answer questions. Don't mention the passages."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )

    answer = response.choices[0].message.content

    # Then, generate follow-up questions based on the answer and context
    followup_prompt = (
        "Based on the following question and its answer, suggest 5 relevant "
        "follow-up questions that would help explore the topic further. "
        "Make questions specific and directly related to the content.\n\n"
        f"Original Question: {query}\n\n"
        f"Answer: {answer}\n\n"
        "Generate 5 natural follow-up questions that would help explore "
        "this topic in more detail. Questions should be specific and based "
        "on the information provided."
    )

    followup_response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant that generates relevant "
                    "follow-up questions. Generate specific, focused "
                    "questions that explore the topic in more detail."
                )
            },
            {"role": "user", "content": followup_prompt}
        ],
        temperature=0.7,
        max_tokens=200
    )

    # Extract and clean up follow-up questions
    followup_questions = [
        q.strip().strip('0123456789.)')
        for q in followup_response.choices[0].message.content.split('\n')
        if q.strip() and any(c.isalpha() for c in q)
    ][:5]  # Ensure we get exactly 5 questions

    query_time = time.time() - start_time

    return RetrievalResult(
        answer=answer,
        sources=sources,
        query_time_seconds=query_time,
        follow_up_questions=followup_questions
    )


@app.local_entrypoint()
def main(
    query: str = "What is the best tractor I can buy?",
    url_prefix: str = None
):
    """Test the retrieval system locally."""

    print(f"\nQuery: {query}")
    if url_prefix:
        print(f"URL Prefix: {url_prefix}")

    result = retrieve_and_generate.remote(query, url_prefix=url_prefix)

    print("\nAnswer:")
    print(result.answer)

    print("\nSources:")
    for i, source in enumerate(result.sources, 1):
        print(f"\n{i}. {source['url']}")
        print(f"   Relevance Score: {source['score']:.3f}")
        print(f"   Preview: {source['text']}")

    print("\nFollow-up Questions:")
    for i, question in enumerate(result.follow_up_questions, 1):
        print(f"{i}. {question}")

    print(f"\nQuery Time: {result.query_time_seconds:.2f} seconds")
