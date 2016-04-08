from django.core.management.base import BaseCommand

from core.tests.factories import FixturesData


class Command(BaseCommand):
    help = """Loads in test data for
            organizations, users, roles,
            and projects."""

    def add_arguments(self, parser):
        parser.add_argument('--delete',
                            action='store_true',
                            dest='delete',
                            default=False,
                            help="""Delete all of
                            the test data."""
                            )

    def handle(self, *args, **options):
        data = FixturesData

        if options['delete']:
            data.delete_test_users(self)
            data.delete_test_organizations(self)
            data.delete_test_projects(self)

        else:
            data.add_test_organizations(self)
            data.add_test_users_and_roles(self)
            data.add_test_projects(self)
            self.stdout.write(self.style.SUCCESS("All test data loaded."))
