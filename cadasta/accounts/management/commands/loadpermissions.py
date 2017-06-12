from django.core.management.base import BaseCommand
from accounts import permissions


class Command(BaseCommand):
    help = """Load platform groups and permissions."""

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False)

    def handle(self, *args, **options):
        permissions.load()
