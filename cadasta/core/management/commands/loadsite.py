from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site


class Command(BaseCommand):
    help = """Loads initial site object for Cadasta.org."""

    def handle(self, *args, **options):
        if not Site.objects.filter(name='Cadasta').exists():
            site = Site.objects.get(name='example.com')
            site.name = 'Cadasta'
            site.domain = 'platform.cadasta.org'
            site.save()
