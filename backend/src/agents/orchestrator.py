"""
BuySmart Orchestrator Module
Coordinates the full agent pipeline: parse → crawl → rank → save.
Integrates with Django ORM to persist results.
"""

import logging
import os
from typing import Any
from urllib.parse import urlparse

import django

# Ensure Django is set up before importing models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.config.settings")
try:
    django.setup()
except RuntimeError:
    pass  # Already configured

from django.utils import timezone

from src.domains.procurement.models import (
    ComparisonResult,
    CrawlSession,
    Product,
    ProductQuery,
    ProductRanking,
)

from .crawler import ProductCrawlerSync
from .query_parser import QueryParser
from .ranker import ProductRanker

logger = logging.getLogger(__name__)


class BuySmartOrchestrator:
    """
    Orchestrates the complete BuySmart agent pipeline.

    Coordinates query parsing, web crawling, product ranking,
    and result persistence through Django ORM.
    """

    def __init__(self, api_key: str | None = None) -> None:
        """
        Initialize the orchestrator and all sub-components.

        Args:
        Args:
            api_key: LLM API key. Falls back to OPENROUTER_API_KEY or OPENAI_API_KEY.
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.query_parser = QueryParser(api_key=self.api_key)
        self.crawler = ProductCrawlerSync(api_key=self.api_key)
        self.ranker = ProductRanker(api_key=self.api_key)

    def run_pipeline(self, query_id: str) -> dict[str, Any]:
        """
        Execute the complete BuySmart pipeline for a given query.

        Pipeline stages:
        1. Parse the natural language query
        2. Generate search URLs
        3. Crawl e-commerce sites
        4. Rank and compare products
        5. Save results to database

        Args:
            query_id: UUID of the ProductQuery to process.

        Returns:
            Dictionary with pipeline results including products,
            rankings, and comparison summary.

        Raises:
            ProductQuery.DoesNotExist: If query_id is not found.
        """
        try:
            # Fetch the query
            query = ProductQuery.objects.get(id=query_id)
            logger.info(f"Starting pipeline for query: {query.query_text[:80]}")

            # Update status to processing
            query.status = "processing"
            query.save(update_fields=["status", "updated_at"])

            # Stage 1: Parse the query
            parsed_intent = self._parse_query(query)

            # Stage 2: Generate search URLs
            search_urls = self.query_parser.generate_search_urls(parsed_intent)
            if not search_urls:
                raise ValueError("No search URLs generated from parsed intent.")

            # Stage 3: Crawl URLs
            crawl_session = self._crawl_urls(query, search_urls)

            # Stage 4: Extract and save products
            products = self._save_products(crawl_session)
            if not products:
                raise ValueError(
                    "No products were extracted from crawling. "
                    "Try refining your search query."
                )

            # Stage 5: Rank products
            ranking_result = self._rank_products(
                products, query.query_text, parsed_intent
            )

            # Stage 6: Save comparison results
            comparison = self._save_comparison(query, products, ranking_result)

            # Stage 7: Generate summary
            summary = self._generate_summary(products, ranking_result, query.query_text)

            # Update query status to completed
            query.status = "completed"
            query.save(update_fields=["status", "updated_at"])

            logger.info(f"Pipeline completed for query {query_id}")

            return {
                "query_id": str(query.id),
                "status": "completed",
                "products_found": len(products),
                "comparison_id": str(comparison.id),
                "summary": summary,
                "rankings": ranking_result.get("rankings", []),
                "best_overall": ranking_result.get("best_overall"),
                "best_value": ranking_result.get("best_value"),
            }

        except ProductQuery.DoesNotExist:
            logger.error(f"Query {query_id} not found.")
            raise
        except Exception as e:
            logger.error(f"Pipeline failed for query {query_id}: {e}")
            self._handle_pipeline_error(query_id, str(e))
            return {
                "query_id": str(query_id),
                "status": "failed",
                "error": str(e),
                "products_found": 0,
            }

    def _parse_query(self, query: ProductQuery) -> dict[str, Any]:
        """
        Parse the query text and save the parsed intent.

        Args:
            query: The ProductQuery instance.

        Returns:
            Parsed intent dictionary.
        """
        logger.info("Stage 1: Parsing query...")
        parsed_intent = self.query_parser.parse_query(query.query_text)

        # Save parsed intent to the query
        query.parsed_intent = parsed_intent
        query.save(update_fields=["parsed_intent", "updated_at"])

        logger.info(
            f"Query parsed. Product type: {parsed_intent.get('product_type', 'unknown')}"
        )
        return parsed_intent

    def _crawl_urls(
        self, query: ProductQuery, search_urls: list[str]
    ) -> CrawlSession:
        """
        Crawl the search URLs and create a CrawlSession.

        Args:
            query: The ProductQuery instance.
            search_urls: List of URLs to crawl.

        Returns:
            The created CrawlSession instance.
        """
        logger.info(f"Stage 2-3: Crawling {len(search_urls)} URLs...")

        # Create crawl session
        crawl_session = CrawlSession.objects.create(
            query=query,
            urls_to_crawl=search_urls,
            status="crawling",
            started_at=timezone.now(),
        )

        try:
            # Execute crawling
            crawl_results = self.crawler.crawl_urls(search_urls)

            # Track crawled and failed URLs
            urls_crawled = []
            urls_failed = []

            for result in crawl_results:
                if result["success"]:
                    urls_crawled.append(result["url"])
                else:
                    urls_failed.append({
                        "url": result["url"],
                        "error": result.get("error", "Unknown error"),
                    })

            # Update crawl session
            crawl_session.urls_crawled = urls_crawled
            crawl_session.urls_failed = urls_failed
            crawl_session.raw_results = crawl_results
            crawl_session.status = "completed"
            crawl_session.completed_at = timezone.now()
            crawl_session.save()

            logger.info(
                f"Crawl session complete: {len(urls_crawled)} succeeded, "
                f"{len(urls_failed)} failed."
            )
            return crawl_session

        except Exception as e:
            crawl_session.status = "failed"
            crawl_session.error_message = str(e)
            crawl_session.completed_at = timezone.now()
            crawl_session.save()
            raise

    def _save_products(self, crawl_session: CrawlSession) -> list[dict[str, Any]]:
        """
        Extract products from crawl results and save to database.

        Args:
            crawl_session: The CrawlSession with raw results.

        Returns:
            List of product data dictionaries (for ranking).
        """
        logger.info("Stage 4: Saving extracted products...")
        products_data: list[dict[str, Any]] = []

        raw_results = crawl_session.raw_results or []

        for result in raw_results:
            if not result.get("success"):
                continue

            for product_data in result.get("products", []):
                try:
                    # Determine source domain
                    product_url = product_data.get("url", result.get("url", ""))
                    domain = urlparse(product_url).netloc if product_url else result.get("domain", "unknown")

                    # Parse price safely
                    price = product_data.get("price")
                    if price is not None:
                        try:
                            price = float(str(price).replace(",", "").replace("$", ""))
                        except (ValueError, TypeError):
                            price = None

                    # Create Product in DB
                    product = Product.objects.create(
                        crawl_session=crawl_session,
                        name=product_data.get("name", "Unknown Product")[:500],
                        price=price,
                        currency=product_data.get("currency", "USD")[:3],
                        url=product_url[:1000] if product_url else "",
                        source_domain=domain[:255] if domain else "unknown",
                        image_url=product_data.get("image_url", ""),
                        raw_data=product_data,
                        features=product_data.get("features", []),
                    )

                    # Build product dict for ranking
                    products_data.append({
                        "id": str(product.id),
                        "name": product.name,
                        "price": float(product.price) if product.price else None,
                        "currency": product.currency,
                        "url": product.url,
                        "source_domain": product.source_domain,
                        "rating": product_data.get("rating"),
                        "review_count": product_data.get("review_count"),
                        "features": product.features,
                        "availability": product_data.get("availability", "unknown"),
                    })

                except Exception as e:
                    logger.warning(
                        f"Error saving product '{product_data.get('name', '?')}': {e}"
                    )
                    continue

        logger.info(f"Saved {len(products_data)} products to database.")
        return products_data

    def _rank_products(
        self,
        products: list[dict[str, Any]],
        user_query: str,
        parsed_intent: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Rank the extracted products using the ProductRanker.

        Args:
            products: List of product dictionaries.
            user_query: Original user query text.
            parsed_intent: Parsed intent dictionary.

        Returns:
            Ranking results dictionary.
        """
        logger.info(f"Stage 5: Ranking {len(products)} products...")
        ranking_result = self.ranker.rank_products(
            products, user_query, parsed_intent
        )
        return ranking_result

    def _save_comparison(
        self,
        query: ProductQuery,
        products: list[dict[str, Any]],
        ranking_result: dict[str, Any],
    ) -> ComparisonResult:
        """
        Save the comparison result and individual product rankings.

        Args:
            query: The ProductQuery instance.
            products: List of product data dictionaries.
            ranking_result: Ranking results from the ranker.

        Returns:
            The created ComparisonResult instance.
        """
        logger.info("Stage 6: Saving comparison results...")

        comparison = ComparisonResult.objects.create(
            query=query,
            llm_reasoning=ranking_result.get("overall_summary", ""),
            llm_recommendation=(
                f"Best Overall: {ranking_result.get('best_overall', 'N/A')}\n"
                f"Best Value: {ranking_result.get('best_value', 'N/A')}"
            ),
            ranking_criteria={
                "price_value": 25,
                "features_match": 25,
                "quality_rating": 20,
                "brand_reputation": 15,
                "availability": 15,
            },
        )

        # Create individual product rankings
        rankings = ranking_result.get("rankings", [])
        for rank_idx, rank_info in enumerate(rankings, start=1):
            try:
                # Find the matching product in the database
                product_index = rank_info.get("product_index", rank_idx - 1)
                if product_index < len(products):
                    product_id = products[product_index].get("id")
                    if product_id:
                        product = Product.objects.get(id=product_id)

                        # Update product with LLM enrichment data
                        product.llm_score = rank_info.get("score")
                        product.llm_pros = rank_info.get("pros", [])
                        product.llm_cons = rank_info.get("cons", [])
                        product.llm_summary = rank_info.get("reasoning", "")
                        product.save(update_fields=[
                            "llm_score", "llm_pros", "llm_cons",
                            "llm_summary", "updated_at",
                        ])

                        # Create ProductRanking entry
                        ProductRanking.objects.create(
                            comparison=comparison,
                            product=product,
                            rank=rank_idx,
                            reasoning=rank_info.get("reasoning", ""),
                            score_breakdown={
                                "overall_score": rank_info.get("score", 0),
                                "price_value_rating": rank_info.get(
                                    "price_value_rating", "unknown"
                                ),
                                "pros": rank_info.get("pros", []),
                                "cons": rank_info.get("cons", []),
                            },
                        )

            except Product.DoesNotExist:
                logger.warning(
                    f"Product not found for ranking at index {product_index}"
                )
            except Exception as e:
                logger.warning(f"Error saving ranking #{rank_idx}: {e}")

        logger.info(f"Comparison saved with {len(rankings)} rankings.")
        return comparison

    def _generate_summary(
        self,
        products: list[dict[str, Any]],
        ranking_result: dict[str, Any],
        user_query: str,
    ) -> str:
        """
        Generate a markdown comparison summary.

        Args:
            products: List of product data dictionaries.
            ranking_result: Ranking results dictionary.
            user_query: Original user query.

        Returns:
            Markdown-formatted summary string.
        """
        logger.info("Stage 7: Generating comparison summary...")
        try:
            summary = self.ranker.generate_comparison_summary(
                products, ranking_result, user_query
            )
            return summary
        except Exception as e:
            logger.warning(f"Summary generation failed, using fallback: {e}")
            return ranking_result.get(
                "overall_summary", "Comparison completed successfully."
            )

    def _handle_pipeline_error(self, query_id: str, error_message: str) -> None:
        """
        Handle pipeline errors by updating the query status.

        Args:
            query_id: UUID of the query that failed.
            error_message: Error description.
        """
        try:
            query = ProductQuery.objects.get(id=query_id)
            query.status = "failed"
            query.error_message = error_message
            query.save(update_fields=["status", "error_message", "updated_at"])
        except ProductQuery.DoesNotExist:
            logger.error(f"Cannot update error status: Query {query_id} not found.")
        except Exception as e:
            logger.error(f"Error updating pipeline failure status: {e}")
