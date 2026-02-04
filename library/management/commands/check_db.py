from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError
from urllib.parse import urlparse
import os


class Command(BaseCommand):
    help = 'Check database connectivity for the default database (prints host/port and attempts a connection).'

    def handle(self, *args, **options):
        database_url = os.environ.get('DATABASE_URL')
        if database_url:
            try:
                p = urlparse(database_url)
                host = p.hostname
                port = p.port
                self.stdout.write(self.style.NOTICE(f'DATABASE_URL host={host} port={port}'))
            except Exception:
                self.stdout.write(self.style.WARNING('DATABASE_URL present but could not be parsed'))
        else:
            self.stdout.write(self.style.WARNING('DATABASE_URL is not set; using settings DATABASES configuration'))

        conn = connections['default']
        try:
            conn.ensure_connection()
            self.stdout.write(self.style.SUCCESS('DB connection OK'))
            return 0
        except OperationalError as e:
            self.stderr.write(self.style.ERROR('DB connection FAILED: ' + str(e)))
            raise SystemExit(1)
