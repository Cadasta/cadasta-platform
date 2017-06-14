from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
import json


def load():

    PERMISSIONS_DIR = settings.BASE_DIR + '/permissions/'

    Group.objects.all().delete()
    Permission.objects.all().delete()  # remove all perms here??

    # add permissions
    for ct in [
            'organizations', 'projects', 'users', 'parties', 'spatialunits',
            'resources']:
        perm_file = open(PERMISSIONS_DIR + ct + '.json')
        perms = json.loads(perm_file.read())
        content_type_label = perms['content_type'].split('.')
        permissions = perms['permissions']
        content_type = ContentType.objects.get_by_natural_key(
            app_label=content_type_label[0], model=content_type_label[1])
        for perm in permissions:
            Permission.objects.create(
                name=permissions[perm]['name'], content_type=content_type,
                codename=permissions[perm]['codename'])
        perm_file.close()

    # add groups
    groups_file = open(PERMISSIONS_DIR + 'groups.json')
    groups = json.loads(groups_file.read())
    for group in groups:
        perm_list = groups[group]['permissions']
        perms = Permission.objects.filter(
            codename__in=perm_list)
        g = Group.objects.create(name=group)
        g.permissions.set(perms)
        g.save()
