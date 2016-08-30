from django.core.management.base import BaseCommand

from ... import load
from ...models import WorldBorder


class Command(BaseCommand):
    help = """Loads country boundary data."""

    def handle(self, *args, **options):
        if options['force'] or not WorldBorder.objects.exists():
            load.run()
