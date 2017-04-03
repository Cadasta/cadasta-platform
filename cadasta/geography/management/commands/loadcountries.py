from django.core.management.base import BaseCommand

from ... import load
from ...models import WorldBorder


class Command(BaseCommand):
    help = """Loads country boundary data."""

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            default=False,
            help=('Erase all WorldBorder instances before creating '
                  'new instances')
        )

    def handle(self, *args, **options):
        if options['force'] or not WorldBorder.objects.exists():
            load.run()
            msg = "Loaded boundaries"
            return self.stdout.write(self.style.SUCCESS(msg))
        msg = (
            "Boundaries not loaded, boundaries already existant and "
            "command not forced."
        )
        return self.stdout.write(self.style.WARNING(msg))
