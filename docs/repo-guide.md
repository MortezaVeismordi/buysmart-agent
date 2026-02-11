# Repository Navigation Guide

This repository implements BuySmart Agent, an AI-powered buy-side procurement agent designed to automate intelligent product sourcing, comparison, and decision support.

## Current Project Status (as of February 2025)
- Completed: Repository structure, clean architecture layout, initial documentation  
- In progress: Crawling pipeline, LLM integration, agent reasoning layer  
- Planned: Frontend dashboard, production-grade deployment, multi-user features

## Where to Start

### 2-minute overview
- README.md → Project summary, quick-start instructions, badges  
- docs/index.md → High-level overview and current status

### 5–10 minute deep dive
- docs/system-overview.md → Domain model (procurement), ownership boundaries, high-level data flows  
- docs/architecture.md (upcoming) → System architecture diagrams and component breakdown

### 15–30 minute technical review (recommended for technical evaluators)
- docs/architecture.md → C4-level diagrams and design rationale  
- docs/decision-log.md (upcoming) → Architecture Decision Records  
- docs/tradeoffs.md → Key technical trade-offs and alternatives considered  
- docs/roadmap.md → Detailed roadmap with completion status

## Folder Structure Overview

| Directory                  | Purpose                                                                 | Status          |
|----------------------------|-------------------------------------------------------------------------|-----------------|
| backend/src/               | Core business logic, domain model (procurement), agents, pipelines, interfaces | In development  |
| frontend/                  | User dashboard and presentation layer (React/Next.js or Vue planned)   | Planned         |
| platform/                  | Infrastructure, deployment artifacts, observability, security tooling  | Base ready      |
| configs/                   | Configuration files for environments, LLM providers, crawling settings | Base ready      |
| infra/ or platform/infra/  | Dockerfiles, compose files, Kubernetes manifests (production optional) | Base ready      |
| docs/                      | All architecture, decision, and navigation documentation               | Actively maintained |
| data/                      | Development and demonstration fixtures only (no real/sensitive data)   | Base ready      |
| tools/                     | Linting, formatting, pre-commit hooks                                   | Base ready      |

## Local Quick Start

### Using Docker (recommended for consistency)

```bash
# Start services (backend + postgres + redis + ...)
docker compose -f platform/compose/docker-compose.local.yml up -d

# Apply migrations if needed
docker compose exec backend python manage.py migrate

# Run development server
docker compose exec backend python manage.py runserver