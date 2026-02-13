from django.db import models
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=models.Model) 
def log_model_update(sender, instance, **kwargs):
    """
    Log model changes before save (for auditing/debugging).
    """
    if instance.pk:  
        action = "update"
    else:
        action = "create"
    logger.debug(f"{action.capitalize()} {sender.__name__} {instance.pk or 'new'}")


@receiver(post_delete, sender=models.Model)
def log_soft_or_hard_delete(sender, instance, **kwargs):
    """
    Log soft-delete or hard-delete.
    """
    if hasattr(instance, 'is_deleted') and instance.is_deleted:
        logger.info(f"Soft-deleted {sender.__name__} {instance.pk}")
    else:
        logger.warning(f"Hard-deleted {sender.__name__} {instance.pk}")


# NOTE: This signal is disabled because it conflicts with auto_now=True on updated_at
# @receiver(pre_save, sender='core.BaseModel')
# def update_timestamp_on_save(sender, instance, **kwargs):
#     """Ensure updated_at is always fresh on save (redundant but safe)."""
#     instance.updated_at = timezone.now()