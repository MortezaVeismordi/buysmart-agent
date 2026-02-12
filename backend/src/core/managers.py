from django.db import models
from django.db.models import QuerySet
from django.utils import timezone


class ActiveManager(models.Manager):
    """
    Default manager: only returns active and non-soft-deleted records.
    """
    def get_queryset(self):
        return super().get_queryset().filter(
            is_active=True,
            is_deleted=False
        )


class AllObjectsManager(models.Manager):
    """
    Manager to access ALL records, including soft-deleted and inactive ones.
    Use: Model.all_objects.all()
    """
    def get_queryset(self):
        return super().get_queryset()


class BaseQuerySet(QuerySet):
    """
    Custom QuerySet with chainable methods for common operations.
    """
    def active(self):
        """Filter only active and non-deleted records."""
        return self.filter(is_active=True, is_deleted=False)

    def deleted(self):
        """Filter only soft-deleted records."""
        return self.filter(is_deleted=True)

    def inactive(self):
        """Filter only inactive records (even if not deleted)."""
        return self.filter(is_active=False)

    def recently_updated(self, days=7):
        """Records updated in the last N days."""
        return self.filter(updated_at__gte=timezone.now() - timezone.timedelta(days=days))


class AdvancedManager(models.Manager.from_queryset(BaseQuerySet)):
    """
    Advanced manager combining custom QuerySet + default filtering.
    """
    def get_queryset(self):
        return BaseQuerySet(self.model, using=self._db).active()