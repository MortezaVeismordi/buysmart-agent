"""
Query Parser Module
Uses Anthropic Claude to parse natural language product queries
into structured search intent.
"""

import json
import os
import re
import logging
from typing import Any
from urllib.parse import quote_plus

import anthropic

logger = logging.getLogger(__name__)

# System prompt for Claude to extract structured intent from queries
QUERY_PARSE_SYSTEM_PROMPT = """You are a product search query parser. Your job is to extract structured intent from natural language product queries.

Given a user query, extract the following fields and return ONLY valid JSON (no markdown, no explanation):

{
    "product_type": "the main product category",
    "price_min": null or number,
    "price_max": null or number,
    "use_case": "primary use case or null",
    "requirements": ["list", "of", "must-have", "features"],
    "preferences": ["list", "of", "nice-to-have", "features"],
    "brand_preference": "preferred brand or null",
    "search_queries": ["3 to 5 optimized search queries for e-commerce sites"]
}

Rules:
- Extract price constraints from phrases like "under $200", "between $50 and $100"
- Identify use cases from context (e.g., "for gaming", "for office work")
- Separate hard requirements from soft preferences
- Generate 3-5 diverse search queries that cover different aspects of the request
- Return ONLY valid JSON, no additional text or markdown formatting
"""


class QueryParser:
    """
    Parses natural language product queries using Anthropic Claude.

    Extracts structured intent including product type, price range,
    use case, requirements, and generates optimized search queries.
    """

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize the QueryParser with Anthropic API credentials.

        Args:
            api_key: Anthropic API key. Falls back to ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key is required. Set ANTHROPIC_API_KEY environment "
                "variable or pass api_key parameter."
            )
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-sonnet-4-20250514"

    def parse_query(self, query_text: str) -> dict[str, Any]:
        """
        Parse a natural language product query into structured intent.

        Args:
            query_text: The user's natural language query.

        Returns:
            Dictionary with parsed intent fields.

        Raises:
            ValueError: If the query cannot be parsed.
            anthropic.APIError: If the API call fails.
        """
        try:
            logger.info(f"Parsing query: {query_text[:100]}...")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=QUERY_PARSE_SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": f"Parse this product search query: {query_text}",
                    }
                ],
            )

            raw_content = response.content[0].text
            parsed = self._extract_json(raw_content)

            # Ensure search_queries exists
            if "search_queries" not in parsed:
                parsed["search_queries"] = self._generate_fallback_queries(query_text)

            logger.info(
                f"Successfully parsed query. "
                f"Product type: {parsed.get('product_type', 'unknown')}"
            )
            return parsed

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error while parsing query: {e}")
            raise
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse Claude response: {e}")
            raise ValueError(f"Could not parse query response: {e}") from e

    def generate_search_urls(self, parsed_intent: dict[str, Any]) -> list[str]:
        """
        Generate e-commerce search URLs from parsed intent.

        Creates search URLs for Amazon and Best Buy based on the
        extracted search queries.

        Args:
            parsed_intent: Dictionary with parsed query intent.

        Returns:
            List of search URLs for crawling.
        """
        urls: list[str] = []
        search_queries = parsed_intent.get("search_queries", [])

        if not search_queries:
            logger.warning("No search queries in parsed intent.")
            return urls

        for query in search_queries[:5]:
            encoded_query = quote_plus(query)

            # Amazon search URL
            urls.append(
                f"https://www.amazon.com/s?k={encoded_query}"
            )

            # Best Buy search URL
            urls.append(
                f"https://www.bestbuy.com/site/searchpage.jsp?st={encoded_query}"
            )

        logger.info(f"Generated {len(urls)} search URLs from parsed intent.")
        return urls

    def _extract_json(self, raw_text: str) -> dict[str, Any]:
        """
        Extract JSON from Claude's response, handling markdown code blocks.

        Args:
            raw_text: Raw text response from Claude.

        Returns:
            Parsed JSON dictionary.

        Raises:
            ValueError: If no valid JSON can be extracted.
        """
        # Try direct JSON parsing first
        try:
            return json.loads(raw_text.strip())
        except json.JSONDecodeError:
            pass

        # Try extracting from markdown code blocks (```json ... ``` or ``` ... ```)
        code_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
        matches = re.findall(code_block_pattern, raw_text, re.DOTALL)
        if matches:
            return json.loads(matches[0].strip())

        # Try finding JSON object pattern
        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        matches = re.findall(json_pattern, raw_text, re.DOTALL)
        if matches:
            return json.loads(matches[0])

        raise ValueError(f"Could not extract valid JSON from response: {raw_text[:200]}")

    def _generate_fallback_queries(self, query_text: str) -> list[str]:
        """
        Generate basic search queries as a fallback.

        Args:
            query_text: Original user query.

        Returns:
            List of search query strings.
        """
        base_query = query_text.strip()
        return [
            base_query,
            f"best {base_query}",
            f"{base_query} top rated",
        ]
