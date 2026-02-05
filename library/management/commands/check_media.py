from django.core.management.base import BaseCommand
from django.apps import apps
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Check media files referenced by FileField/ImageField exist on disk.\nOutputs a summary and a list of missing files (path and model/field).' 

    def add_arguments(self, parser):
        parser.add_argument('--fixplaceholders', action='store_true', help='Create empty placeholder files for missing entries (useful if you want 404 -> 200).')

    def handle(self, *args, **options):
        missing = []
        total = 0
        for model in apps.get_models():
            for field in model._meta.get_fields():
                # only inspect FileField/ImageField instances
                if getattr(field, 'is_relation', False):
                    continue
                field_class_name = field.__class__.__name__
                if field_class_name in ('FileField', 'ImageField'):
                    # iterate all instances of this model
                    qs = model.objects.all()
                    for obj in qs:
                        total += 1
                        try:
                            filefield = getattr(obj, field.name)
                        except Exception:
                            continue
                        if not filefield:
                            continue
                        file_path = os.path.join(settings.MEDIA_ROOT, filefield.name)
                        if not os.path.exists(file_path):
                            missing.append((model._meta.label, obj.pk, field.name, filefield.name, file_path))
        self.stdout.write(self.style.MIGRATE_HEADING(f"Media check summary"))
        self.stdout.write(f"Total referenced file fields scanned (approx): {total}")
        self.stdout.write(f"Missing files: {len(missing)}")
        if missing:
            self.stdout.write('List of missing files:')
            for mdl, pk, field_name, stored_name, path in missing:
                self.stdout.write(f" - {mdl}[pk={pk}].{field_name} -> {stored_name} (expected on disk: {path})")
            if options['fixplaceholders']:
                self.stdout.write('Creating placeholder files for missing entries...')
                for mdl, pk, field_name, stored_name, path in missing:
                    d = os.path.dirname(path)
                    os.makedirs(d, exist_ok=True)
                    with open(path, 'wb') as f:
                        f.write(b'')
                self.stdout.write(self.style.SUCCESS('Placeholders created.'))
        else:
            self.stdout.write(self.style.SUCCESS('All referenced media files were present on disk.'))
