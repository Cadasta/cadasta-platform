from django.conf import settings

from tutelary import models


def run(verbose=True):
    PERMISSIONS_DIR = settings.BASE_DIR + '/permissions/'

    models.PolicyInstance.objects.all().delete()
    models.Role.objects.all().delete()
    models.Policy.objects.all().delete()
    models.PermissionSet.objects.all().delete()

    pols = {}
    for pol in ['default', 'superuser', 'org-admin', 'org-member',
                'project-manager', 'data-collector', 'project-user']:
        pols[pol] = models.Policy.objects.create(
            name=pol,
            body=open(PERMISSIONS_DIR + pol + '.json').read()
        )

    models.assign_user_policies(None, pols['default'])
