from django.db import models
from django.contrib.postgres.fields import JSONField, ArrayField

from tutelary.decorators import permissioned_model

from core.models import RandomIDModel
from .validators import validate_contact


@permissioned_model
class Organization(RandomIDModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    archived = models.BooleanField(default=False)
    urls = ArrayField(models.URLField(), default=[])
    contacts = JSONField(validators=[validate_contact], default={})
    users = models.ManyToManyField('accounts.User',
                                   related_name='organizations')
    # logo = TemporalForeignKey('Resource')

    class TutelaryMeta:
        perm_type = 'organization'
        path_fields = ('slug',)
        actions = (('org.list', {'description': "List existing organisations",
                                 'permissions_object': None}),
                   ('org.view', "View existing organisations"),
                   ('org.create', {'description': "Create organisations",
                                   'permissions_object': None}),
                   ('org.update', "Update an existing organization"),
                   ('org.archive', "Archive an existing organization"),
                   ('org.unarchive', "Unarchive an existing organization"),
                   ('org.users.list', "List members of an organization"),
                   ('org.users.add', "Add a member to an organization"),
                   ('org.users.remove', "Remove a member from an organization"))

    def __str__(self):
        return "<Organization: {name}>".format(name=self.name)
