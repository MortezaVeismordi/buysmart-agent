# System Overview

## Purpose of the system

BuySmart Agent is a buyer-side decision support system designed to assist users in finding, comparing, and evaluating products across multiple online marketplaces.

The system does not aim to replace marketplaces or act as a transactional layer. Instead, it functions as an **independent reasoning layer** that aggregates public information, structures it, and applies explicit decision logic aligned with user intent.

---

## Primary user interaction model

The system is driven by a single high-level interaction:

> A user expresses a purchasing intent in natural language, including constraints and preferences.

Example:
- Product category
- Budget constraints
- Technical requirements
- Soft preferences (brand trust, delivery speed, seller reputation)

The system is responsible for translating this intent into:
- Search and discovery actions
- Data extraction and normalization
- Comparison and ranking
- A transparent, reasoned recommendation

---

## Supported data sources (initial scope)

The initial version of the system focuses on a limited and explicit set of sources:

- Torob (ترب)
- Emalls (ایمالز)
- (Optional / future) Digikala

These sources are selected because:
- They aggregate multiple sellers
- They expose rich product and pricing metadata
- They represent realistic constraints of regional e-commerce ecosystems

The system assumes **read-only interaction** with these platforms via publicly accessible pages.

---

## High-level system flow

At a conceptual level, the system operates as a staged pipeline:

1. **Intent interpretation**
   - User input is parsed and normalized into a structured intent model.
   - Hard constraints and soft preferences are separated explicitly.

2. **Targeted web exploration**
   - Relevant listing and product pages are identified per source.
   - Crawling is constrained by source-specific rules and limits.

3. **Data extraction and structuring**
   - Raw HTML is processed using Crawl4AI.
   - The output is converted into a normalized, source-agnostic schema.

4. **LLM-based reasoning**
   - Structured data and user intent are passed to an LLM via OpenRouter.
   - The model performs comparison, trade-off analysis, and ranking.
   - The output includes both recommendations and reasoning artifacts.

5. **Result presentation**
   - Ranked options are returned to the user.
   - The system exposes the reasoning behind each recommendation.

---

## Role of Crawl4AI

Crawl4AI is used as an **intelligent extraction layer**, not as a generic crawler.

Its responsibilities are limited to:
- Rendering dynamic pages when necessary
- Extracting relevant product attributes
- Producing a clean, structured intermediate representation

Crawl4AI is explicitly **not responsible for decision-making or ranking**.

This separation ensures that:
- Crawling logic remains deterministic
- AI reasoning remains inspectable and replaceable

---

## Role of the LLM (via OpenRouter)

The LLM acts as a **reasoning engine**, not a source of truth.

Its responsibilities include:
- Interpreting user intent relative to available options
- Evaluating trade-offs between price, features, and constraints
- Producing human-readable explanations for its choices

The system assumes:
- LLM outputs may be probabilistic
- All inputs to the LLM are structured and auditable
- Final decisions can be overridden or constrained by deterministic rules

---

## System boundaries and non-responsibilities

The system explicitly does not:
- Perform authentication or actions on third-party marketplaces
- Guarantee price accuracy beyond crawl time
- Act as a payment processor or checkout proxy
- Scrape private or authenticated content

These boundaries are intentional and documented to avoid scope creep.

---

## Key assumptions

- Public marketplace pages can be accessed without authentication
- Product comparison can be reasonably approximated from available metadata
- Users value explainability over purely optimized pricing
- Partial or stale data is preferable to opaque recommendations

When these assumptions fail, the system should degrade gracefully.

---

## Failure modes and constraints

The system is designed with awareness of:
- Source layout changes
- Rate limits and crawling failures
- Incomplete or inconsistent product metadata
- Ambiguous or underspecified user intent

Handling these cases is part of the system design, not an afterthought.

---

## Evolution path

The current system is intentionally scoped to a small number of sources and use cases.

Future extensions may include:
- Additional marketplaces
- Price history tracking
- Alerting and monitoring workflows
- Deeper personalization and preference learning

These are treated as extensions, not core dependencies.

---

## Summary

BuySmart Agent is structured as a layered system with clear responsibilities:

- Crawling extracts data
- LLMs reason over structured inputs
- Domain logic enforces boundaries and intent
- Infrastructure supports scalability without dictating design

This separation is central to the system’s long-term maintainability and credibility.
