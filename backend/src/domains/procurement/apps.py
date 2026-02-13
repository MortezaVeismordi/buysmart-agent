from django.apps import AppConfig


class ProcurementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'src.domains.procurement'
    verbose_name = 'Procurement Domain'
    
    def ready(self):
        """Import signals when app is ready."""
        # Import signals here if you add them later
        # import src.domains.procurement.signals
        pass