"""
Main FastAPI application module.
This module initializes and configures the FastAPI application.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import retrieval, scraper, website
from .db.base_class import Base
from .db.session import engine

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Retrieval-Augmented Generation API",
    description="API for retrieving answers using RAG",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(retrieval.router)
app.include_router(scraper.router)
app.include_router(website.router)


@app.get("/")
async def root():
    """Root endpoint to verify API is running."""
    return {
        "status": "ok",
        "message": "Retrieval-Augmented Generation API is running"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
