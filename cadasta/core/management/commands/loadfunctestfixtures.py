import cadasta.test
import inspect
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = """Loads in functional test data for users, roles, organizations,
              projects, records, and resources."""

    def handle(self, *args, **options):
        print('LOADING FUNCTIONAL TEST DATA\n')
        dir = os.path.join(
            os.path.dirname(inspect.getfile(cadasta.test)), 'fixtures')
        files = [os.path.join(dir, f) for f in os.listdir(dir) if '.json' in f]
        call_command('loaddata', *files)
        self.stdout.write(self.style.SUCCESS("Functional test data loaded."))
