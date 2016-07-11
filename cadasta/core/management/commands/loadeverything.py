from django.core.management.base import BaseCommand

from core.management.commands import loadfixtures, loadsite
from accounts.management.commands import loadpolicies
from geography.management.commands import loadcountries


class Command(BaseCommand):
    help = """Load in all site, country, policy and test data."""

    def handle(self, *args, **options):
        loadsite.Command().handle()
        loadcountries.Command().handle()
        loadpolicies.Command().handle()
        loadfixtures.Command().handle(delete=False)
