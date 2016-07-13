from django.core.management.base import BaseCommand

from ...models import load_tenure_relationship_types


class Command(BaseCommand):
    help = "Load tenure relationship types."

    def handle(self, *args, **options):
        load_tenure_relationship_types()
