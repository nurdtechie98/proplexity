import modal
from typing import List, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import queue
import uuid

from app.services.modal.config import (
    COLLECTION_NAME,
    MODAL_APP_NAME,
    MODAL_VOLUME_NAME,
    QDRANT_DB_PATH,
    EMBEDDING_MODEL_NAME,
    EMBEDDING_MODEL_NORMALIZE
)


# Create persistent volume for storing Qdrant data
try:
    storage = modal.Volume.from_name(MODAL_VOLUME_NAME)
except modal.exception.NotFoundError:
    storage = modal.Volume.create(name=MODAL_VOLUME_NAME, size=10)


app = modal.App(name=MODAL_APP_NAME)


playwright_image = modal.Image.debian_slim(python_version="3.10").run_commands(
    "apt-get update",
    "apt-get install -y software-properties-common",
    "apt-add-repository non-free",
    "apt-add-repository contrib",
    "pip install playwright==1.42.0",
    "pip install html2text",
    "playwright install-deps chromium",
    "playwright install chromium",
)


@dataclass
class ChunkMetadata:
    url: str
    text: str
    start_idx: int
    end_idx: int
    timestamp: str = datetime.now().isoformat()


# ToDo: Go for a better splitter than fixed length
def generate_chunks(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100
) -> List[Tuple[str, int, int]]:
    """Split text into overlapping chunks."""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        chunks.append((chunk, i, i + len(chunk)))
    return chunks


@app.function(
    image=modal.Image.debian_slim(python_version="3.10").pip_install(
        "qdrant-client",
        "torch",
        "transformers",
        "sentence-transformers"
    ),
    volumes={"/storage": storage},
    max_containers=4
)
async def process_and_index_content(
    markdown_content: str,
    url: str
) -> None:
    """Process markdown content, create embeddings, and store in Qdrant.

    Args:
        markdown_content (str): The markdown content to process
        url (str): Source URL of the content
    """
    from sentence_transformers import SentenceTransformer
    from qdrant_client import QdrantClient
    from qdrant_client.http import models

    # Initialize Qdrant client with persistent storage
    client = QdrantClient(path=QDRANT_DB_PATH)

    # Create collection if it doesn't exist
    collections = client.get_collections().collections
    if not any(col.name == COLLECTION_NAME for col in collections):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                # BGE-small-en-v1.5 embedding size
                size=384,
                distance=models.Distance.COSINE
            )
        )

    # Initialize the embedding model
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    # Generate chunks
    chunks_with_positions = generate_chunks(markdown_content)

    # Create embeddings and points
    points = []
    for i, (chunk, start_idx, end_idx) in enumerate(chunks_with_positions):
        embedding = model.encode(
            chunk,
            normalize_embeddings=EMBEDDING_MODEL_NORMALIZE
        )

        metadata = ChunkMetadata(
            url=url,
            text=chunk,
            start_idx=start_idx,
            end_idx=end_idx
        )

        # Generate a UUID for the point
        point_id = str(uuid.uuid4())

        points.append(models.PointStruct(
            id=point_id,  # Use UUID string as ID
            vector=embedding.tolist(),
            payload=metadata.__dict__
        ))

    # Upload points in batches
    BATCH_SIZE = 100
    for i in range(0, len(points), BATCH_SIZE):
        batch = points[i:i + BATCH_SIZE]
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=batch
        )


@app.function(image=playwright_image)
async def scrape_page_and_links(url: str) -> Tuple[str, Set[str]]:
    """Scrape a webpage and extract all links from the same domain.

    Args:
        url (str): The URL of the webpage to scrape.

    Returns:
        Tuple[str, Set[str]]: Tuple of (markdown_content, set of links)
    """
    from playwright.async_api import async_playwright
    from html2text import html2text
    from urllib.parse import urlparse

    base_domain = urlparse(url).netloc

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/58.0.3029.110 Safari/537.3"
        )
        page = await context.new_page()

        try:
            await page.goto(url)
            await page.wait_for_load_state("networkidle")

            # Get page content for markdown conversion
            content = await page.content()
            markdown_content = html2text(content)

            # Extract all links
            links = await page.eval_on_selector_all(
                "a[href]",
                "elements => elements.map(element => element.href)"
            )

            # Filter links to only include those from the same domain
            filtered_links = {
                link for link in links
                if urlparse(link).netloc == base_domain
                and not link.endswith(('.pdf', '.jpg', '.png', '.gif'))
            }

            await browser.close()
            return markdown_content, filtered_links

        except Exception as e:
            print(f"Error processing {url}: {str(e)}")
            await browser.close()
            return "", set()


