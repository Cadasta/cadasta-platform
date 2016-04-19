from django.core.management.base import BaseCommand

from ... import load


class Command(BaseCommand):
    help = """Loads country boundary data."""

    def handle(self, *args, **options):
        load.run()
