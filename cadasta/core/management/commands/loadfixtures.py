from django.core.management.base import BaseCommand

from core.factories import FixturesData


class Command(BaseCommand):
    help = """Loads in test data for
            organizations, users, roles,
            and projects. Using loadfixtures
            without any additional arguments
            will load in all test data."""

    def add_arguments(self, parser):
        parser.add_argument('--users',
                            action='store_true',
                            dest='users',
                            default=False,
                            help="""Load in just
                            the test users, and
                            nothing else."""
                            )

        parser.add_argument('--organizations',
                            action='store_true',
                            dest='organizations',
                            default=False,
                            help="""Load in just
                            the test
                            organizations,
                            and nothing else."""
                            )

        parser.add_argument('--projects',
                            action='store_true',
                            dest='projects',
                            default=False,
                            help="""Load in just
                            the test projects,
                            and nothing else."""
                            )

        parser.add_argument('--delete-users',
                            action='store_true',
                            dest='delete-users',
                            default=False,
                            help="""Delete test
                            users, but leave
                            everything else."""
                            )

        parser.add_argument('--delete-organizations',
                            action='store_true',
                            dest='delete-organizations',
                            default=False,
                            help="""Delete test
                            organizations, but
                            leave the users."""
                            )

        parser.add_argument('--delete-projects',
                            action='store_true',
                            dest='delete-projects',
                            default=False,
                            help="""Delete test
                            projects, but leave
                            everything else."""
                            )

        parser.add_argument('--delete',
                            action='store_true',
                            dest='delete',
                            default=False,
                            help="""Delete all of
                            the test data."""
                            )

    def handle(self, *args, **options):
        data = FixturesData
        if options['users']:
            data.add_test_users(self)

        elif options['organizations']:
            data.add_test_organizations(self)

        elif options['projects']:
            data.add_test_projects(self)

        elif options['delete-organizations']:
            data.delete_test_organizations(self)

        elif options['delete-users']:
            data.delete_test_users(self)

        elif options['delete-projects']:
            data.delete_test_projects(self)

        elif options['delete']:
            data.delete_test_users(self)
            data.delete_test_organizations(self)
            data.delete_test_projects(self)

        else:
            data.add_test_users_and_roles(self)
            data.add_test_organizations(self)
            data.add_test_projects(self)
            self.stdout.write(self.style.SUCCESS("All test data loaded."))
