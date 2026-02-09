# Architecture Decision Records (ADR)

## ADR 001: Project Structure
**Status**: Decided
**Context**: We need a structured repository that supports scaling both domain logic and platform infrastructure.
**Decision**: Follow the "Internal Platform" pattern with a clear separation between `backend`, `frontend`, and `platform`.
**Consequences**: Increased initial complexity but better long-term maintainability.
