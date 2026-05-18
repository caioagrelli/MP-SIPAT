from django.apps import AppConfig


class DimrcbpConfig(AppConfig):
    name = 'dimrcbp'

    def ready(self):
        import dimrcbp.signals  # noqa: F401
