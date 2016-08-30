from django.conf import settings

from tutelary import models


def run(verbose=True, force=False, update=False):
    PERMISSIONS_DIR = settings.BASE_DIR + '/permissions/'

    if force:
        models.PermissionSet.objects.all().delete()
        models.Role.objects.all().delete()
        models.Policy.objects.all().delete()

    pols = {}
    for pol in ['default', 'superuser', 'org-admin', 'org-member',
                'project-manager', 'data-collector', 'project-user']:
        try:
            pols[pol] = models.Policy.objects.get(name=pol)
            if update:
                pols[pol].body = open(PERMISSIONS_DIR + pol + '.json').read()
                pols[pol].save()
        except:
            pols[pol] = models.Policy.objects.create(
                name=pol,
                body=open(PERMISSIONS_DIR + pol + '.json').read()
            )

    if not models.Role.objects.filter(name='superuser').exists():
        models.Role.objects.create(
            name='superuser',
            policies=[pols['default'], pols['superuser']]
        )

    models.assign_user_policies(None, pols['default'])