@app.function(
        timeout=3600
)
def spider_master(
    start_url: str,
    max_urls: int = 100,
    batch_size: int = 10
) -> None:
    """Master function that coordinates workers to spider through a website.

    Args:
        start_url: Starting URL to begin scraping from
        max_urls: Maximum number of URLs to scrape
        batch_size: Number of URLs to process in each batch
    """
    start_time = datetime.now()

    # Create shared queue and dict for coordination
    with (
        modal.Queue.ephemeral() as url_queue,
        modal.Dict.ephemeral() as visited_urls
    ):
        # Initialize counter in the shared dict
        visited_urls['count'] = 0
        visited_urls['urls'] = {}

        # Add starting URL to queue
        url_queue.put(start_url)

        # Process URLs until queue is empty or max_urls reached
        while visited_urls['count'] < max_urls:
            try:
                print(
                    f"Current progress: "
                    f"{visited_urls['count']}/{max_urls} URLs processed"
                )
                # Get batch of URLs from queue
                urls = []
                try:
                    queued_url = url_queue.get_many(
                        n_values=batch_size,
                        timeout=10
                    )
                    urls = [
                        url for url in queued_url
                        if url not in visited_urls['urls']
                    ]
                except queue.Empty:
                    print("Queue is empty or timeout reached")
                    break

                if not urls:
                    print("No more URLs to process")
                    break
                else:
                    print(f"Processing batch of {len(urls)} URLs")

                # Spawn workers for the batch of URLs and consume results
                worker_tasks = [
                    (url, url_queue, visited_urls, max_urls)
                    for url in urls
                ]

                for result in worker.starmap(worker_tasks):
                    print(f"Done prcessing {result}")
            except Exception as e:
                print(f"Error in master: {str(e)}")
                break

        elapsed = (datetime.now() - start_time).total_seconds()
        print(
            f"Finished processing {visited_urls['count']} URLs "
            f"in {elapsed:.2f} seconds"
        )


@app.function(max_containers=10)
def worker(
    url: str,
    url_queue: modal.Queue,
    visited_urls: modal.Dict,
    max_urls: int
) -> None:
    """Worker function that processes a single URL and adds new URLs to queue.

    Args:
        url: URL to process
        url_queue: Queue for new URLs to process
        visited_urls: Shared dict of visited URLs
        max_urls: Maximum number of URLs to process
    """
    # Skip if we've already visited or hit the limit
    if url in visited_urls['urls'] or visited_urls['count'] >= max_urls:
        return

    print(f"Worker processing {url} ({visited_urls['count'] + 1}/{max_urls})")

    # Mark as visited
    visited_urls['urls'][url] = True
    visited_urls['count'] += 1

    # Scrape page and get links
    markdown_content, new_links = scrape_page_and_links.remote(url)

    # Index the content if we got any
    if markdown_content:
        process_and_index_content.spawn(
            markdown_content=markdown_content,
            url=url
        )

    # Add new unvisited links to queue
    for link in new_links:
        if (
            link not in visited_urls['urls']
            and visited_urls['count'] < max_urls
        ):
            try:
                url_queue.put(link, block=False)
            except queue.Full:
                break

    return url


@app.local_entrypoint()
def main(
    action: str = "scrape",
    url: str = "https://www.paulgraham.com/articles.html",
    max_urls: int = 10,
    batch_size: int = 20,
    point_id: Optional[str] = None
):
    """Main entrypoint for the scraper.

    Args:
        action (str): Either "scrape", "spider", "delete", "stats", or "get"
        url (str): URL to scrape or URL prefix to delete
        max_urls (int): Maximum number of URLs to scrape in spider mode
        batch_size (int): Number of URLs to process in each batch
        point_id (Optional[str]): ID of point to retrieve for "get" action
    """
    if action == "spider":
        spider_master.remote(
            start_url=url,
            max_urls=max_urls,
            batch_size=batch_size,
        )
        print("Spider scraping completed")
    elif action == "scrape":
        # Get content and links in one go
        markdown_content, _ = scrape_page_and_links.remote(url)
        # Wait for indexing to complete
        process_and_index_content.remote(
            markdown_content=markdown_content,
            url=url
        )
    else:
        print(
            f"Invalid action: {action}. "
            f"Use 'scrape', 'spider', 'delete', 'stats', or 'get'"
        )
