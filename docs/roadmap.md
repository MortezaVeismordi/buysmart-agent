# Project Roadmap

This roadmap outlines the phased development of BuySmart Agent, an AI-powered buy-side procurement agent.  
Phases are prioritized based on delivering core value early while building toward production readiness and scalability.

## Phase 1 – Foundation & Structure (Completed)
- Repository structure following clean architecture principles  
- Domain model definition (procurement domain)  
- Initial separation of concerns: backend, frontend, platform, configs, data  
- Basic documentation foundation: index.md, system-overview.md, repo-guide.md  
- GitHub workflows: CI, linting, testing, security scanning  
- pre-commit hooks and basic tooling setup  

Status: Completed (as of February 2026)

## Phase 2 – Core Agent Functionality (In Progress)
- Web crawling pipeline using Crawl4AI (async, JavaScript-capable, structured extraction)  
- LLM integration layer (Claude / GPT-4o / Groq) with tool calling and reasoning chains  
- Basic agent orchestration: query → crawl → extract → enrich → rank → response  
- Backend API endpoints for search initiation and result retrieval (Django + DRF)  
- Initial data persistence for search history and comparison results (PostgreSQL)  
- Rate limiting, caching, and error handling for external services (LLM + crawling)  

Status: In progress (core crawling and LLM reasoning currently under active development)

## Phase 3 – User-Facing Features & Polish (Planned – Short Term)
- Frontend dashboard: natural language query input, comparison tables, ranked results view  
- Chat-style interface for iterative refinement of queries and criteria  
- Result visualization: price trends, supplier scoring, decision rationale display  
- Export functionality (CSV, PDF) for comparison reports  
- Basic authentication and user session management  
- Live demo deployment (Render, Railway, or Vercel) with public access  

Status: □ Planned (target: Q1–Q2 2026)

## Phase 4 – Production Readiness & Scalability (Planned – Medium Term)
- Full observability stack: structured logging, metrics (Prometheus), dashboards (Grafana)  
- Production-grade deployment: Kubernetes manifests, Helm chart, autoscaling  
- Security hardening: secrets management, threat modeling, scraping ethics compliance  
- Multi-user support with role-based access control  
- Monitoring and alerting for LLM/crawling failures and cost spikes  
- Performance benchmarks and optimization (response time, throughput, cost per query)  

Status: □ Planned (target: Q3 2026)

## Phase 5 – Advanced Capabilities & Ecosystem Integration (Long Term / Future)
- Multi-source enrichment (reviews, supplier ratings, delivery estimates)  
- Personalization engine (user preferences, purchase history memory)  
- Alerting system (price drop notifications, stock availability)  
- Integration with external procurement systems (ERP/CRM APIs)  
- Open-source contributions and community extensions  

Status: □ Long-term vision (post-2026, subject to validation and resources)

## Notes
- Priorities may shift based on user feedback, technical discoveries, or external dependencies (e.g., LLM provider changes, legal scraping considerations).  
- All phases include automated testing (unit, integration, end-to-end) and documentation updates.  
- Production features (Kubernetes, Helm, full observability) are included as demonstration of readiness, not as immediate requirements for local development.

Last updated: February 11, 2026