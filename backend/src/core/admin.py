from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import User


class BaseModelAdmin(admin.ModelAdmin):
    """
    Reusable base admin class for models inheriting from core.BaseModel.
    Includes support for soft-delete actions and standard metadata display.
    """
    list_display = ("id", "is_active", "created_at", "updated_at", "is_deleted")
    list_filter = ("is_active", "is_deleted", "created_at", "updated_at")
    search_fields = ("id",)
    readonly_fields = ("id", "created_at", "updated_at", "deleted_at")
    ordering = ("-created_at",)
    
    actions = ["soft_delete_selected", "restore_selected"]

    @admin.action(description=_("Soft delete selected items"))
    def soft_delete_selected(self, request, queryset):
        """Mark selected items as deleted instead of removing them."""
        updated_count = queryset.update(
            is_deleted=True, 
            deleted_at=timezone.now(), 
            is_active=False
        )
        self.message_user(request, _(f"{updated_count} items have been soft deleted."))

    @admin.action(description=_("Restore selected items"))
    def restore_selected(self, request, queryset):
        """Restore soft-deleted items."""
        updated_count = queryset.update(
            is_deleted=False, 
            deleted_at=None, 
            is_active=True
        )
        self.message_user(request, _(f"{updated_count} items have been restored."))


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Advanced User Admin with UUID support and extended filtering.
    """
    list_display = (
        "username", 
        "email", 
        "first_name", 
        "last_name", 
        "is_staff", 
        "is_active", 
        "date_joined"
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "groups", "date_joined")
    search_fields = ("username", "first_name", "last_name", "email", "id")
    ordering = ("-date_joined",)
    readonly_fields = ("id", "date_joined", "last_login")

    # Layout for the "Change User" page
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (_("Metadata"), {"fields": ("id",)}),
    )

    # Layout for the "Add User" page
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username", 
                    "email", 
                    "password", 
                    "first_name", 
                    "last_name",
                    "is_staff",
                    "is_superuser",
                    "is_active"
                ),
            },
        ),
    )
