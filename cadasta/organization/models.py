from django.utils.functional import cached_property
from django.core.urlresolvers import reverse
from django.conf import settings
from django.db import models
from django_countries.fields import CountryField
from django.contrib.postgres.fields import JSONField, ArrayField
from django.dispatch import receiver
from django.utils.translation import ugettext as _
from django.utils.encoding import iri_to_uri
import django.contrib.gis.db.models as gismodels
from simple_history.models import HistoricalRecords
from shapely.geometry import Polygon
from shapely.wkt import dumps

from tutelary.decorators import permissioned_model
from tutelary.models import Policy

from core.models import RandomIDModel, SlugModel
from geography.models import WorldBorder
from resources.mixins import ResourceModelMixin
from .validators import validate_contact
from .choices import ROLE_CHOICES, ACCESS_CHOICES
from . import messages


PERMISSIONS_DIR = settings.BASE_DIR + '/permissions/'


def get_policy_instance(policy_name, variables):
    policy = Policy.objects.get(name=policy_name)
    return (policy, variables)


@permissioned_model
class Organization(SlugModel, RandomIDModel):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    description = models.TextField(null=True, blank=True)
    archived = models.BooleanField(default=False)
    urls = ArrayField(models.URLField(), default=[])
    contacts = JSONField(validators=[validate_contact], default=[],
                         null=True, blank=True)
    users = models.ManyToManyField('accounts.User',
                                   through='OrganizationRole',
                                   related_name='organizations')
    # TEMPORARY:
    logo = models.URLField(null=True)
    # logo = TemporalForeignKey('Resource')
    last_updated = models.DateTimeField(auto_now=True)
    access = models.CharField(
        default="public", choices=ACCESS_CHOICES, max_length=8
    )

    history = HistoricalRecords()

    class Meta:
        ordering = ('name',)

    class TutelaryMeta:
        perm_type = 'organization'
        path_fields = ('slug',)
        actions = (
            ('org.list',
             {'description': _("List existing organizations"),
              'permissions_object': None}),
            ('org.create',
             {'description': _("Create organizations"),
              'permissions_object': None}),
            ('org.view',
             {'description': _("View existing organizations"),
              'error_message': messages.ORG_VIEW}),
            ('org.view_archived',
             {'description': _("View archived organization"),
              'error_message': messages.ORG_VIEW}),
            ('org.update',
             {'description': _("Update an existing organization"),
              'error_message': messages.ORG_EDIT}),
            ('org.archive',
             {'description': _("Archive an existing organization"),
              'error_message': messages.ORG_ARCHIVE}),
            ('org.unarchive',
             {'description': _("Unarchive an existing organization"),
              'error_message': messages.ORG_UNARCHIVE}),
            ('org.users.list',
             {'description': _("List members of an organization"),
              'error_message': messages.ORG_USERS_LIST}),
            ('org.users.add',
             {'description': _("Add a member to an organization"),
              'error_message': messages.ORG_USERS_ADD}),
            ('org.users.edit',
             {'description': _("Edit a member of an organization"),
              'error_message': messages.ORG_USERS_EDIT}),
            ('org.users.remove',
             {'description': _("Remove a member from an organization"),
              'error_message': messages.ORG_USERS_REMOVE})
        )

    def __str__(self):
        return "<Organization: {name}>".format(name=self.name)

    def __repr__(self):
        repr_string = ('<Organization id={obj.id} name={obj.name}'
                       ' slug={obj.slug}'
                       ' archived={obj.archived}'
                       ' access={obj.access}>')
        return repr_string.format(obj=self)

    def public_projects(self):
        return self.projects.filter(access='public', archived=False)

    def all_projects(self):
        return self.projects.all()


class OrganizationRole(RandomIDModel):
    organization = models.ForeignKey(Organization)
    user = models.ForeignKey('accounts.User')
    admin = models.BooleanField(default=False)

    history = HistoricalRecords()

    class Meta:
        unique_together = ('organization', 'user')

    def __repr__(self):
        repr_string = ('<OrganizationRole id={obj.id} user={obj.user.username}'
                       ' organization={obj.organization.slug}'
                       ' admin={obj.admin}>')
        return repr_string.format(obj=self)


