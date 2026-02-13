import asyncio
import logging
from typing import Optional
from asgiref.sync import sync_to_async
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BrowserConfig
from src.core.exceptions import ExternalServiceError
from ..models import CrawlResult, SearchQuery

logger = logging.getLogger(__name__)


class CrawlService:
    """
    Service for performing web crawls and persisting results to CrawlResult model.
    Supports async execution and configurable crawling behavior.
    """

    @staticmethod
    async def crawl_url(
        url: str,
        search_query: SearchQuery,
        config: Optional[CrawlerRunConfig] = None,
        max_retries: int = 2,
        timeout: int = 45,
    ) -> CrawlResult:
        """
        Asynchronously crawl a single URL and store the result.
        Retries on transient errors.
        """
        crawler_config = config or CrawlerRunConfig(
            timeout=timeout,
            # js_code="window.scrollTo(0, document.body.scrollHeight);",
        )

        browser_config = BrowserConfig(headless=True, verbose=False)

        attempt = 0
        last_error = None

        while attempt < max_retries:
            attempt += 1
            try:
                async with AsyncWebCrawler(
                    verbose=True,
                    browser_config=browser_config,
                ) as crawler:
                    result = await crawler.arun(
                        url=url,
                        config=crawler_config,
                    )

                    if not result.success:
                        raise ExternalServiceError(
                            detail=f"Crawl failed: {result.error_message or 'Unknown error'}"
                        )

                    crawl_result = await sync_to_async(CrawlResult.objects.create)(
                        search_query=search_query,
                        source_url=url,
                        crawled_url=result.url or url,
                        raw_content=result.markdown or result.cleaned_html or "",
                        extracted_data=result.extracted_content,
                        status="success",
                        response_time_ms=int(result.time_taken or 0),
                        raw_content_length=len(result.markdown or ""),
                    )

                    logger.info(
                        f"Crawl success: {url} for query {search_query.id} "
                        f"(time: {result.time_taken:.2f}s)"
                    )
                    return crawl_result

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Crawl attempt {attempt}/{max_retries} failed for {url}: {str(e)}"
                )
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)  # exponential backoff
                continue

        error_detail = str(last_error) if last_error else "Unknown error after retries"
        await sync_to_async(CrawlResult.objects.create)(
            search_query=search_query,
            source_url=url,
            status="error",
            error_detail=error_detail,
        )

        logger.error(f"Crawl failed after {max_retries} attempts: {url} - {error_detail}")
        raise ExternalServiceError(detail=error_detail)

    @staticmethod
    def crawl_url_sync(
        url: str,
        search_query: SearchQuery,
        config: Optional[CrawlerRunConfig] = None,
    ) -> CrawlResult:
        """
        Synchronous wrapper for use in views, Celery tasks, or management commands.
        """
        try:
            return asyncio.run(
                CrawlService.crawl_url(url, search_query, config)
            )
        except RuntimeError as e:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(
                CrawlService.crawl_url(url, search_query, config)
            )