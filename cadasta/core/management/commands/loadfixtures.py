from django.core.management.base import BaseCommand

from core.fixtures import FixturesData


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
        data = FixturesData()

        if options['delete']:
            data.delete_test_users()
            data.delete_test_organizations()
            data.delete_test_projects()

        else:
            data.add_test_organizations()
            data.add_test_users_and_roles()
            data.add_test_projects()
            self.stdout.write(self.style.SUCCESS("All test data loaded."))
