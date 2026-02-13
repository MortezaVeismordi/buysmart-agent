from django.contrib import admin
from .models import ProductQuery, CrawlSession, Product, ComparisonResult, ProductRanking


@admin.register(ProductQuery)
class ProductQueryAdmin(admin.ModelAdmin):
    list_display = ['query_text_short', 'user', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['query_text', 'user__username', 'user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def query_text_short(self, obj):
        return obj.query_text[:60] + '...' if len(obj.query_text) > 60 else obj.query_text
    query_text_short.short_description = 'Query'


@admin.register(CrawlSession)
class CrawlSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'query', 'status', 'started_at', 'completed_at']
    list_filter = ['status', 'created_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'started_at', 'completed_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name_short', 'price', 'source_domain', 'llm_score', 'created_at']
    list_filter = ['source_domain', 'created_at']
    search_fields = ['name', 'source_domain']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def name_short(self, obj):
        return obj.name[:50] + '...' if len(obj.name) > 50 else obj.name
    name_short.short_description = 'Product Name'


@admin.register(ComparisonResult)
class ComparisonResultAdmin(admin.ModelAdmin):
    list_display = ['query', 'created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ProductRanking)
class ProductRankingAdmin(admin.ModelAdmin):
    list_display = ['rank', 'product', 'comparison', 'score_breakdown']
    list_filter = ['rank']
    ordering = ['comparison', 'rank']