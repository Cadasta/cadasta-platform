from django.db import models

from django.contrib.postgres.fields import JSONField, ArrayField
from tutelary.decorators import permissioned_model
from core.models import RandomIDModel
from organization.models import Organization
from organization.validators import validate_contact


@permissioned_model
class Project(RandomIDModel):
    name = models.CharField(max_length=100)
    organization = models.ForeignKey(Organization)
    country = models.CharField(max_length=50, blank=True)
    description = models.TextField(null=True, blank=True)
    logo = models.ImageField(blank=True, upload_to='/image/logo')
    urls = ArrayField(models.URLField(), default=[])
    contacts = JSONField(validators=[validate_contact], default={})
    users = models.ManyToManyField('accounts.User')

    class Meta:
        ordering = ('organization', 'name')

    class TutelaryMeta:
        perm_type = 'project'
        path_fields = ('organization', 'name')
        actions = [
            ('project.list', {'description':'List organization existing '
                                'projects', 'permissions_object':
                                'organisation'}),
            ('project.view', {'description':'View organization project '
                                'projects', 'permissions_object':
                                'organisation'}),
            ('project.create', {'permissions_object': 'organisation'}),
            'project.delete'
        ]

    def __str__(self):
        return "<Organization: {name}>".format(name=self.name)
