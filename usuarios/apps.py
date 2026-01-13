from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "usuarios"

    def ready(self):
        """
        Se ejecuta cuando Django termina de cargar la aplicación
        """
        import usuarios.signals
