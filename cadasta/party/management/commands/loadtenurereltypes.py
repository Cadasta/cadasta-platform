from django.core.management.base import BaseCommand

from ...models import load_tenure_relationship_types


class Command(BaseCommand):
    help = "Load tenure relationship types."

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            default=False,
            help=('Erase all TenureRelationshipType instances before '
                  'creating new instances')
        )

    def handle(self, *args, **options):
        added = load_tenure_relationship_types(force=options['force'])
        if not added:
            msg = "No tenure relationship types added"
            return self.stdout.write(self.style.WARNING(msg))
        msg = "Added the following types:\n{}".format(
            "\n".join(["{}: {}".format(tr.id, tr.label) for tr in added])
        )
        return self.stdout.write(self.style.SUCCESS(msg))
