# Technical Trade-offs

This document records the major technical decisions made during the design and early implementation of BuySmart Agent, including the trade-offs considered and the rationale for each choice.

## 1. Backend Framework: Django vs FastAPI vs Flask

| Option       | Pros                                                                 | Cons                                                                 | Decision & Rationale                                                                 |
|--------------|----------------------------------------------------------------------|----------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| Django       | Batteries-included (ORM, admin, auth, migrations, security defaults) | Slightly heavier startup time, more opinionated structure            | Chosen: Provides rapid development for complex domain logic (procurement) and strong ecosystem support for production features like Celery integration. |
| FastAPI      | Extremely fast, modern async-first, automatic OpenAPI docs           | Less built-in tooling (no ORM, no admin panel)                       | Not chosen: We need robust domain modeling and background tasks — Django + DRF covers this better out of the box. |
| Flask        | Very lightweight, maximum flexibility                                 | Requires building almost everything from scratch                     | Not chosen: Too minimal for a system with agents, pipelines, and future scalability needs. |

**Trade-off accepted**: Slightly slower cold-start in exchange for faster feature development and better long-term maintainability.

## 2. Web Crawling Library: Crawl4AI vs Firecrawl vs Playwright + BeautifulSoup

| Option                  | Pros                                                                 | Cons                                                                 | Decision & Rationale                                                                 |
|-------------------------|----------------------------------------------------------------------|----------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| Crawl4AI                | Async-first, designed for LLM/RAG use-cases, structured extraction, open-source | Still relatively young project, fewer battle-tested examples         | Chosen: Excellent balance of async performance, LLM-friendly output, and no vendor lock-in. |
| Firecrawl               | Very reliable JS rendering, clean markdown output, paid API available | Requires API key (even self-hosted version has limits), less flexible | Not chosen: Prefer fully self-hosted and open-source solution for control and cost. |
| Playwright + BeautifulSoup | Maximum control, full browser emulation, no external dependencies   | More boilerplate code, manual cleanup and extraction logic           | Not chosen: Crawl4AI already wraps Playwright and adds LLM-ready extraction — no need to reinvent. |

**Trade-off accepted**: Slightly higher risk from a younger library in exchange for better LLM integration and lower maintenance overhead.

## 3. Database: PostgreSQL vs SQLite vs MongoDB

| Option       | Pros                                                                 | Cons                                                                 | Decision & Rationale                                                                 |
|--------------|----------------------------------------------------------------------|----------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| PostgreSQL   | Strong relational integrity, JSONB support, full-text search, mature ecosystem | Requires separate service (more setup than SQLite)                   | Chosen: Procurement domain benefits from structured relations (products, suppliers, searches) + JSONB for flexible result storage. |
| SQLite       | Zero-config, embedded, great for local dev                           | Not suitable for production concurrency or scaling                   | Not chosen: Project targets production readiness — PostgreSQL is the right long-term choice. |
| MongoDB      | Flexible schema, good for unstructured data                          | Weaker relational integrity, higher operational complexity           | Not chosen: Core entities are relational; JSONB in PostgreSQL covers flexible parts without losing structure. |

**Trade-off accepted**: More setup complexity in development in exchange for production-grade reliability and query performance.

## 4. LLM Orchestration: LangChain vs LlamaIndex vs Custom

| Option       | Pros                                                                 | Cons                                                                 | Decision & Rationale                                                                 |
|--------------|----------------------------------------------------------------------|----------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| LangChain    | Rich ecosystem, tool calling, memory, chains, wide provider support  | Can become abstraction-heavy, occasional breaking changes            | Chosen (partial): Using core concepts (chains, tools) but avoiding over-abstraction. |
| LlamaIndex   | Excellent for RAG-heavy use-cases, indexing, retrieval               | Less focused on agentic/tool-calling workflows                       | Not chosen: Our primary need is agent reasoning + tool calling, not heavy indexing. |
| Custom       | Full control, minimal dependencies                                   | Reinventing many wheels                                              | Partial: We build custom pipelines on top of LangChain primitives for clarity. |

**Trade-off accepted**: Some dependency on LangChain in exchange for faster prototyping of agent flows.

## 5. Deployment Target: Docker Compose vs Kubernetes from Day One

| Option                  | Pros                                                                 | Cons                                                                 | Decision & Rationale                                                                 |
|-------------------------|----------------------------------------------------------------------|----------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| Docker Compose only     | Simple, fast local & staging, low learning curve                     | Limited production scaling & observability                           | Chosen for MVP: Sufficient for development and demo. |
| Kubernetes + Helm early | Full production readiness, autoscaling, observability                | High complexity for solo developer, steep learning curve             | Planned (demonstration only): Manifests included to show production thinking, not required for local use. |

**Trade-off accepted**: Faster iteration in early phases in exchange for deferred production complexity.

## Summary of Philosophy
We prioritize:
- Development velocity in early phases
- Production readiness as a demonstrated capability (not immediate requirement)
- Open-source and self-hosted tools where possible
- Transparency of decisions and trade-offs

All choices are documented and can be revisited as the project evolves.

Last updated: February 11, 2026