from django.apps import AppConfig


class SecurityChecksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'security_checks'

    def ready(self):
        import security_checks.signals # noqa
