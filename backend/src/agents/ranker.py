"""
Product Ranker Module
Uses OpenRouter to access Claude and other LLMs for ranking products.
"""

import json
import logging
import os
import re
from typing import Any
import requests

logger = logging.getLogger(__name__)

RANKING_SYSTEM_PROMPT = """You are an expert product comparison analyst. Your job is to objectively analyze and rank products based on the user's requirements.

Given a list of products and the user's original query with parsed intent, rank each product and provide detailed analysis.

Return ONLY valid JSON (no markdown, no explanation) in this format:

{
    "rankings": [
        {
            "product_index": 0,
            "product_name": "Product Name",
            "score": 85,
            "pros": ["Pro 1", "Pro 2", "Pro 3"],
            "cons": ["Con 1", "Con 2"],
            "reasoning": "Brief explanation of why this product ranked here",
            "price_value_rating": "excellent|good|fair|poor",
            "recommendation": "Brief recommendation for this product"
        }
    ],
    "overall_summary": "Overall comparison summary",
    "best_overall": "Name of best overall product",
    "best_value": "Name of best value product",
    "comparison_notes": "Additional comparison notes"
}

Scoring criteria (total 100 points):
- Price/Value: 25 points
- Features Match: 25 points
- Quality/Rating: 20 points
- Brand Reputation: 15 points
- Availability: 15 points

Rules:
- Score each product 0-100
- Be objective about pros/cons
- Consider user's requirements and budget
- Rank from highest to lowest score
- Return ONLY valid JSON
"""


class ProductRanker:
    """
    Ranks and compares products using OpenRouter API.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None):
        """
        Initialize the ProductRanker.

        Args:
            api_key: OpenRouter API key. Falls back to OPENROUTER_API_KEY env var.
            model: Model to use. Defaults to Claude 3.5 Sonnet.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OpenRouter API key is required. Set OPENROUTER_API_KEY environment "
                "variable or pass api_key parameter."
            )
        
        self.model = model or os.getenv(
            "OPENROUTER_MODEL",
            "anthropic/claude-3.5-sonnet"
        )
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    def rank_products(
        self,
        products: list[dict[str, Any]],
        user_query: str,
        parsed_intent: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Rank a list of products based on user query and parsed intent.

        Args:
            products: List of product dictionaries from the crawler.
            user_query: Original natural language query.
            parsed_intent: Structured intent from the QueryParser.

        Returns:
            Dictionary with rankings, scores, and analysis.
        """
        if not products:
            logger.warning("No products to rank.")
            return {
                "rankings": [],
                "overall_summary": "No products found to compare.",
                "best_overall": None,
                "best_value": None,
                "comparison_notes": "No products were available for comparison.",
            }

        try:
            logger.info(f"Ranking {len(products)} products for query: {user_query[:80]}")

            products_text = self._format_products_for_llm(products)

            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://buysmart-agent.local",
                    "X-Title": "BuySmart Agent"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": RANKING_SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": (
                                f"User Query: {user_query}\n\n"
                                f"Parsed Intent: {json.dumps(parsed_intent, indent=2)}\n\n"
                                f"Products to rank:\n{products_text}"
                            )
                        }
                    ],
                    "temperature": 0.3,
                    "max_tokens": 4000
                },
                timeout=60
            )

            response.raise_for_status()
            raw_content = response.json()["choices"][0]["message"]["content"]
            ranking_result = self._extract_json(raw_content)

            # Sort rankings by score
            if "rankings" in ranking_result:
                ranking_result["rankings"].sort(
                    key=lambda x: x.get("score", 0), reverse=True
                )

            logger.info(
                f"Ranking complete. Best overall: "
                f"{ranking_result.get('best_overall', 'N/A')}"
            )
            return ranking_result

        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API error during ranking: {e}")
            raise ValueError(f"Failed to rank products: {e}") from e
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse ranking response: {e}")
            raise ValueError(f"Could not parse ranking response: {e}") from e

    def generate_comparison_summary(
        self,
        products: list[dict[str, Any]],
        rankings: dict[str, Any],
        user_query: str,
    ) -> str:
        """
        Generate a markdown-formatted comparison summary.

        Args:
            products: List of product dictionaries.
            rankings: Ranking results from rank_products().
            user_query: Original user query.

        Returns:
            Markdown-formatted comparison summary string.
        """
        try:
            products_text = self._format_products_for_llm(products)
            rankings_text = json.dumps(rankings, indent=2)

            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Create a comprehensive markdown comparison summary."
                        },
                        {
                            "role": "user",
                            "content": (
                                f"User Query: {user_query}\n\n"
                                f"Products:\n{products_text}\n\n"
                                f"Rankings:\n{rankings_text}\n\n"
                                "Please create a comprehensive markdown comparison summary."
                            )
                        }
                    ],
                    "max_tokens": 2000
                },
                timeout=30
            )

            summary = response.json()["choices"][0]["message"]["content"]
            logger.info("Comparison summary generated successfully.")
            return summary

        except Exception as e:
            logger.error(f"Error generating comparison summary: {e}")
            return self._generate_fallback_summary(rankings)

    def _format_products_for_llm(self, products: list[dict[str, Any]]) -> str:
        """Format product list into readable text for the LLM."""
        formatted_parts: list[str] = []
        for i, product in enumerate(products):
            part = (
                f"Product {i + 1}:\n"
                f"  Name: {product.get('name', 'Unknown')}\n"
                f"  Price: {product.get('price', 'N/A')} {product.get('currency', 'USD')}\n"
                f"  Rating: {product.get('rating', 'N/A')}/5 "
                f"({product.get('review_count', 'N/A')} reviews)\n"
                f"  Features: {', '.join(product.get('features', []))}\n"
                f"  Availability: {product.get('availability', 'Unknown')}\n"
                f"  Source: {product.get('source_domain', 'Unknown')}\n"
            )
            formatted_parts.append(part)
        return "\n".join(formatted_parts)

    def _extract_json(self, raw_text: str) -> dict[str, Any]:
        """Extract JSON from LLM response."""
        try:
            return json.loads(raw_text.strip())
        except json.JSONDecodeError:
            pass

        # Try markdown code blocks
        code_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
        matches = re.findall(code_block_pattern, raw_text, re.DOTALL)
        if matches:
            return json.loads(matches[0].strip())

        # Try JSON object pattern
        json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
        matches = re.findall(json_pattern, raw_text, re.DOTALL)
        if matches:
            for match in sorted(matches, key=len, reverse=True):
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue

        raise ValueError(f"Could not extract valid JSON from response: {raw_text[:200]}")

    def _generate_fallback_summary(self, rankings: dict[str, Any]) -> str:
        """Generate basic summary when LLM summary fails."""
        lines = ["# Product Comparison Summary\n"]

        if rankings.get("best_overall"):
            lines.append(f"**Best Overall:** {rankings['best_overall']}\n")
        if rankings.get("best_value"):
            lines.append(f"**Best Value:** {rankings['best_value']}\n")

        if rankings.get("rankings"):
            lines.append("\n## Rankings\n")
            for rank_info in rankings["rankings"]:
                name = rank_info.get("product_name", "Unknown")
                score = rank_info.get("score", "N/A")
                lines.append(f"- **{name}** — Score: {score}/100")
                if rank_info.get("reasoning"):
                    lines.append(f"  - {rank_info['reasoning']}")

        return "\n".join(lines)