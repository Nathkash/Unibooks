from django.apps import AppConfig


class LibraryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'library'
    
    def ready(self):
        try:
            from . import signals
        except Exception:
            import sys
            print('Avertissement : impossible d’importer la bibliothèque signaux.', file=sys.stderr)