def assign_org_policies(instance, delete=False):
    assigned_policies = instance.user.assigned_policies()
    policy_vars = {'organization': instance.organization.slug}

    org_admin = get_policy_instance('org-admin', policy_vars)
    is_admin = org_admin in assigned_policies

    org_member = get_policy_instance('org-member', policy_vars)
    is_member = org_member in assigned_policies

    if not is_admin and (instance.admin and not delete):
        assigned_policies.append(org_admin)
    elif is_admin and (not instance.admin or delete):
        assigned_policies.remove(org_admin)

    if not is_member and not delete:
        assigned_policies.append(org_member)
    elif is_member and delete:
        assigned_policies.remove(org_member)

    instance.user.assign_policies(*assigned_policies)


@receiver(models.signals.post_save, sender=OrganizationRole)
def assign_org_permissions(sender, instance, **kwargs):
    assign_org_policies(instance)


@receiver(models.signals.pre_delete, sender=OrganizationRole)
def remove_org_permissions(sender, instance, **kwargs):
    prjs = instance.organization.projects.values_list('id', flat=True)
    ProjectRole.objects.filter(user=instance.user,
                               project_id__in=prjs).delete()
    assign_org_policies(instance, delete=True)


@permissioned_model
class Project(ResourceModelMixin, SlugModel, RandomIDModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=50, unique=True, null=True)
    organization = models.ForeignKey(Organization, related_name='projects')
    country = CountryField(null=True)
    description = models.TextField(null=True, blank=True)
    # logo = models.ImageField(blank=True, upload_to='/image/logo')
    archived = models.BooleanField(default=False)
    urls = ArrayField(models.URLField(), default=[])
    contacts = JSONField(validators=[validate_contact], default=[],
                         null=True, blank=True)
    users = models.ManyToManyField('accounts.User', through='ProjectRole')
    last_updated = models.DateTimeField(auto_now=True)
    extent = gismodels.PolygonField(null=True)
    access = models.CharField(
        default="public", choices=ACCESS_CHOICES, max_length=8
    )
    current_questionnaire = models.CharField(
        max_length=24, null=True, blank=True
    )

    history = HistoricalRecords()

    class Meta:
        ordering = ('organization', 'name')
        unique_together = ('organization', 'name')

    class TutelaryMeta:
        perm_type = 'project'
        path_fields = ('organization', 'slug')
        actions = (
            ('project.list',
             {'description': _("List existing projects in an organization"),
              'permissions_object': 'organization'}),
            ('project.create',
             {'description': _("Create projects in an organization"),
              'permissions_object': 'organization'}),
            ('project.view',
             {'description': _("View existing projects"),
              'error_message': messages.PROJ_VIEW}),
            ('project.view_private',
             {'description': _("View private projects"),
              'error_message': messages.PROJ_VIEW}),
            ('project.view_archived',
             {'description': _("View archived projects"),
              'error_message': messages.PROJ_VIEW}),
            ('project.update',
             {'description': _("Update an existing project"),
              'error_message': messages.PROJ_EDIT}),
            ('project.archive',
             {'description': _("Archive an existing project"),
              'error_message': messages.PROJ_ARCHIVE}),
            ('project.unarchive',
             {'description': _("Unarchive an existing project"),
              'error_message': messages.PROJ_UNARCHIVE}),
            ('project.users.list',
             {'description': _("List users within a project"),
              'error_message': messages.PROJ_USERS_LIST}),
            ('project.users.add',
             {'description': _("Add user to a project"),
              'error_message': messages.PROJ_USERS_ADD}),
            ('project.users.edit',
             {'description': _("Edit roles of user in a project"),
              'error_message': messages.PROJ_USERS_EDIT}),
            ('project.users.remove',
             {'description': _("Remove user from a project"),
              'error_message': messages.PROJ_USERS_REMOVE}),
            ('project.download',
             {'description': _("Export data from a project"),
              'error_message': messages.PROJ_DOWNLOAD}),
            ('project.import',
             {'description': _("Import data to a project"),
              'error_message': messages.PROJ_IMPORT}),
        )

    def __str__(self):
        return "<Project: {name}>".format(name=self.name)

    def __repr__(self):
        repr_string = ('<Project id={obj.id} name={obj.name}'
                       ' slug={obj.slug}'
                       ' organization={obj.organization.slug}'
                       ' archived={obj.archived}'
                       ' access={obj.access}>')
        return repr_string.format(obj=self)

    @property
    def ui_class_name(self):
        return _("Project")

    def get_absolute_url(self):
        return iri_to_uri(reverse(
            'organization:project-dashboard',
            kwargs={
                'organization': self.organization.slug,
                'project': self.slug,
            },
        ))

    @cached_property
    def has_records(self):
        check_records = ['parties', 'tenure_relationships', 'spatial_units']
        return any([getattr(self, r).exists() for r in check_records])

    def save(self, *args, **kwargs):
        if ((self.country is None or self.country == '') and
           self.extent is not None):
            try:
                self.country = WorldBorder.objects.get(
                    mpoly__contains=self.extent.centroid
                ).iso2
            except:
                pass
        super().save(*args, **kwargs)

    def public(self):
        return self.access == 'public'


