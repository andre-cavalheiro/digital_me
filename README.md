# Digital Me

**Digital Me** is an AI-assisted writing application that automatically surfaces relevant content from your curated sources while you write. Instead of context-switching between Twitter, Substack, and your writing environment, everything you need appears exactly when you need it - with zero manual effort.

## Architecture

The Digital Me platform consists of two main components:

### 1. [fury_api](fury_api/) - Backend API
- **Purpose**: FastAPI-based backend for content aggregation, AI processing, and data management
- **Stack**: Python, FastAPI, PostgreSQL, SQLModel, Firebase Authentication
- **Features**:
  - Multi-tenant organization management
  - Plugin system for content source integrations
  - User authentication and authorization
  - RESTful API with OpenAPI documentation
- **Setup**: See [fury_api/docs/00_SETUP.md](fury_api/docs/00_SETUP.md)

### 2. [halo_webapp](halo_webapp/) - Frontend Web Application
- **Purpose**: Next.js frontend for AI-assisted writing and content discovery
- **Stack**: Next.js 15, React 19, TypeScript, Tailwind CSS, shadcn/ui
- **Features**:
  - AI-powered writing interface
  - Content aggregation from multiple sources
  - Plugin management UI
  - Dark mode support
  - Responsive design
- **Setup**: See [halo_webapp/docs/00_SETUP.md](halo_webapp/docs/00_SETUP.md)

## Getting Started

### Prerequisites
- Node.js 18+ and npm/yarn (for frontend)
- Python 3.11+ and Poetry (for backend)
- PostgreSQL 15+ (for database)
- Docker (for containerization)
- Kubernetes cluster (for deployment)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/andre-cavalheiro/digital-me.git
   cd digital-me
   ```

2. **Set up the backend (fury_api)**
   ```bash
   cd fury_api
   # Follow instructions in docs/00_SETUP.md
   make install
   make start
   ```

3. **Set up the frontend (halo_webapp)**
   ```bash
   cd halo_webapp
   # Follow instructions in docs/00_SETUP.md
   npm install
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:3000
   - API Documentation: http://localhost:3000/docs

## Deployment

Both components can be deployed to Kubernetes using Helm charts:

```bash
# Backend
cd fury_api
make deploy

# Frontend
cd halo_webapp
make deploy
```

## Development Workflow

See the respective component READMEs for detailed development instructions:
- [fury_api Development](fury_api/README.md)
- [halo_webapp Development](halo_webapp/README.md)

---

## Nested repositories (git subtree)

This repo vendors some other projects via `git subtree`:

- `fury_api/` ← mirrors branch `digital-me` of `andre-cavalheiro/fury_api`
- `halo_webapp/` ← mirrors branch `digital-me` of `andre-cavalheiro/halo_webapp`

Day-to-day you can edit these folders and commit to `digital_me` as usual.

To sync **from** the upstream repos into this project:

```bash
# fury_api
git fetch fury_api
git subtree pull --prefix=fury_api fury_api digital-me --squash

# halo_webapp
git fetch halo_webapp
git subtree pull --prefix=halo_webapp halo_webapp digital-me --squash
```

To push changes **back** to the upstream repos:

```bash
# fury_api
git subtree push --prefix=fury_api fury_api digital-me

# halo_webapp
git subtree push --prefix=halo_webapp halo_webapp digital-me