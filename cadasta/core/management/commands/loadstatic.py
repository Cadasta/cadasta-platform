from django.core.management.base import BaseCommand

from core.management.commands import loadsite
from accounts.management.commands import loadpolicies
from geography.management.commands import loadcountries
from party.management.commands import loadtenurereltypes
from jsonattrs.management.commands import loadattrtypes


class Command(BaseCommand):
    help = """Load in all site, country, policy and test data."""

    def handle(self, *args, **options):
        # All of the following are idempotent.
        print('LOADING SITE\n')
        loadsite.Command().handle()
        print('LOADING COUNTRIES\n')
        loadcountries.Command().handle()
        print('LOADING POLICIES\n')
        loadpolicies.Command().handle()
        print('LOADING ATTRIBUTE TYPES\n')
        loadattrtypes.Command().handle()
        print('LOADING TENURE RELATIONSHIP TYPES\n')
        loadtenurereltypes.Command().handle()
