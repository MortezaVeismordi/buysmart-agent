# System Architecture

BuySmart Agent is designed as a modular, production-ready AI system following clean architecture principles, domain-driven design (DDD), and separation of concerns. The architecture supports evolution from an MVP to a scalable, observable platform.

## High-Level Context (C4 Level 1 – System Context)

```mermaid
graph TD
    User[User / Buyer] -->|Natural Language Query<br>Criteria & Preferences| Dashboard[Frontend Dashboard]
    Dashboard -->|REST / WebSocket| Backend[Backend Service<br>(Django + DRF)]
    Backend -->|Orchestration & Reasoning| Agent[Buying Agent Layer]
    Agent -->|Web Tool Call| Crawler[Crawl4AI<br>Async Web Crawler]
    Agent -->|LLM Reasoning & Extraction| LLM[External LLM Provider<br>Claude / GPT-4o / Groq]
    Crawler -->|Raw HTML / Structured Data| Agent
    Agent -->|Ranked Results & Rationale| Backend
    Backend -->|JSON Response| Dashboard
    Backend <-->|Persistence| Database[(PostgreSQL)]
    Backend <-->|Async Tasks & Caching| Redis[(Redis)]