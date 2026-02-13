from django.db import models
from src.core.models import BaseModel, User


class ProductQuery(BaseModel):
    """User's natural language search query."""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='queries',
        help_text="User who created this query"
    )
    query_text = models.TextField(
        help_text="Natural language query (e.g., 'best wireless headphones under $200')"
    )
    parsed_intent = models.JSONField(
        null=True, 
        blank=True, 
        help_text="LLM-parsed intent with extracted entities"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error details if query failed"
    )
    
    class Meta:
        verbose_name = "Product Query"
        verbose_name_plural = "Product Queries"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}: {self.query_text[:50]}..."


class CrawlSession(BaseModel):
    """Track crawling sessions for a query."""
    query = models.ForeignKey(
        ProductQuery, 
        on_delete=models.CASCADE, 
        related_name='crawl_sessions'
    )
    urls_to_crawl = models.JSONField(
        default=list,
        help_text="Target URLs for crawling"
    )
    urls_crawled = models.JSONField(
        default=list, 
        help_text="Successfully crawled URLs"
    )
    urls_failed = models.JSONField(
        default=list,
        help_text="Failed URLs with error reasons"
    )
    raw_results = models.JSONField(
        null=True, 
        blank=True, 
        help_text="Raw crawl data from Crawl4AI"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('crawling', 'Crawling'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    error_message = models.TextField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Crawl Session"
        verbose_name_plural = "Crawl Sessions"

    def __str__(self):
        return f"Crawl for Query {self.query.id} - {self.status}"


class Product(BaseModel):
    """Extracted product from crawling."""
    crawl_session = models.ForeignKey(
        CrawlSession, 
        on_delete=models.CASCADE, 
        related_name='products'
    )
    name = models.CharField(max_length=500)
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Product price in USD"
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text="Currency code (ISO 4217)"
    )
    url = models.URLField(max_length=1000)
    source_domain = models.CharField(max_length=255)
    image_url = models.URLField(max_length=1000, null=True, blank=True)
    
    # Extracted features
    raw_data = models.JSONField(
        default=dict,
        help_text="All extracted data (specs, reviews, etc.)"
    )
    features = models.JSONField(
        default=list,
        help_text="List of product features"
    )
    
    # LLM enrichment fields
    llm_summary = models.TextField(
        null=True, 
        blank=True,
        help_text="AI-generated summary"
    )
    llm_score = models.FloatField(
        null=True, 
        blank=True, 
        help_text="LLM ranking score (0-100)"
    )
    llm_pros = models.JSONField(
        default=list,
        help_text="AI-identified pros"
    )
    llm_cons = models.JSONField(
        default=list,
        help_text="AI-identified cons"
    )
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-llm_score', '-created_at']

    def __str__(self):
        return f"{self.name} - ${self.price}"


class ComparisonResult(BaseModel):
    """Final ranked comparison for a query."""
    query = models.OneToOneField(
        ProductQuery, 
        on_delete=models.CASCADE, 
        related_name='result'
    )
    llm_reasoning = models.TextField(
        help_text="Chain-of-thought explanation for rankings"
    )
    llm_recommendation = models.TextField(
        null=True,
        blank=True,
        help_text="AI recommendation summary"
    )
    ranking_criteria = models.JSONField(
        default=dict,
        help_text="Criteria used for ranking (price, features, reviews, etc.)"
    )
    
    class Meta:
        verbose_name = "Comparison Result"
        verbose_name_plural = "Comparison Results"

    def __str__(self):
        return f"Comparison for: {self.query.query_text[:50]}"


class ProductRanking(models.Model):
    """Through table for ranked products in a comparison."""
    comparison = models.ForeignKey(
        ComparisonResult, 
        on_delete=models.CASCADE,
        related_name='rankings'
    )
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE
    )
    rank = models.PositiveIntegerField(
        help_text="Position in ranking (1 = best)"
    )
    reasoning = models.TextField(
        blank=True,
        help_text="Specific reasoning for this product's rank"
    )
    score_breakdown = models.JSONField(
        default=dict,
        help_text="Detailed scoring (price_score, feature_score, etc.)"
    )
    
    class Meta:
        ordering = ['rank']
        unique_together = [['comparison', 'rank']]
        verbose_name = "Product Ranking"
        verbose_name_plural = "Product Rankings"

    def __str__(self):
        return f"#{self.rank}: {self.product.name}"