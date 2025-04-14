<div align="center">

<h1>Proplexity</h1>

A modern web archival and retrieval system with semantic search capabilities.

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

</div>

## Overview

WayBack is an intelligent web archival system that combines modern web crawling with advanced semantic search capabilities. It allows you to:

- 🕷️ Crawl and archive websites automatically
- 🔍 Search archived content using natural language
- 🤖 Get AI-generated answers from your archived content
- ⏰ Keep content fresh with scheduled updates
- 📊 Track and manage archived websites


## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Poetry
- Modal CLI and account
- Qdrant instance

### Backend Setup

```bash
# Install dependencies
cd backend
poetry install

# Start server
poetry run uvicorn app.main:app --reload

# Deploy Modal functions
poetry run modal deploy app/services/modal/
```

### Frontend Setup

```bash
# Install dependencies
cd frontend
npm install

# Set up environment
cp .env.example .env.local
# Edit .env.local with your configurations

# Start development server
npm run dev
```

## Key Features

### Web Crawling
- Configurable crawling depth and limits
- Respects robots.txt and site boundaries
- Automatic content extraction and cleaning

### Content Processing
- Vector embeddings for semantic search
- Chunking and indexing of content
- Metadata extraction and storage

### Search and Retrieval
- Natural language querying
- LLM-powered answer generation
- Source attribution and citations

### Content Management
- Scheduled content refreshes
- Website tracking and monitoring
- Content update statistics


## ToDo

### Deployments
- [ ] Setup Backend Deployment
- [ ] Modal Secrets are manual rn

### Refactoring
- [ ] Move db operations to db repository

### Functionality
- [ ] Semantic chunking

## Documentation
- [Backend API Documentation](backend/README.md)
- [Frontend Documentation](frontend/README.md)
