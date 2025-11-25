# Semantic Search Implementation Plan: Hackathon MVP

**Scope**: Twitter content only, ~5K tweets, basic relevance, fast to ship

---

## What We're Building

**Core Flow**:
1. User connects Twitter → Content syncs → Embeddings generated on ingest
2. User types in document → Query gets embedded → Similar content surfaces in left panel
3. User drags content to document → Citation added

**Non-Goals for Hackathon**:
- ❌ Hybrid search (vector + FTS fusion)
- ❌ Advanced re-ranking
- ❌ Index optimization (HNSW/IVFFlat)
- ❌ Caching layer
- ❌ Substack/YouTube integration (Twitter only for demo)

---

## Architecture Overview

```
┌─────────────────┐
│  Content Ingest │
│  (Twitter Sync) │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Generate Embedding      │
│ (OpenAI API call)       │
│ text-embedding-3-small  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Store in Postgres       │
│ content.embedding       │
│ vector(1536)           │
└─────────────────────────┘

┌─────────────────┐
│ User Types      │
│ "AI safety..."  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Embed Query             │
│ (same model)            │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Vector Search           │
│ ORDER BY embedding      │
│ <-> query_vec LIMIT 20  │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Return Results          │
│ to Left Panel           │
└─────────────────────────┘
```

---

## Implementation Steps

### Step 1: Database Schema Changes

**1.1 Enable pgvector Extension**

If using Docker Compose locally:
```yaml
# docker-compose.yml
services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: digital_me
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

**1.2 Create Alembic Migration**

```bash
# Generate migration
alembic revision -m "add_embedding_to_content"
```

```python
# migrations/versions/xxxx_add_embedding_to_content.py
"""add embedding to content

Revision ID: xxxx
Revises: yyyy
Create Date: 2024-11-24
"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = 'xxxx'
down_revision = 'yyyy'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add embedding column (1536 dimensions for text-embedding-3-small)
    op.add_column(
        'content',
        sa.Column('embedding', Vector(1536), nullable=True)
    )

    # For hackathon: skip index, linear scan is fine for 5K items
    # Post-hackathon: add index for performance
    # op.execute('CREATE INDEX ON content USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);')

def downgrade() -> None:
    op.drop_column('content', 'embedding')
```

**1.3 Apply Migration**

```bash
# Local
alembic upgrade head

# K8s (run from migration job or pod)
kubectl exec -it <api-pod> -- alembic upgrade head
```

---

### Step 2: Add Embedding Generation Service

**2.1 Create Embedding Service**

```python
# src/services/embedding_service.py
from openai import AsyncOpenAI
from typing import List
import os

class EmbeddingService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "text-embedding-3-small"  # 1536 dimensions, $0.00002/1K tokens

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
            encoding_format="float"
        )
        return response.data[0].embedding

    async def embed_texts_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts (batch API call)."""
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
            encoding_format="float"
        )
        return [item.embedding for item in response.data]

# Singleton instance
embedding_service = EmbeddingService()
```

**2.2 Update Content Model**

```python
# src/domains/content/models.py
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from src.database import Base

class Content(Base):
    __tablename__ = "content"

    id = Column(UUID(as_uuid=True), primary_key=True)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id"), nullable=False)
    external_id = Column(String, nullable=False)  # Twitter tweet ID
    content_type = Column(String, nullable=False)  # "tweet", "article", etc.

    title = Column(String, nullable=True)
    body = Column(Text, nullable=False)
    url = Column(String, nullable=False)
    author = Column(String, nullable=True)

    published_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    # NEW: Embedding vector
    embedding = Column(Vector(1536), nullable=True)

    # Indexes
    __table_args__ = (
        # Keep existing indexes...
    )
```

---

### Step 3: Embed on Content Ingest

**3.1 Add Embedding to Content Creation**

```python
# src/domains/content/service.py
from src.services.embedding_service import embedding_service
from src.domains.content.models import Content
from src.domains.content.schemas import ContentCreate
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime

