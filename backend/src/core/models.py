from django.db import models
from uuid import uuid4


class BaseModel(models.Model):
    """
    Abstract base model with UUID primary key and timestamps.
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

    class Meta:
        abstract = True
        ordering = ["-created_at"]
        get_latest_by = "created_at"

    def __str__(self) -> str:
        return f"{self.__class__.__name__} ({self.id})"


class TimestampedModel(BaseModel):
    """
    Lightweight version without UUID – use when integer PK is preferred.
    """
    class Meta:
        abstract = True
        ordering = ["-created_at"]