from django.core.management.base import BaseCommand

from accounts import load


class Command(BaseCommand):
    help = """Loads policy data."""

    def handle(self, *args, **options):
        load.run(force=options['force'], update=options['update'])
