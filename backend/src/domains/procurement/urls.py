"""
Procurement Domain URL Configuration
Routes for product queries, products, and comparisons.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ComparisonResultViewSet,
    ProductQueryViewSet,
    ProductViewSet,
)

router = DefaultRouter()
router.register(r"queries", ProductQueryViewSet, basename="productquery")
router.register(r"products", ProductViewSet, basename="product")
router.register(r"comparisons", ComparisonResultViewSet, basename="comparisonresult")

app_name = "procurement"

urlpatterns = [
    path("", include(router.urls)),
]
