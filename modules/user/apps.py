from django.apps import AppConfig


class UserConfig(AppConfig):
    name = "modules.user"

    def ready(self):
        # Import signals to ensure they are registered
        import modules.user.signals.user_signals  # noqa: F401
