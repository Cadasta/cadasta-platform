from django.core.management.base import BaseCommand

from core.management.commands import loadsite
from accounts.management.commands import loadpolicies
from geography.management.commands import loadcountries
from party.management.commands import loadtenurereltypes
from jsonattrs.management.commands import loadattrtypes


class Command(BaseCommand):
    help = """Load in all site, country, policy and test data.
            Only run first time a database is set up."""

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Force object deletion and recreation'
        )

    def handle(self, *args, **options):
        # All of the following are idempotent unless "force" is used.
        if options['force']:
            print('FORCING STATIC DATA RELOAD!!!\n')

        print('LOADING SITE\n')
        loadsite.Command().handle(force=options['force'])
        print('LOADING COUNTRIES\n')
        loadcountries.Command().handle(force=options['force'])
        print('LOADING POLICIES\n')
        loadpolicies.Command().handle(force=options['force'])
        print('LOADING ATTRIBUTE TYPES\n')
        loadattrtypes.Command().handle(force=options['force'])
        print('LOADING TENURE RELATIONSHIP TYPES\n')
        loadtenurereltypes.Command().handle(force=options['force'])