def reassign_project_extent(instance):
    coords = [list(x) for x in list(instance.extent.boundary.coords)]
    for point in coords:
        if point[0] >= -180 and point[0] <= 180:
            return
    while coords[0][0] < -180:
        for point in coords:
            point[0] += 360
    while coords[0][0] > 180:
        for point in coords:
            point[0] -= 360
    extent = []
    for point in coords:
        latlng = [point[0], point[1]]
        extent.append(tuple(latlng))
    instance.extent = dumps(Polygon(extent))


@receiver(models.signals.pre_save, sender=Project)
def check_extent(sender, instance, **kwargs):
    if instance.extent:
        reassign_project_extent(instance)


class ProjectRole(RandomIDModel):
    project = models.ForeignKey(Project)
    user = models.ForeignKey('accounts.User')
    role = models.CharField(max_length=2,
                            choices=ROLE_CHOICES,
                            default='PU')

    history = HistoricalRecords()

    class Meta:
        unique_together = ('project', 'user')

    def __repr__(self):
        repr_string = ('<ProjectRole id={obj.id} user={obj.user.username}'
                       ' project={obj.project.slug}'
                       ' role={obj.role}>')
        return repr_string.format(obj=self)


def assign_prj_policies(role, delete=False):
    assigned_policies = role.user.assigned_policies()
    policy_vars = {
        'organization': role.project.organization.slug,
        'project': role.project.slug
    }

    project_manager = get_policy_instance('project-manager', policy_vars)
    is_manager = project_manager in assigned_policies

    project_user = get_policy_instance('project-user', policy_vars)
    is_user = project_user in assigned_policies

    data_collector = get_policy_instance('data-collector', policy_vars)
    is_collector = data_collector in assigned_policies

    new_role = role.role

    if is_user and (delete or not new_role == 'PU'):
        assigned_policies.remove(project_user)
    elif not is_user and new_role == 'PU':
        assigned_policies.append(project_user)

    if is_collector and (delete or not new_role == 'DC'):
        assigned_policies.remove(data_collector)
    elif not is_collector and new_role == 'DC':
        assigned_policies.append(data_collector)

    if is_manager and (delete or not new_role == 'PM'):
        assigned_policies.remove(project_manager)
    elif not is_manager and new_role == 'PM':
        assigned_policies.append(project_manager)

    role.user.assign_policies(*assigned_policies)


@receiver(models.signals.post_save, sender=ProjectRole)
def assign_project_permissions(sender, instance, **kwargs):
    assign_prj_policies(instance)


@receiver(models.signals.post_delete, sender=ProjectRole)
def remove_project_permissions(sender, instance, **kwargs):
    assign_prj_policies(instance, delete=True)
