from django.db import models
from django.contrib.postgres.fields import JSONField, ArrayField
from django_countries.fields import CountryField
from django.dispatch import receiver

from tutelary.decorators import permissioned_model
from tutelary.models import Role, Policy

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
    users = models.ManyToManyField('accounts.User', through='OrganizationRole')
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


class OrganizationRole(RandomIDModel):
    organization = models.ForeignKey(Organization)
    user = models.ForeignKey('accounts.User')
    admin = models.BooleanField(default=False)


@receiver(models.signals.post_save, sender=OrganizationRole)
def assign_org_permissions(sender, instance, created, **kwargs):
    if created:
        # role = Role.objects.get(
        #     name='org-admin',
        #     variables={'organization': instance.organization.slug}
        # )
        policy = Policy.objects.get(name='org-admin')
        instance.user.assign_policies(
            (policy, {'organization': instance.organization.slug})
        )
    else:
        pass
        # check if the user has exactly the policies they need


@permissioned_model
class Project(RandomIDModel):
    name = models.CharField(max_length=100)
    organization = models.ForeignKey(Organization, related_name='projects')
    country = CountryField()
    description = models.TextField(null=True, blank=True)
    # logo = models.ImageField(blank=True, upload_to='/image/logo')
    archived = models.BooleanField(default=False)
    urls = ArrayField(models.URLField(), default=[])
    contacts = JSONField(validators=[validate_contact], default={})
    users = models.ManyToManyField('accounts.User', through='ProjectRole')

    class Meta:
        ordering = ('organization', 'name')

    class TutelaryMeta:
        perm_type = 'project'
        path_fields = ('organization', 'id')
        actions = [
            ('project.list',
             {'description': 'List organization existing',
              'permissions_object': 'organization'}),
            ('project.view',
             {'description': 'View organization project'}),
            ('project.edit',
             {'description': 'Edit project details'}),
            ('project.archive',
             {'description': 'Archive an existing project'}),
            ('project.unarchive',
             {'description': 'Unarchive an existing'}),
            ('project.users.list',
             {'description': 'List users within a'}),
            ('project.users.add',
             {'description': 'Add user to a project'}),
            ('project.users.remove',
             {'description': 'Remove user from a project'}),
            # ('project.resource.add',
            #  {'description': 'Add project resource',
            #   'permissions_object': 'organization'}),
            # ('project.resource.archive',
            #  {'description': 'Archive a projects resource',
            #   'permissions_object': 'organization'}),
            # ('project.resource.list',
            #  {'description': 'List project resource',
            #   'permissions_object': 'organization'}),
            # ('project.resource.delete',
            #  {'description': 'Delete a project',
            #   'permissions_object': 'organization'}),
        ]

    def __str__(self):
        return "<Project: {name}>".format(name=self.name)


class ProjectRole(RandomIDModel):
    project = models.ForeignKey(Project)
    user = models.ForeignKey('accounts.User')
    manager = models.BooleanField(default=False)
    collector = models.BooleanField(default=False)

    class Meta:
        unique_together = ('project', 'user')
