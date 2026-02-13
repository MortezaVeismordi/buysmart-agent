"""
Product Crawler Module
Uses Crawl4AI's AsyncWebCrawler to scrape product data from e-commerce sites.
Provides both async and sync interfaces for Django integration.
"""

import asyncio
import json
import logging
import os
import re
from typing import Any
from urllib.parse import urlparse

from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import LLMExtractionStrategy

logger = logging.getLogger(__name__)

# Schema instruction for the LLM extraction
PRODUCT_EXTRACTION_INSTRUCTION = """
Extract product information from this e-commerce page. For each product found,
extract the following fields and return as a JSON array:

[
    {
        "name": "Full product name",
        "price": 99.99,
        "currency": "USD",
        "url": "full product URL",
        "image_url": "product image URL or null",
        "rating": 4.5,
        "review_count": 1234,
        "features": ["feature 1", "feature 2", "feature 3"],
        "availability": "in stock" or "out of stock" or "unknown"
    }
]

Rules:
- Extract ALL products visible on the page
- Price should be a number without currency symbols
- Rating should be on a 0-5 scale
- Features should be a list of key product features/specs
- Return ONLY valid JSON array, no additional text
- If a field cannot be determined, use null
"""


class ProductCrawler:
    """
    Async product crawler using Crawl4AI.

    Crawls e-commerce URLs and extracts structured product data
    using LLM-powered extraction.
    """

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize the ProductCrawler.

        Args:
            api_key: Anthropic API key for LLM extraction.
                     Falls back to ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Anthropic API key is required. Set ANTHROPIC_API_KEY environment "
                "variable or pass api_key parameter."
            )

    async def crawl_urls(self, urls: list[str]) -> list[dict[str, Any]]:
        """
        Crawl a list of URLs and extract product data.

        Args:
            urls: List of e-commerce URLs to crawl.

        Returns:
            List of dictionaries containing crawl results with extracted products.
            Each result has: url, domain, success, products, error.
        """
        results: list[dict[str, Any]] = []

        extraction_strategy = LLMExtractionStrategy(
            provider="anthropic/claude-sonnet-4-20250514",
            api_token=self.api_key,
            instruction=PRODUCT_EXTRACTION_INSTRUCTION,
        )

        async with AsyncWebCrawler(verbose=False) as crawler:
            for i, url in enumerate(urls):
                if i > 0:
                    # Delay between requests to be respectful
                    await asyncio.sleep(2)

                result = await self._crawl_single_url(
                    crawler, url, extraction_strategy
                )
                results.append(result)

        total_products = sum(len(r.get("products", [])) for r in results)
        successful = sum(1 for r in results if r["success"])
        logger.info(
            f"Crawl complete: {successful}/{len(urls)} URLs successful, "
            f"{total_products} total products extracted."
        )
        return results

    async def _crawl_single_url(
        self,
        crawler: AsyncWebCrawler,
        url: str,
        extraction_strategy: LLMExtractionStrategy,
    ) -> dict[str, Any]:
        """
        Crawl a single URL and extract products.

        Args:
            crawler: The AsyncWebCrawler instance.
            url: URL to crawl.
            extraction_strategy: LLM extraction strategy to use.

        Returns:
            Dictionary with url, domain, success flag, products list, and error.
        """
        domain = urlparse(url).netloc
        logger.info(f"Crawling: {url}")

        try:
            crawl_result = await crawler.arun(
                url=url,
                extraction_strategy=extraction_strategy,
            )

            if not crawl_result.success:
                logger.warning(f"Crawl failed for {url}: {crawl_result.error_message}")
                return {
                    "url": url,
                    "domain": domain,
                    "success": False,
                    "products": [],
                    "error": crawl_result.error_message or "Crawl failed",
                }

            products = self._parse_extracted_content(
                crawl_result.extracted_content, domain
            )
            logger.info(f"Extracted {len(products)} products from {domain}")

            return {
                "url": url,
                "domain": domain,
                "success": True,
                "products": products,
                "error": None,
            }

        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return {
                "url": url,
                "domain": domain,
                "success": False,
                "products": [],
                "error": str(e),
            }

    def _parse_extracted_content(
        self, content: str | None, domain: str
    ) -> list[dict[str, Any]]:
        """
        Parse the LLM-extracted content into structured product data.

        Args:
            content: Raw extracted content string from crawl4ai.
            domain: Source domain for the products.

        Returns:
            List of product dictionaries.
        """
        if not content:
            return []

        try:
            # Try direct JSON parsing
            products = json.loads(content)
        except json.JSONDecodeError:
            # Try extracting from markdown code blocks
            try:
                code_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
                matches = re.findall(code_block_pattern, content, re.DOTALL)
                if matches:
                    products = json.loads(matches[0].strip())
                else:
                    # Try finding JSON array pattern
                    array_pattern = r"\[.*\]"
                    matches = re.findall(array_pattern, content, re.DOTALL)
                    if matches:
                        products = json.loads(matches[0])
                    else:
                        logger.warning(
                            f"Could not parse extracted content from {domain}"
                        )
                        return []
            except (json.JSONDecodeError, IndexError) as e:
                logger.warning(f"JSON parse error for {domain}: {e}")
                return []

        # Ensure we have a list
        if isinstance(products, dict):
            products = [products]
        elif not isinstance(products, list):
            return []

        # Enrich each product with source domain
        for product in products:
            if isinstance(product, dict):
                product["source_domain"] = domain
                # Ensure required fields exist with defaults
                product.setdefault("name", "Unknown Product")
                product.setdefault("price", None)
                product.setdefault("currency", "USD")
                product.setdefault("url", "")
                product.setdefault("image_url", None)
                product.setdefault("rating", None)
                product.setdefault("review_count", None)
                product.setdefault("features", [])
                product.setdefault("availability", "unknown")

        return [p for p in products if isinstance(p, dict)]


class ProductCrawlerSync:
    """
    Synchronous wrapper around ProductCrawler for Django integration.

    Django views and ORM operations run synchronously, so this wrapper
    provides a sync interface to the async crawler.
    """

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize the sync crawler wrapper.

        Args:
            api_key: Anthropic API key for LLM extraction.
        """
        self.crawler = ProductCrawler(api_key=api_key)

    def crawl_urls(self, urls: list[str]) -> list[dict[str, Any]]:
        """
        Synchronously crawl a list of URLs.

        Creates a new event loop if needed, or uses the existing one
        with nest_asyncio for Jupyter/Django compatibility.

        Args:
            urls: List of URLs to crawl.

        Returns:
            List of crawl result dictionaries.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If there's already a running loop (e.g., in Jupyter or Django),
                # create a new thread to run the async code
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run, self.crawler.crawl_urls(urls)
                    )
                    return future.result()
            else:
                return loop.run_until_complete(self.crawler.crawl_urls(urls))
        except RuntimeError:
            # No event loop exists, create one
            return asyncio.run(self.crawler.crawl_urls(urls))
