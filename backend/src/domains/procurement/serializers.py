"""
Procurement Domain Serializers
DRF serializers for product queries, products, rankings, and comparisons.
"""

from rest_framework import serializers

from .models import (
    ComparisonResult,
    CrawlSession,
    Product,
    ProductQuery,
    ProductRanking,
)


class QueryCreateSerializer(serializers.Serializer):
    """Serializer for creating a new product query (POST requests)."""

    query_text = serializers.CharField(
        max_length=2000,
        help_text="Natural language product search query.",
    )

    def validate_query_text(self, value: str) -> str:
        """Ensure query text is not empty or whitespace-only."""
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("Query text cannot be empty.")
        if len(cleaned) < 5:
            raise serializers.ValidationError(
                "Query text must be at least 5 characters long."
            )
        return cleaned


class ProductQuerySerializer(serializers.ModelSerializer):
    """Serializer for ProductQuery model (read operations)."""

    class Meta:
        model = ProductQuery
        fields = [
            "id",
            "query_text",
            "parsed_intent",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "parsed_intent",
            "status",
            "error_message",
            "created_at",
            "updated_at",
        ]


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for Product model with all fields including LLM data."""

    class Meta:
        model = Product
        fields = [
            "id",
            "crawl_session",
            "name",
            "price",
            "currency",
            "url",
            "source_domain",
            "image_url",
            "raw_data",
            "features",
            "llm_summary",
            "llm_score",
            "llm_pros",
            "llm_cons",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CrawlSessionSerializer(serializers.ModelSerializer):
    """Serializer for CrawlSession model."""

    products_count = serializers.SerializerMethodField()

    class Meta:
        model = CrawlSession
        fields = [
            "id",
            "query",
            "urls_to_crawl",
            "urls_crawled",
            "urls_failed",
            "status",
            "error_message",
            "started_at",
            "completed_at",
            "products_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_products_count(self, obj: CrawlSession) -> int:
        """Return the number of products extracted in this crawl session."""
        return obj.products.count()


class ProductRankingSerializer(serializers.ModelSerializer):
    """Serializer for ProductRanking with nested product data."""

    product = ProductSerializer(read_only=True)

    class Meta:
        model = ProductRanking
        fields = [
            "id",
            "rank",
            "product",
            "reasoning",
            "score_breakdown",
        ]
        read_only_fields = fields


class ComparisonResultSerializer(serializers.ModelSerializer):
    """Serializer for ComparisonResult with nested rankings and query."""

    rankings = ProductRankingSerializer(many=True, read_only=True)
    query = ProductQuerySerializer(read_only=True)

    class Meta:
        model = ComparisonResult
        fields = [
            "id",
            "query",
            "llm_reasoning",
            "llm_recommendation",
            "ranking_criteria",
            "rankings",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
