import json
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.contrib.auth.models import Permission, Group


PERMISSIONED_APPS = ('organization', )
PERMISSIONS_DIR = settings.BASE_DIR + '/permissions/'


def create_permissions(force=False):
    for app in PERMISSIONED_APPS:
        perm_file = open(PERMISSIONS_DIR + app + '.json')
        models = json.loads(perm_file.read())

        for m in models:
            app_label, model = m['content_type'].split('.')
            content_type = ContentType.objects.get_by_natural_key(
                app_label=app_label, model=model)

            for perm in m['permissions']:
                create = False
                try:
                    perm_obj = Permission.objects.get(
                        name=perm['name'],
                        content_type=content_type,
                        codename=perm['codename'])

                    if force:
                        perm_obj.delete()
                        create = True
                except Permission.DoesNotExist:
                    create = True

                if create:
                    Permission.objects.create(
                        name=perm['name'],
                        content_type=content_type,
                        codename=perm['codename'])
        perm_file.close()


def assign_permissions():
    groups_file = open(PERMISSIONS_DIR + 'group-policies.json')
    groups = json.loads(groups_file.read())

    for g in groups:
        perms = Permission.objects.filter(codename__in=g['permissions'])
        g = Group.objects.get(name=g['group'])
        g.permissions.set(perms)
        g.save()
    groups_file.close()


class Command(BaseCommand):
    help = """Loads permission data."""

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False)

    def handle(self, *args, **options):
        create_permissions(force=options['force'])
        assign_permissions()
