from django.contrib import admin
from .models import (
    SearchQuery,
    CrawlSource,
    CrawlResult,
    ProductMatch,
    SupplierProfile,
)

@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ("query_text", "status", "user", "created_at", "total_results")
    list_filter = ("status", "created_at")
    search_fields = ("query_text", "parsed_intent")
    readonly_fields = ("created_at", "updated_at", "parsed_intent")

@admin.register(CrawlSource)
class CrawlSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "base_url", "is_active", "priority")
    list_filter = ("is_active", "robots_txt_compliant")
    search_fields = ("name", "base_url")

@admin.register(CrawlResult)
class CrawlResultAdmin(admin.ModelAdmin):
    list_display = ("source", "crawled_url", "status", "search_query", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("crawled_url", "error_detail")
    readonly_fields = ("created_at", "updated_at", "extracted_data")

@admin.register(ProductMatch)
class ProductMatchAdmin(admin.ModelAdmin):
    list_display = ("name", "supplier_name", "price", "currency", "ranking_score", "search_query")
    list_filter = ("currency", "created_at")
    search_fields = ("name", "supplier_name", "ranking_rationale")
    readonly_fields = ("created_at", "updated_at", "metadata", "ranking_rationale")

@admin.register(SupplierProfile)
class SupplierProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "website", "country", "reliability_score")
    list_filter = ("country",)
    search_fields = ("name", "website")