from django.db import models
from uuid import uuid4
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

class SoftDeleteManager(models.Manager):
    """Manager that excludes soft-deleted records by default."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class BaseModel(models.Model):
    """
    Abstract base model with UUID PK, timestamps, soft-delete, and active flag.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
        verbose_name="ID"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        editable=False,
        verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
        help_text="Whether the record is active and visible"
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name="Is Deleted",
        help_text="Soft deletion flag"
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        editable=False,
        verbose_name="Deleted At"
    )

    objects = AdvancedManager()      # default: non-deleted only
    all_objects = AllObjectsManager()      # access all records including deleted(NEW VERSION)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
        get_latest_by = "created_at"
        indexes = [
            models.Index(fields=["is_active", "is_deleted"]),
        ]

    def __str__(self) -> str:
        return f"{self.__class__.__name__} ({self.id})"

    def delete(self, *args, **kwargs):
        """Soft delete the instance."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.is_active = False  # usually delete → deactivate
        self.save(update_fields=["is_deleted", "deleted_at", "is_active"])

    def hard_delete(self, *args, **kwargs):
        """Perform permanent deletion."""
        super().delete(*args, **kwargs)


class TimestampedModel(BaseModel):
    """
    Lightweight abstract model without UUID – use when integer PK is preferred.
    """
    class Meta:
        abstract = True
        ordering = ["-created_at"]


class User(AbstractUser):
    """
    Custom user model with UUID primary key.
    Extends default AbstractUser for future custom fields.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
        verbose_name=_("ID")
    )

    # Optional future fields (uncomment when needed)
    # phone_number = models.CharField(max_length=15, blank=True, null=True)
    # is_verified = models.BooleanField(default=False, verbose_name=_("Is Verified"))

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]

    def __str__(self) -> str:
        return self.get_full_name() or self.username or self.email