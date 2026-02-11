# System Architecture

BuySmart Agent is designed as a modular, production-ready AI system following clean architecture principles, domain-driven design (DDD), and separation of concerns. The architecture supports evolution from an MVP to a scalable, observable platform.

## High-Level Context (C4 Level 1 – System Context)

```mermaid
graph TD
    User["User / Buyer"] -->|Natural Language Query\nCriteria & Preferences| Dashboard["Frontend Dashboard"]
    Dashboard -->|REST API| Backend["Backend Service\n(Django + DRF)"]
    Backend -->|Orchestrate| Agent["Buying Agent Layer"]
    Agent -->|Tool Call| Crawler["Crawl4AI\nAsync Web Crawler"]
    Agent -->|Reasoning & Extraction| LLM["LLM Provider\n(Claude / GPT-4o / Groq)"]
    Crawler -->|Raw / Structured Data| Agent
    Agent -->|Ranked Results & Rationale| Backend
    Backend -->|JSON Response| Dashboard
    Backend <-->|Persistence| Database["PostgreSQL"]
    Backend <-->|Async Tasks & Caching| Redis["Redis\n(Celery + Caching)"]