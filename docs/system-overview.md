# System Overview

## Big Picture
BuySmart Agent is designed to be his own platform for procurement automation.

## Domain Boundaries
- **Procurement**: Core domain for managing RFQs, bids, and vendor selection.
- **Intelligence**: LLM-driven analysis and strategy.
- **Platform**: Infrastructure, observability, and security.

## Ownership Assumptions
The platform team owns the `platform/` directory, while domain experts focus on `backend/src/domains/`.
