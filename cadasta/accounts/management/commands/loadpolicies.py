from django.core.management.base import BaseCommand

from accounts import load


class Command(BaseCommand):
    help = """Loads policy data."""

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False)

        parser.add_argument(
            '--update',
            action='store_true',
            dest='update',
            default=False)

    def handle(self, *args, **options):
        load.run(force=options['force'], update=options['update'])