class ContentService:
    async def create_content(
        self,
        db: AsyncSession,
        content_data: ContentCreate
    ) -> Content:
        """Create new content with embedding."""

        # 1. Prepare text for embedding (combine title + body)
        embedding_text = self._prepare_embedding_text(
            title=content_data.title,
            body=content_data.body
        )

        # 2. Generate embedding
        try:
            embedding_vector = await embedding_service.embed_text(embedding_text)
        except Exception as e:
            # Log error but don't fail content creation
            print(f"Failed to generate embedding: {e}")
            embedding_vector = None

        # 3. Create content record
        content = Content(
            id=uuid.uuid4(),
            source_id=content_data.source_id,
            external_id=content_data.external_id,
            content_type=content_data.content_type,
            title=content_data.title,
            body=content_data.body,
            url=content_data.url,
            author=content_data.author,
            published_at=content_data.published_at,
            embedding=embedding_vector,  # Store embedding
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        db.add(content)
        await db.commit()
        await db.refresh(content)

        return content

    def _prepare_embedding_text(self, title: str | None, body: str) -> str:
        """Prepare text for embedding generation.

        Strategy: Combine title + body, truncate if needed.
        OpenAI token limit: 8,191 tokens for text-embedding-3-small.
        For tweets (280 chars), this is never an issue.
        For articles, we might need to truncate.
        """
        parts = []

        if title:
            parts.append(title)

        parts.append(body)

        text = " ".join(parts)

        # For hackathon: don't worry about truncation
        # For production: truncate to ~6K tokens (~4500 words)
        # if len(text) > 30000:  # rough char limit
        #     text = text[:30000]

        return text

# Singleton instance
content_service = ContentService()
```

**3.2 Add Endpoint for Testing**

```python
# src/domains/content/router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.domains.content.service import content_service
from src.domains.content.schemas import ContentCreate, ContentResponse

router = APIRouter(prefix="/content", tags=["content"])

@router.post("/", response_model=ContentResponse)
async def create_content(
    content_data: ContentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new content (with automatic embedding generation)."""
    content = await content_service.create_content(db, content_data)
    return content
```

---

### Step 4: Implement Semantic Search

**4.1 Create Search Service**

```python
# src/domains/content/search_service.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from src.domains.content.models import Content
from src.services.embedding_service import embedding_service

class SearchService:
    async def semantic_search(
        self,
        db: AsyncSession,
        query: str,
        source_ids: List[str] | None = None,
        limit: int = 20,
        min_similarity: float = 0.7  # Cosine similarity threshold
    ) -> List[Content]:
        """Search content using semantic similarity.

        Args:
            query: User's search query (what they're writing about)
            source_ids: Optional filter to specific sources
            limit: Max results to return
            min_similarity: Minimum cosine similarity threshold (0-1)

        Returns:
            List of relevant content, ordered by similarity
        """

        # 1. Generate query embedding
        query_embedding = await embedding_service.embed_text(query)

        # 2. Build query
        stmt = select(Content).where(
            Content.embedding.isnot(None)  # Only search content with embeddings
        )

        # 3. Filter by sources if specified
        if source_ids:
            stmt = stmt.where(Content.source_id.in_(source_ids))

        # 4. Order by cosine similarity
        # pgvector operator: <-> is cosine distance (lower = more similar)
        # cosine similarity = 1 - cosine distance
        stmt = stmt.order_by(
            Content.embedding.cosine_distance(query_embedding)
        ).limit(limit)

        # 5. Execute query
        result = await db.execute(stmt)
        contents = result.scalars().all()

        # 6. Filter by similarity threshold
        # Note: cosine_distance returns distance (0=identical, 2=opposite)
        # For hackathon: skip this filtering, show top-k results
        # For production: calculate actual similarity and filter

        return list(contents)

# Singleton
search_service = SearchService()
```

**4.2 Add Search Endpoint**

```python
# src/domains/content/router.py
from src.domains.content.search_service import search_service
from src.domains.content.schemas import SearchRequest, SearchResponse

@router.post("/search", response_model=SearchResponse)
async def search_content(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """Semantic search over content.

    This is what gets called when user types in the document editor.
    """
    results = await search_service.semantic_search(
        db=db,
        query=request.query,
        source_ids=request.source_ids,
        limit=request.limit or 20
    )

    return SearchResponse(
        query=request.query,
        results=results,
        count=len(results)
    )
```

**4.3 Define Schemas**

```python
# src/domains/content/schemas.py
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import List

class SearchRequest(BaseModel):
    query: str
    source_ids: List[UUID4] | None = None
    limit: int = 20

class ContentResult(BaseModel):
    id: UUID4
    source_id: UUID4
    content_type: str
    title: str | None
    body: str
    url: str
    author: str | None
    published_at: datetime

    class Config:
        from_attributes = True

class SearchResponse(BaseModel):
    query: str
    results: List[ContentResult]
    count: int
```

---

## Cost Estimate for Hackathon

**Content to embed**:
- 5,000 tweets × 50 words = 250K words = ~333K tokens
- Cost: 333K × $0.00002/1K = **$0.0067** (~0.7 cents)

**Queries during demo**:
- Estimate 100 searches during testing/demo
- 100 × 50 words × $0.00002/1K tokens = **$0.0001** (<0.01 cents)

**Total hackathon cost: <$0.01** (less than one cent)

---

## What Success Looks Like

✅ User starts typing → Relevant content appears automatically
✅ Search results feel accurate (users recognize relevant tweets)
✅ Latency <2 seconds (acceptable for demo)
✅ Citations work (drag → [1] appears)
✅ No crashes during demo

---

## Post-Hackathon Improvements

**Priority 1: Performance**
- Add HNSW index for faster search
- Implement result caching
- Optimize query debouncing

**Priority 2: Relevance**
- Add hybrid search (vector + FTS)
- Implement re-ranking
- Add user feedback loop ("was this relevant?")

**Priority 3: Scale**
- Batch embedding generation
- Add rate limiting
- Implement background workers

---

## Quick Reference Commands

```bash
# Setup
docker-compose up -d
alembic upgrade head
python scripts/backfill_embeddings.py

# Test
curl -X POST http://localhost:8000/api/content/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "limit": 10}'

# Monitor
# Check embedding generation success rate
psql -d digital_me -c "SELECT
  COUNT(*) as total,
  COUNT(embedding) as with_embedding,
  COUNT(*) - COUNT(embedding) as missing_embedding
FROM content;"
```

---

This plan should get you from zero to working semantic search in **4-6 hours of focused work**. The key is to keep it simple for the hackathon and iterate after you validate the core value proposition.

Want me to help with any specific part of the implementation?

---

## Local implementation status (phase 1)
- Local Postgres now uses a pgvector-enabled image in docker-compose (`pgvector/pgvector:pg15`).
- Schema change in place: `content.embedding VECTOR(1536)` plus an IVFFlat index (cosine, lists=100). Migration id: `d0f4e7f6c4a1`.
- Model change: `Content.embedding: list[float] | None` backed by `pgvector.sqlalchemy.Vector(1536)`.
- How to run locally:
  1. `cd fury_api && docker-compose up postgres -d` (first run creates DB with pgvector).
  2. `make db-migrate` (applies migrations using `src/fury_api/lib/db/alembic.ini`).
  3. (Optional) regenerate migration with autogenerate: `make db-create-migration m="add content embedding"` — we've already added one manually.
- Not yet done: embedding generation/backfill; search query path; ~~k8s/Helm changes~~ ✅ **DONE**.

---

## Production Deployment (Kubernetes/Helm)

### Overview

Deploying pgvector-enabled PostgreSQL to Kubernetes requires careful configuration due to differences between the official PostgreSQL Docker image (which pgvector is based on) and the Bitnami PostgreSQL Helm chart we use for deployment.

### Architecture Decisions

**Image Choice: `pgvector/pgvector:pg15`**
- Based on the official PostgreSQL 15 Docker image
- Includes the pgvector extension pre-installed
- Different from Bitnami's PostgreSQL image structure

**Schema Strategy: Install Extension in `platform` Schema**
- All application tables live in the `platform` schema
- Installing the vector extension in the same schema avoids search_path issues
- Simplifies migrations and queries (no need to reference `public` schema)

**Deployment Method: Bitnami PostgreSQL Helm Chart with Custom Image**
- Use Bitnami chart for standardized Kubernetes deployment patterns
- Override default image to use pgvector image
- Requires specific compatibility configurations

### Configuration Details

**File: `fury_api/deploy/helm/values.yaml`**

```yaml
postgresql:
  enabled: true
  auth:
    # Credentials set via helm --set flags in Makefile's push-helm target
    username: postgres
    database: digital-me
  service:
    port: 5432

  # Override Bitnami image with pgvector
  image:
    registry: docker.io
    repository: pgvector/pgvector
    tag: pg15

  primary:
    # Set POSTGRES_DB environment variable for official image compatibility
    extraEnvVars:
      - name: POSTGRES_DB
        value: digital-me

    # Initialize database with platform schema and vector extension
    initdb:
      scripts:
        enable-vector.sh: |
          #!/bin/bash
          set -e
          psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "digital-me" <<-EOSQL
            CREATE SCHEMA IF NOT EXISTS platform;
            CREATE EXTENSION IF NOT EXISTS vector SCHEMA platform;
          EOSQL

    # Security context for official PostgreSQL image (user 999)
    podSecurityContext:
      enabled: true
      fsGroup: 999
    containerSecurityContext:
      enabled: true
      runAsUser: 999
      runAsNonRoot: true

    # Mount writable /var/run/postgresql for lock files
    extraVolumes:
      - name: run-postgresql
        emptyDir: {}
    extraVolumeMounts:
      - name: run-postgresql
        mountPath: /var/run/postgresql
```

### Key Compatibility Issues & Solutions

#### Issue 1: Database Not Created
**Problem**: Bitnami chart's `auth.database` setting doesn't work with official PostgreSQL image.

**Solution**: Explicitly set `POSTGRES_DB` environment variable:
```yaml
extraEnvVars:
  - name: POSTGRES_DB
    value: digital-me
```

#### Issue 2: Read-Only File System Error
**Problem**: Official PostgreSQL image needs write access to `/var/run/postgresql` for lock files, but Bitnami chart mounts it as read-only.

**Solution**: Mount an `emptyDir` volume at `/var/run/postgresql`:
```yaml
extraVolumes:
  - name: run-postgresql
    emptyDir: {}
extraVolumeMounts:
  - name: run-postgresql
    mountPath: /var/run/postgresql
```

#### Issue 3: Permission Errors
**Problem**: Official PostgreSQL image runs as user `postgres` (UID 999), not Bitnami's default user.

**Solution**: Set security contexts to match official image:
```yaml
podSecurityContext:
  enabled: true
  fsGroup: 999
containerSecurityContext:
  enabled: true
  runAsUser: 999
  runAsNonRoot: true
```

#### Issue 4: Vector Extension Not Found
**Problem**: Migration fails with `type "vector" does not exist` because:
1. Alembic sets `search_path` to `platform` schema only
2. Vector extension was initially installed in `public` schema

**Solution**: Install extension in the same schema as application tables:
```sql
CREATE SCHEMA IF NOT EXISTS platform;
CREATE EXTENSION IF NOT EXISTS vector SCHEMA platform;
```

This way, when migrations run with `search_path=platform`, the vector type is accessible.

### Migration Configuration

**File: `fury_api/src/fury_api/lib/db/migrations/env.py`**

The migration environment sets the search path to the platform schema:

```python
def context_pre_begin_transaction() -> None:
    context.execute(f"create schema if not exists {target_metadata.schema};")
    context.execute(f"set search_path to {target_metadata.schema}")
```

With the vector extension installed in the `platform` schema, migrations can use the `VECTOR` type without additional configuration.

### Deployment Workflow

**1. Initial Deployment**
```bash
# Set correct Kubernetes context
make set-context

# Deploy Helm chart (creates PostgreSQL with pgvector)
make push-helm

# Wait for PostgreSQL pod to be ready
kubectl get pods -w

# Run migrations
make db-migrate-prod
```

**2. Redeployment (Clean Slate)**
```bash
# Delete existing PostgreSQL resources
kubectl delete statefulset digital-me-api-postgresql
kubectl delete pvc data-digital-me-api-postgresql-0

# Redeploy
make push-helm

# Run migrations
make db-migrate-prod
```

**3. Verification**
```bash
# Check PostgreSQL logs
kubectl logs digital-me-api-postgresql-0

# Verify extension installation
kubectl exec -it digital-me-api-postgresql-0 -- \
  psql -U postgres -d digital-me -c "\dx"

# Expected output:
#   Name   | Version | Schema   | Description
# ---------+---------+----------+------------------
#  vector  | 0.8.1   | platform | vector data type...

# Verify platform schema exists
kubectl exec -it digital-me-api-postgresql-0 -- \
  psql -U postgres -d digital-me -c "\dn"

# Check migration status
make db-current
```

### Makefile Integration

**File: `fury_api/Makefile`**

The `push-helm` target handles database credentials and Helm deployment:

```makefile
.PHONY: push-helm
push-helm:
	@$(MAKE) validate-context
	@if [ ! -f .env.prod ]; then echo "Error: .env.prod file not found!" && exit 1; fi
	@echo "Extracting DB credentials from .env.prod"
	@FURY_DB_USER=$$(grep -E '^FURY_DB_USER=' .env.prod | cut -d'=' -f2) && \
	 FURY_DB_PASSWORD=$$(grep -E '^FURY_DB_PASSWORD=' .env.prod | cut -d'=' -f2) && \
	 FURY_DB_NAME=$$(grep -E '^FURY_DB_NAME=' .env.prod | cut -d'=' -f2) && \
	 echo "Installing Helm Chart with user: $$FURY_DB_USER" && \
	 helm upgrade --install $(HELM_CHART_NAME) $(HELM_CHART_PATH) \
		--set postgresql.auth.username=$$FURY_DB_USER \
		--set postgresql.auth.password=$$FURY_DB_PASSWORD \
		--set postgresql.auth.database=$$FURY_DB_NAME
```

The `db-migrate-prod` target runs migrations via port-forward:

```makefile
.PHONY: db-migrate-prod
db-migrate-prod:
	@$(MAKE) validate-context
	@echo "Starting port-forwarding for PostgreSQL..."
	@kubectl port-forward svc/digital-me-api-postgresql 5432:5432 &
	@sleep 3
	@echo "Running database migration..."
	@FURY_DB_URL=postgresql+psycopg://$$(grep -E '^FURY_DB_USER=' .env.prod | cut -d'=' -f2):$$(grep -E '^FURY_DB_PASSWORD=' .env.prod | cut -d'=' -f2)@127.0.0.1:5432/$$(grep -E '^FURY_DB_NAME=' .env.prod | cut -d'=' -f2) \
	$(POETRY) run alembic --config $(ALEMBIC_CONFIG) upgrade head
	@echo "Stopping port-forwarding..."
	@pkill -f "kubectl port-forward svc/digital-me-api-postgresql 5432:5432"
```

### Production Checklist

Before deploying to production, ensure:

- [ ] `.env.prod` contains correct database credentials (`FURY_DB_USER`, `FURY_DB_PASSWORD`, `FURY_DB_NAME`)
- [ ] Kubernetes context is set to production cluster (`make validate-context`)
- [ ] Helm dependencies are updated (`helm dependency update fury_api/deploy/helm/`)
- [ ] Database backup exists (if upgrading existing deployment)
- [ ] Monitoring is in place to track migration success/failure

### Troubleshooting

**Pod stuck in CrashLoopBackOff**
```bash
# Check logs for permission errors
kubectl logs digital-me-api-postgresql-0

# Common fixes:
# 1. Verify security contexts match official image (user 999)
# 2. Check /var/run/postgresql is writable (emptyDir mounted)
# 3. Ensure POSTGRES_DB is set
```

**Migration fails with "database does not exist"**
```bash
# Verify POSTGRES_DB environment variable
kubectl exec -it digital-me-api-postgresql-0 -- env | grep POSTGRES_DB

# Check if database was created
kubectl exec -it digital-me-api-postgresql-0 -- \
  psql -U postgres -l
```

**Migration fails with "type vector does not exist"**
```bash
# Check if extension exists and in which schema
kubectl exec -it digital-me-api-postgresql-0 -- \
  psql -U postgres -d digital-me -c "SELECT * FROM pg_extension WHERE extname = 'vector';"

# If in wrong schema, recreate:
kubectl exec -it digital-me-api-postgresql-0 -- \
  psql -U postgres -d digital-me -c "DROP EXTENSION vector; CREATE EXTENSION vector SCHEMA platform;"
```

### Cost Considerations

**Storage**:
- Default PVC size: 8Gi (Bitnami chart default)
- For 5K tweets: ~100MB of actual data + embeddings
- Plenty of headroom for growth

**Compute**:
- No special CPU/memory requirements for pgvector with small dataset
- Linear scan is fast enough for <10K vectors
- Consider HNSW index for >50K vectors

### Future Optimizations

When scaling beyond hackathon MVP:

1. **Index Optimization**: Switch from IVFFlat to HNSW for better performance
2. **Resource Limits**: Set appropriate CPU/memory limits based on usage patterns
3. **Backup Strategy**: Implement automated backups of PostgreSQL data
4. **High Availability**: Consider primary-replica setup for production
5. **Monitoring**: Add metrics for query latency and index usage

---

## Status: Production-Ready ✅

The database is now deployed to Kubernetes with pgvector support. Next steps:
- [ ] Implement embedding generation service
- [ ] Create backfill script for existing content
- [ ] Build semantic search API endpoint
- [ ] Integrate with frontend
