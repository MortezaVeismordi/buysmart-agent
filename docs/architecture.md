# System Architecture

## Context Map
The BuySmart Agent interacts with vendors, internal procurement teams, and various data sources.

```mermaid
graph TD
    User((Procurement Team)) --> BSA[BuySmart Agent]
    BSA --> Web[Web Crawlers]
    BSA --> LLM[LLM Services]
    BSA --> DB[(System Database)]
    Web --> Vendors[Vendor Sites]
```

## Containers
- **Frontend**: Dashboard for users to monitor agent activity.
- **Backend API**: Django-driven core logic and domain services.
- **Agent Workers**: Autonomous agents running specialized tasks.
- **Data Store**: Postgres + Redis.
