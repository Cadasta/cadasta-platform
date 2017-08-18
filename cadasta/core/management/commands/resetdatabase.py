from django.core.management.base import BaseCommand
from django_extensions.management.commands import reset_db
from subprocess import call


class Command(BaseCommand):
    help = """Recreates a database using the current local migration files.
              It runs loadstatic at the end."""

    def handle(self, *args, **options):

        print('RESETTING DATABASE\n')
        reset_db.Command().handle(router='default')

        print('MAKING MIGRATION FILES\n')
        call(args=['./manage.py', 'makemigrations'])

        print('LOADING MIGRATION FILES\n')
        call(args=['./manage.py', 'migrate'])

        print('LOADING STATIC:\n')
        call(args=['./manage.py', 'loadstatic'])

        self.stdout.write(self.style.SUCCESS("Database reset successfully."))
