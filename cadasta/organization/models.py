from django.conf import settings
from django.db import models
from django_countries.fields import CountryField
from django.contrib.postgres.fields import JSONField, ArrayField
from django.dispatch import receiver
from django.utils.translation import ugettext as _
import django.contrib.gis.db.models as gismodels

from tutelary.decorators import permissioned_model
from tutelary.models import Policy

from core.models import RandomIDModel
from .validators import validate_contact

PERMISSIONS_DIR = settings.BASE_DIR + '/permissions/'


def get_policy_instance(policy_name, variables):
    try:
        policy = Policy.objects.get(name=policy_name)
    except Policy.DoesNotExist:
        policy = Policy.objects.create(
            name=policy_name,
            body=open(PERMISSIONS_DIR + policy_name + '.json').read()
        )
    return (policy, variables)


@permissioned_model
class Organization(RandomIDModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    archived = models.BooleanField(default=False)
    urls = ArrayField(models.URLField(), default=[])
    contacts = JSONField(validators=[validate_contact], default={})
    users = models.ManyToManyField('accounts.User',
                                   through='OrganizationRole',
                                   related_name='organizations')
    # TEMPORARY:
    logo = models.URLField(null=True)
    # logo = TemporalForeignKey('Resource')
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)

    class TutelaryMeta:
        perm_type = 'organization'
        path_fields = ('slug',)
        actions = (
            ('org.list',
             {'description': _("List existing organisations"),
              'permissions_object': None}),
            ('org.view',
             {'description': _("View existing organisations")}),
            ('org.create',
             {'description': "Create organisations",
              'permissions_object': None}),
            ('org.update',
             {'description': _("Update an existing organization")}),
            ('org.archive',
             {'description': _("Archive an existing organization")}),
            ('org.unarchive',
             {'description': _("Unarchive an existing organization")}),
            ('org.users.list',
             {'description': _("List members of an organization")}),
            ('org.users.add',
             {'description': _("Add a member to an organization")}),
            ('org.users.remove',
             {'description': _("Remove a member from an organization")})
        )

    def __str__(self):
        return "<Organization: {name}>".format(name=self.name)


class OrganizationRole(RandomIDModel):
    organization = models.ForeignKey(Organization)
    user = models.ForeignKey('accounts.User')
    admin = models.BooleanField(default=False)


@receiver(models.signals.post_save, sender=OrganizationRole)
def assign_org_permissions(sender, instance, **kwargs):
    policy_instance = get_policy_instance('org-admin', {
        'organization': instance.organization.slug})
    assigned_policies = instance.user.assigned_policies()
    has_policy = policy_instance in assigned_policies

    if not has_policy and instance.admin:
        assigned_policies.append(policy_instance)
    elif has_policy and not instance.admin:
        assigned_policies.remove(policy_instance)

    instance.user.assign_policies(*assigned_policies)


@receiver(models.signals.pre_delete, sender=OrganizationRole)
def remove_project_membership(sender, instance, **kwargs):
    prjs = instance.organization.projects.values_list('id', flat=True)
    ProjectRole.objects.filter(user=instance.user,
                               project_id__in=prjs).delete()


@permissioned_model
class Project(RandomIDModel):
    ACCESS_CHOICES = [
        ("public", _("Public")),
        ("private", _("Private")),
    ]
    name = models.CharField(max_length=100)
    project_slug = models.SlugField(max_length=50, unique=True, null=True)
    organization = models.ForeignKey(Organization, related_name='projects')
    country = CountryField(null=True)
    description = models.TextField(null=True, blank=True)
    # logo = models.ImageField(blank=True, upload_to='/image/logo')
    archived = models.BooleanField(default=False)
    urls = ArrayField(models.URLField(), default=[])
    contacts = JSONField(validators=[validate_contact], default={})
    users = models.ManyToManyField('accounts.User', through='ProjectRole')
    last_updated = models.DateTimeField(auto_now=True)
    extent = gismodels.PolygonField(null=True)
    access = models.CharField(default="public", choices=ACCESS_CHOICES,
                              max_length=15, blank=True)

    class Meta:
        ordering = ('organization', 'name')

    class TutelaryMeta:
        perm_type = 'project'
        path_fields = ('organization', 'project_slug')
        actions = (
            ('project.list',
             {'description': _("List organization existing"),
              'permissions_object': 'organization'}),
            ('project.create',
             {'description': _("Create an organization project"),
              'permissions_object': 'organization'}),
            ('project.view_private',
             {'description': _("View a private project within a organization"),
              'permissions_object': 'organization'}),
            ('project.view',
             {'description': _("View organization project")}),
            ('project.update',
             {'description': ("Update a project")}),
            ('project.archive',
             {'description': _("Archive an existing project")}),
            ('project.unarchive',
             {'description': _("Unarchive an existing")}),
            ('project.users.list',
             {'description': _("List users within a")}),
            ('project.users.add',
             {'description': _("Add user to a project")}),
            ('project.users.edit',
             {'description': _("Edit roles of user in a project")}),
            ('project.users.remove',
             {'description': _("Remove user from a project")}),
        )

    def __str__(self):
        return "<Project: {name}>".format(name=self.name)


class ProjectRole(RandomIDModel):
    project = models.ForeignKey(Project)
    user = models.ForeignKey('accounts.User')
    manager = models.BooleanField(default=False)
    collector = models.BooleanField(default=False)

    class Meta:
        unique_together = ('project', 'user')


@receiver(models.signals.post_save, sender=ProjectRole)
def assign_project_permissions(sender, instance, **kwargs):
    assigned_policies = instance.user.assigned_policies()

    policy_instance = get_policy_instance('project-manager', {
        'organization': instance.project.organization.slug,
        'project': instance.project.project_slug
    })
    has_policy = policy_instance in assigned_policies

    if not has_policy and instance.manager:
        assigned_policies.append(policy_instance)
    elif has_policy and not instance.manager:
        assigned_policies.remove(policy_instance)

    policy_instance = get_policy_instance('data-collector', {
        'organization': instance.project.organization.slug,
        'project': instance.project.project_slug
    })
    has_policy = policy_instance in assigned_policies

    if not has_policy and instance.collector:
        assigned_policies.append(policy_instance)
    elif has_policy and not instance.collector:
        assigned_policies.remove(policy_instance)

    instance.user.assign_policies(*assigned_policies)
