from django.apps import AppConfig

class LogisticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.logistics'

    def ready(self):
        # Import signals to ensure they are registered
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Avoid breaking app startup if signals fail
            pass
