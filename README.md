# BuySmart Agent

**AI-Powered Buy-Side Procurement Agent**

BuySmart Agent is an intelligent system that automates product sourcing, comparison, and decision support for buyers. It ingests natural language queries, crawls relevant web sources, extracts structured data, applies LLM reasoning for ranking and enrichment, and presents transparent, data-driven recommendations.

The project demonstrates clean architecture, domain-driven design, agentic workflows, and production-ready patterns in a real-world procurement use case.

## Features (Current & Planned)

- Natural language query parsing and intent extraction  
- Async web crawling with structured output (Crawl4AI)  
- LLM-powered reasoning, enrichment, and ranking (Claude / GPT-4o / Groq)  
- Transparent decision rationale (chain-of-thought visibility)  
- Modular pipelines: crawl → extract → enrich → rank → respond  
- Multi-environment configuration (local, staging, production)  
- Observability hooks (logging, metrics, future tracing)  

Planned:
- Responsive frontend dashboard (comparison tables, chat interface)  
- User authentication and session management  
- Price drop alerts and history tracking  
- Production deployment (Kubernetes + Helm demonstration)

## Tech Stack

| Layer              | Technology                          | Purpose                                      |
|--------------------|-------------------------------------|----------------------------------------------|
| Backend            | Django + Django REST Framework      | Core API, business logic, domain model       |
| Agent & Orchestration | LangChain primitives + custom pipelines | Tool calling, reasoning chains               |
| Web Crawling       | Crawl4AI                            | Async JS-capable crawling & LLM extraction   |
| LLM Providers      | Claude 3.5, GPT-4o, Groq Llama      | Reasoning, summarization, structured output  |
| Database           | PostgreSQL (with JSONB)             | Relational entities + flexible results       |
| Task Queue & Cache | Celery + Redis                      | Async processing, caching                    |
| Frontend (planned) | React / Next.js                     | Dashboard and user interaction               |
| Deployment         | Docker, docker-compose, Kubernetes  | Local → production readiness                 |
| Observability      | Prometheus, Grafana (planned)       | Metrics and dashboards                       |

## Project Status

- ✅ Repository structure & clean architecture  
- ✅ Comprehensive documentation (architecture, decisions, trade-offs, roadmap)  
- 🚧 Core agent pipeline & crawling integration  
- □ Frontend dashboard  
- □ Production deployment & observability  

See [docs/roadmap.md](docs/roadmap.md) for detailed phased plan.

## Quick Start (Local Development)

### Using Docker (recommended)

```bash
# Start services
docker compose -f platform/compose/docker-compose.local.yml up -d

# Apply migrations
docker compose exec backend python manage.py migrate

# Run development server
docker compose exec backend python manage.py runserver
```

### Without Docker

```bash
cd backend
pip install -r requirements/dev.txt
cp .env.example .env          # Configure LLM keys, etc.
python manage.py migrate
python manage.py runserver
```

Open http://localhost:8000 to access the API (Swagger docs at /api/schema/swagger-ui/).

## Documentation

All architecture, decisions, and navigation docs are in the [`docs/` directory](docs/).

| File                  | Purpose                                      |
|-----------------------|----------------------------------------------|
| index.md              | Project overview & status                    |
| repo-guide.md         | How to navigate the repository               |
| system-overview.md    | Domain model & ownership boundaries          |
| architecture.md       | System architecture with C4 diagrams         |
| decision-log.md       | Architecture Decision Records (ADRs)         |
| tradeoffs.md          | Key technical trade-offs                     |
| roadmap.md            | Phased development plan                      |
| contributing.md       | Contribution guidelines                      |

## Contributing

We welcome contributions!  
Please read [CONTRIBUTING.md](CONTRIBUTING.md) (or [docs/contributing.md](docs/contributing.md)) for guidelines on issues, pull requests, commit messages, and development setup.

## License

MIT License — see [LICENSE](LICENSE) for details.

## Contact / Feedback

Open an issue or start a discussion for questions, suggestions, or collaboration.

Last updated: February 11, 2026