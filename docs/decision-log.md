# Architecture Decision Log (ADRs)

This document serves as a lightweight Architecture Decision Record (ADR) log for BuySmart Agent.  
Each entry captures a significant architectural or technical decision, the context, considered options, chosen solution, and consequences.

Decisions are numbered sequentially and kept concise. New ADRs are added as meaningful choices are made.

## ADR-001: Adoption of Django as Primary Backend Framework

**Date:** February 2026  
**Status:** Accepted

**Context**  
The project requires a robust backend capable of handling complex domain logic (procurement entities, workflows, search history), background tasks (crawling, LLM calls), relational data modeling, and future authentication/authorization needs.

**Considered Options**  
- Django: Full-featured framework with ORM, migrations, admin, security defaults, and strong Celery integration.  
- FastAPI: Modern, async-first, excellent OpenAPI docs, but minimal built-in tooling.  
- Flask: Lightweight and flexible, but requires building most features manually.

**Decision**  
Use Django + Django REST Framework (DRF) as the core backend framework.

**Rationale**  
Django provides the highest development velocity for domain-heavy applications with relational data and background processing. DRF handles REST API needs effectively. The batteries-included nature reduces boilerplate for authentication, migrations, and admin interfaces (useful for internal tooling).

**Consequences**  
- Positive: Faster implementation of business rules, easier scaling with Celery/Redis, mature ecosystem.  
- Negative: Slightly heavier runtime footprint and more opinionated structure compared to FastAPI.  
- Mitigated by: Following clean architecture to keep domain logic framework-agnostic where possible.

## ADR-002: Selection of Crawl4AI for Web Crawling

**Date:** February 2026 
**Status:** Accepted

**Context**  
The agent requires reliable, async-capable web crawling with JavaScript rendering support and structured output suitable for LLM consumption (markdown or JSON).

**Considered Options**  
- Crawl4AI: Async-first, LLM/RAG optimized, open-source, Playwright-based.  
- Firecrawl: High-quality markdown output, but API-key dependent even in self-hosted mode.  
- Playwright + BeautifulSoup/trafilatura: Maximum control, but high maintenance.

**Decision**  
Adopt Crawl4AI as the primary crawling engine.

**Rationale**  
Crawl4AI offers the best balance of async performance, LLM-friendly extraction strategies, and zero vendor lock-in. It wraps Playwright for JS rendering while providing higher-level abstractions for structured output.

**Consequences**  
- Positive: Reduced custom code for extraction and cleanup, better integration with agent reasoning layer.  
- Negative: Younger project with potentially fewer edge-case battle-tests.  
- Mitigated by: Fallback mechanisms (direct Playwright if needed) and monitoring crawl success rates.

## ADR-003: Use of PostgreSQL with JSONB for Persistence

**Date:** February 2026  
**Status:** Accepted

**Context**  
The system needs to store structured entities (products, suppliers, queries) while handling flexible, semi-structured LLM/crawl results.

**Considered Options**  
- PostgreSQL: Strong relational model, JSONB for flexible fields, full-text search.  
- SQLite: Zero-config for local dev, but poor concurrency/scaling.  
- MongoDB: Native document store, but weaker relational integrity.

**Decision**  
Use PostgreSQL as the primary database, leveraging JSONB columns for flexible result storage.

**Rationale**  
Procurement domain benefits from relational integrity (products ↔ suppliers ↔ searches). JSONB provides document-like flexibility without sacrificing query power or transactions.

**Consequences**  
- Positive: Strong data consistency, advanced querying, production-grade scalability.  
- Negative: Requires running a separate database service (more setup than SQLite).  
- Mitigated by: Docker Compose for local development and clear separation in configs.

## ADR-004: Agent Orchestration via Custom Pipelines + LangChain Primitives

**Date:** February 2026  
**Status:** Accepted

**Context**  
The buying agent needs reliable orchestration of tools (crawling), LLM reasoning, and multi-step pipelines.

**Considered Options**  
- Full LangChain: Rich agent/tool ecosystem, but abstraction-heavy.  
- LlamaIndex: Strong for RAG, weaker for agentic/tool flows.  
- Fully custom: Maximum control, high implementation cost.

**Decision**  
Build custom pipelines using LangChain primitives (chains, tools, memory) rather than full high-level agents.

**Rationale**  
Custom pipelines provide transparency and control over the exact flow (parse → crawl → extract → rank). LangChain primitives accelerate implementation without over-abstraction.

**Consequences**  
- Positive: Clearer debugging, easier testing, less magic.  
- Negative: Slightly more code than using high-level LangChain agents.  
- Mitigated by: Reusing tested LangChain components (prompt templates, output parsers).

## Summary
This log will be updated as significant decisions are made.  
All ADRs follow the principle of documenting context, alternatives, and consequences to support future maintainers and reviewers.

Last updated: February 11, 2026