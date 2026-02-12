from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from src.core.models import BaseModel, User
from decimal import Decimal


class SearchQuery(BaseModel):
    """
    User's natural language procurement/search request.
    Core entry point for the agent workflow.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="search_queries",
        verbose_name=_("User"),
        help_text=_("Authenticated user who submitted the query")
    )
    query_text = models.TextField(
        verbose_name=_("Query Text"),
        help_text=_("Raw natural language input from user")
    )
    parsed_intent = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Parsed Intent"),
        help_text=_("LLM-extracted structured intent (criteria, budget, etc.)")
    )
    status = models.CharField(
        max_length=32,
        default="pending",
        choices=[
            ("pending", _("Pending")),
            ("processing", _("Processing")),
            ("completed", _("Completed")),
            ("failed", _("Failed")),
            ("cancelled", _("Cancelled")),
        ],
        verbose_name=_("Status"),
        db_index=True
    )
    error_message = models.TextField(
        blank=True,
        verbose_name=_("Error Message")
    )
    total_results = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total Results Found")
    )

    class Meta:
        verbose_name = _("Search Query")
        verbose_name_plural = _("Search Queries")
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["user", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Query '{self.query_text[:60]}...' ({self.status})"


class CrawlSource(BaseModel):
    """
    Reusable web source / supplier domain configuration.
    Can be used across multiple queries.
    """
    name = models.CharField(
        max_length=255,
        verbose_name=_("Source Name"),
        help_text=_("Display name of the supplier/website")
    )
    base_url = models.URLField(
        verbose_name=_("Base URL"),
        unique=True,
        help_text=_("Root domain or main page")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active")
    )
    priority = models.PositiveSmallIntegerField(
        default=10,
        verbose_name=_("Priority"),
        help_text=_("Lower number = higher priority in crawling")
    )
    crawl_frequency = models.DurationField(
        null=True,
        blank=True,
        verbose_name=_("Crawl Frequency"),
        help_text=_("Recommended crawl interval")
    )
    robots_txt_compliant = models.BooleanField(
        default=True,
        verbose_name=_("Robots.txt Compliant")
    )

    class Meta:
        verbose_name = _("Crawl Source")
        verbose_name_plural = _("Crawl Sources")
        ordering = ["priority", "name"]
        indexes = [models.Index(fields=["is_active", "priority"])]

    def __str__(self) -> str:
        return f"{self.name} ({self.base_url})"


class CrawlResult(BaseModel):
    """
    Individual crawl execution result linked to a search query.
    """
    search_query = models.ForeignKey(
        SearchQuery,
        on_delete=models.CASCADE,
        related_name="crawl_results",
        verbose_name=_("Search Query")
    )
    source = models.ForeignKey(
        CrawlSource,
        on_delete=models.PROTECT,
        related_name="crawl_results",
        verbose_name=_("Crawl Source")
    )
    crawled_url = models.URLField(
        verbose_name=_("Crawled URL"),
        help_text=_("Exact page that was crawled")
    )
    status = models.CharField(
        max_length=32,
        choices=[
            ("success", _("Success")),
            ("timeout", _("Timeout")),
            ("blocked", _("Blocked")),
            ("parse_error", _("Parse Error")),
            ("rate_limited", _("Rate Limited")),
            ("other_error", _("Other Error")),
        ],
        default="success",
        verbose_name=_("Status")
    )
    response_time_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Response Time (ms)")
    )
    raw_content_length = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Raw Content Length")
    )
    extracted_data = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Extracted Structured Data"),
        help_text=_("LLM-parsed product/price/supplier info")
    )
    error_detail = models.TextField(
        blank=True,
        verbose_name=_("Error Detail")
    )

    class Meta:
        verbose_name = _("Crawl Result")
        verbose_name_plural = _("Crawl Results")
        indexes = [
            models.Index(fields=["search_query", "status"]),
            models.Index(fields=["source", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.source.name} crawl for {self.search_query_id} ({self.status})"


class ProductMatch(BaseModel):
    """
    Ranked product/supplier match extracted from crawl results.
    Final output of agent reasoning & ranking.
    """
    search_query = models.ForeignKey(
        SearchQuery,
        on_delete=models.CASCADE,
        related_name="product_matches",
        verbose_name=_("Search Query")
    )
    crawl_result = models.ForeignKey(
        CrawlResult,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="product_matches",
        verbose_name=_("Source Crawl Result")
    )
    name = models.CharField(
        max_length=512,
        verbose_name=_("Product Name")
    )
    price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name=_("Price")
    )
    currency = models.CharField(
        max_length=10,
        default="USD",
        verbose_name=_("Currency")
    )
    supplier_name = models.CharField(
        max_length=255,
        verbose_name=_("Supplier / Store Name")
    )
    product_url = models.URLField(
        verbose_name=_("Product URL")
    )
    ranking_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Ranking Score"),
        help_text=_("Final normalized score from agent ranking")
    )
    ranking_rationale = models.TextField(
        blank=True,
        verbose_name=_("Ranking Rationale"),
        help_text=_("LLM-generated explanation of ranking position")
    )
    confidence = models.FloatField(
        default=0.0,
        verbose_name=_("Confidence Score"),
        help_text=_("LLM confidence in data accuracy")
    )
    metadata = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_("Additional Metadata"),
        help_text=_("Any extra extracted fields (specs, images, reviews)")
    )

    class Meta:
        verbose_name = _("Product Match")
        verbose_name_plural = _("Product Matches")
        indexes = [
            models.Index(fields=["search_query", "ranking_score"]),
            models.Index(fields=["supplier_name"]),
        ]
        ordering = ["-ranking_score", "-created_at"]

    def __str__(self) -> str:
        return f"{self.name} @ {self.price or 'N/A'} ({self.ranking_score or 'N/A'})"


class SupplierProfile(BaseModel):
    """
    Reusable supplier/vendor profile (can be linked to multiple matches).
    """
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name=_("Supplier Name")
    )
    website = models.URLField(
        blank=True,
        verbose_name=_("Website")
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Country")
    )
    reliability_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name=_("Reliability Score"),
        help_text=_("Historical/calculated supplier reliability")
    )
    average_delivery_days = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Avg Delivery Days")
    )

    class Meta:
        verbose_name = _("Supplier Profile")
        verbose_name_plural = _("Supplier Profiles")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name