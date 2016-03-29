from django.db import models
from django.contrib.postgres.fields import JSONField, ArrayField
# from django_countries.fields import CountryField

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


@permissioned_model
class Project(RandomIDModel):
    name = models.CharField(max_length=100)
    project_slug = models.SlugField(max_length=50, unique=True, null=True)
    organization = models.ForeignKey(Organization, related_name='projects')
    # country = CountryField()
    country = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    # logo = models.ImageField(blank=True, upload_to='/image/logo')
    archived = models.BooleanField(default=False)
    urls = ArrayField(models.URLField(), default=[])
    contacts = JSONField(validators=[validate_contact], default={})
    users = models.ManyToManyField('accounts.User')

    class Meta:
        ordering = ('organization', 'name')

    class TutelaryMeta:
        perm_type = 'project'
        path_fields = ('organization', 'id')
        actions = [
            ('project.list',
             {'description': 'List organization existing',
              'permissions_object': 'organization'}),
            ('project.create',
             {'description': 'Create an organization project',
              'permissions_object': 'organization'}),
            ('project.view',
             {'description': 'View organization project'}),
            ('project.update',
             {'description': 'Update a project'}),
            ('project.edit',
             {'description': 'Edit project details'}),
            ('project.archive',
             {'description': 'Archive an existing project'}),
            ('project.unarchive',
             {'description': 'Unarchive an existing'}),
            ('project.user.list',
             {'description': 'List users within a'}),
            ('project.user.add',
             {'description': 'Add user to a project'}),
            ('project.user.remove',
             {'description': 'Remove user from a project'}),
            ('project.resource.add',
             {'description': 'Add project resource'}),
            ('project.resource.archive',
             {'description': 'Archive a projects resource'}),
            ('project.resource.list',
             {'description': 'List project resource'}),
            ('project.resource.delete',
             {'description': 'Delete a project'}),
        ]

    def __str__(self):
        return "<Project: {name}>".format(name=self.name)
