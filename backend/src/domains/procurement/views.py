"""
Procurement Domain Views
DRF ViewSets for product queries, products, and comparisons.
"""

import logging
from typing import Any

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from src.agents.orchestrator import BuySmartOrchestrator

from .models import (
    ComparisonResult,
    CrawlSession,
    Product,
    ProductQuery,
)
from .serializers import (
    ComparisonResultSerializer,
    CrawlSessionSerializer,
    ProductQuerySerializer,
    ProductSerializer,
    QueryCreateSerializer,
)

logger = logging.getLogger(__name__)


class ProductQueryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing product search queries.

    Provides standard CRUD operations plus custom actions
    for processing queries and retrieving results.
    """

    serializer_class = ProductQuerySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return queries belonging to the authenticated user."""
        return ProductQuery.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Use QueryCreateSerializer for create actions."""
        if self.action == "create":
            return QueryCreateSerializer
        return ProductQuerySerializer

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """
        Create a new product query.

        Accepts query_text and creates a ProductQuery for the current user.
        """
        serializer = QueryCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = ProductQuery.objects.create(
            user=request.user,
            query_text=serializer.validated_data["query_text"],
            status="pending",
        )

        response_serializer = ProductQuerySerializer(query)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="process")
    def process(self, request: Request, pk: str = None) -> Response:
        """
        Trigger the BuySmart pipeline for a query.

        Runs the full pipeline: parse → crawl → rank → save.
        Returns pipeline results including products found and rankings.
        """
        try:
            query = self.get_object()

            if query.status == "processing":
                return Response(
                    {"error": "This query is already being processed."},
                    status=status.HTTP_409_CONFLICT,
                )

            if query.status == "completed":
                return Response(
                    {
                        "message": "This query has already been processed.",
                        "query_id": str(query.id),
                        "status": "completed",
                    },
                    status=status.HTTP_200_OK,
                )

            # Run the orchestrator pipeline
            orchestrator = BuySmartOrchestrator()
            result = orchestrator.run_pipeline(str(query.id))

            return Response(result, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Error processing query {pk}: {e}")
            return Response(
                {"error": f"Pipeline execution failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"], url_path="result")
    def result(self, request: Request, pk: str = None) -> Response:
        """
        Get the comparison result for a processed query.

        Returns the full comparison result with rankings
        and product details.
        """
        query = self.get_object()

        try:
            comparison = ComparisonResult.objects.get(query=query)
            serializer = ComparisonResultSerializer(comparison)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ComparisonResult.DoesNotExist:
            if query.status == "processing":
                return Response(
                    {"message": "Query is still being processed."},
                    status=status.HTTP_202_ACCEPTED,
                )
            elif query.status == "failed":
                return Response(
                    {
                        "error": "Query processing failed.",
                        "error_message": query.error_message,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                    {"message": "No results yet. Please process the query first."},
                    status=status.HTTP_404_NOT_FOUND,
                )

    @action(detail=True, methods=["get"], url_path="crawl-sessions")
    def crawl_sessions(self, request: Request, pk: str = None) -> Response:
        """
        Get crawl session history for a query.

        Returns all crawl sessions with URLs crawled/failed and product counts.
        """
        query = self.get_object()
        sessions = CrawlSession.objects.filter(query=query)
        serializer = CrawlSessionSerializer(sessions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for products.

    Lists products ordered by LLM score (highest first).
    """

    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return products from the current user's queries."""
        return Product.objects.filter(
            crawl_session__query__user=self.request.user
        ).order_by("-llm_score", "-created_at")


class ComparisonResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only ViewSet for comparison results.

    Lists comparison results with nested rankings and products.
    """

    serializer_class = ComparisonResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return comparison results for the current user's queries."""
        return ComparisonResult.objects.filter(
            query__user=self.request.user
        ).select_related("query").prefetch_related(
            "rankings__product"
        )
