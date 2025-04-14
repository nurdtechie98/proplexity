"""
Central configuration file for database, model, and storage settings.
"""

# Storage configuration
STORAGE_PATH = "/storage"
QDRANT_DB_PATH = f"{STORAGE_PATH}/qdrant"

# Collection configuration
COLLECTION_NAME = "webpage_chunks"
VECTOR_CONFIG = {
    'size': 384,  # BGE-small-en-v1.5 embedding size
    'distance': 'Cosine'
}

# Model configuration
EMBEDDING_MODEL_NAME = 'BAAI/bge-small-en-v1.5'
EMBEDDING_MODEL_NORMALIZE = True

# Modal configuration
MODAL_APP_NAME = "markdown-scraper"
MODAL_VOLUME_NAME = "embedding-storage"

# Search defaults
DEFAULT_SEARCH_LIMIT = 5
DEFAULT_SCROLL_LIMIT = 200
