"""
Query Parser Module
Uses OpenRouter to access Claude and other LLMs for parsing natural language queries.
"""

import json
import os
import re
import logging
from typing import Any
from urllib.parse import quote_plus
import requests

logger = logging.getLogger(__name__)

# System prompt for query parsing
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
    Parses natural language product queries using OpenRouter API.
    Supports multiple LLM providers through OpenRouter.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Initialize the QueryParser with OpenRouter credentials.

        Args:
            api_key: OpenRouter API key. Falls back to OPENROUTER_API_KEY env var.
            model: Model to use. Defaults to claude-3.5-sonnet via OpenRouter.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key is required. Set OPENROUTER_API_KEY environment "
                "variable or pass api_key parameter."
            )
        
        # Default to Claude 3.5 Sonnet via OpenRouter
        self.model = model or os.getenv(
            "OPENROUTER_MODEL", 
            "anthropic/claude-3.5-sonnet"
        )
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    def parse_query(self, query_text: str) -> dict[str, Any]:
        """
        Parse a natural language product query into structured intent.

        Args:
            query_text: The user's natural language query.

        Returns:
            Dictionary with parsed intent fields.

        Raises:
            ValueError: If the query cannot be parsed.
        """
        try:
            logger.info(f"Parsing query: {query_text[:100]}...")
            
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://buysmart-agent.local",  # Optional
                    "X-Title": "BuySmart Agent"  # Optional
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": QUERY_PARSE_SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": f"Parse this product search query: {query_text}"
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000
                },
                timeout=30
            )
            
            response.raise_for_status()
            raw_content = response.json()["choices"][0]["message"]["content"]
            parsed = self._extract_json(raw_content)

            # Ensure search_queries exists
            if "search_queries" not in parsed:
                parsed["search_queries"] = self._generate_fallback_queries(query_text)

            logger.info(
                f"Successfully parsed query. "
                f"Product type: {parsed.get('product_type', 'unknown')}"
            )
            return parsed

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API error while parsing query: {e}")
            raise ValueError(f"Failed to parse query: {e}") from e
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse OpenRouter response: {e}")
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
            urls.append(f"https://www.amazon.com/s?k={encoded_query}")

            # Best Buy search URL
            urls.append(f"https://www.bestbuy.com/site/searchpage.jsp?st={encoded_query}")

        logger.info(f"Generated {len(urls)} search URLs from parsed intent.")
        return urls

    def _extract_json(self, raw_text: str) -> dict[str, Any]:
        """
        Extract JSON from LLM response, handling markdown code blocks.

        Args:
            raw_text: Raw text response from LLM.

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

        # Try extracting from markdown code blocks
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