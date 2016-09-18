from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import get_object_or_404
from django.db.models import Q

from tutelary.models import Role, check_perms

from ..models import Organization, Project, OrganizationRole, ProjectRole


class OrganizationMixin:
    def get_organization(self, lookup_kwarg='slug'):
        if lookup_kwarg == 'slug' and hasattr(self, 'org_lookup'):
            lookup_kwarg = self.org_lookup

        if not hasattr(self, 'org'):
            self.org = get_object_or_404(Organization,
                                         slug=self.kwargs[lookup_kwarg])
        return self.org

    def get_perms_objects(self):
        return [self.get_organization()]


class OrganizationRoles(OrganizationMixin):
    lookup_field = 'username'
    org_lookup = 'organization'

    def get_queryset(self):
        self.org = self.get_organization()
        return self.org.users.all()

    def get_serializer_context(self, *args, **kwargs):
        context = super(OrganizationRoles, self).get_serializer_context(
            *args, **kwargs)
        context['organization'] = self.get_organization()
        context['domain'] = get_current_site(self.request).domain
        context['sitename'] = settings.SITE_NAME
        return context


class ProjectMixin:
    def get_project(self):
        if not hasattr(self, 'prj'):
            self.prj = get_object_or_404(
                Project,
                organization__slug=self.kwargs['organization'],
                slug=self.kwargs['project']
            )
        return self.prj


class ProjectRoles(ProjectMixin):
    lookup_field = 'username'

    def get_perms_objects(self):
        return [self.get_project()]

    def get_queryset(self):
        self.prj = self.get_project()
        return self.prj.users.all()

    def get_serializer_context(self, *args, **kwargs):
        context = super(ProjectRoles, self).get_serializer_context(
            *args, **kwargs)
        context['project'] = self.get_project()

        return context


class ProjectQuerySetMixin:
    def get_queryset(self):
        if not hasattr(self, 'su_role'):
            self.su_role = Role.objects.get(name='superuser')

        if (not isinstance(self.request.user, AnonymousUser) and
            any([isinstance(pol, Role) and pol == self.su_role
                 for pol in self.request.user.assigned_policies()])):
            return Project.objects.all()

        if hasattr(self.request.user, 'organizations'):
            orgs = self.request.user.organizations.all()
            if len(orgs) > 0:
                return Project.objects.filter(
                    Q(access='public') | Q(organization__in=orgs)
                )

        return Project.objects.filter(access='public')


class ProjectAdminCheckMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_admin = None

    @property
    def is_administrator(self):
        if self.is_admin is None:
            su_role = Role.objects.filter(name='superuser')
            org_admins = [
                role.user for role in OrganizationRole.objects.filter(
                    organization=self.get_project().organization,
                    admin=True
                )
            ]
            proj_managers = [
                role.user for role in ProjectRole.objects.filter(
                    project=self.get_project(),
                    role='PM'
                )

            ]
            self.is_admin = False
            if len(su_role) > 0:
                if hasattr(self.request.user, 'assigned_policies'):
                    if su_role[0] in self.request.user.assigned_policies():
                        self.is_admin = True
            if (self.request.user in org_admins or
               self.request.user in proj_managers):
                self.is_admin = True
        return self.is_admin

    @property
    def is_allowed_add_resource(self):
        is_admin = self.is_administrator
        if is_admin:
            is_allowed_add_resource = True
        else:
            data_collectors = [
                role.user for role in ProjectRole.objects.filter(
                    project=self.get_project(),
                    role='DC'
                )
            ]

            is_allowed_add_resource = False
            if self.request.user in data_collectors:
                is_allowed_add_resource = True
        return is_allowed_add_resource

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['is_administrator'] = self.is_administrator
        context['is_allowed_add_resource'] = self.is_allowed_add_resource
        return context


class ProjectCreateCheckMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_allow = None

    @property
    def add_allowed(self):
        if self.add_allow is None:
            if (hasattr(self, 'project_create_check_multiple') and
               self.project_create_check_multiple):
                self.add_allow = self.add_allowed_multiple()
            else:
                self.add_allow = self.add_allowed_single()
            self.add_allow = self.add_allow or self.is_superuser
        return self.add_allow

    def add_allowed_single(self):
        return check_perms(self.request.user, ('project.create',),
                           (self.get_object(),))

    def add_allowed_multiple(self):
        chk = False
        if Organization.objects.exists():
            u = self.request.user
            if hasattr(u, 'organizations'):
                chk = any([
                    check_perms(u, ('project.create',), (o,))
                    for o in u.organizations.all()
                ])
        return chk

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['add_allowed'] = self.add_allowed
        return context


class OrgAdminCheckMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_admin = None

    @property
    def is_administrator(self):
        if self.is_admin is None:
            su_role = Role.objects.filter(name='superuser')
            if hasattr(self, 'get_organization'):
                org = self.get_organization()
            else:
                org = self.get_object()
            org_admins = [
                role.user for role in OrganizationRole.objects.filter(
                    organization=org,
                    admin=True
                )
            ]
            self.is_admin = False
            if len(su_role) > 0:
                if hasattr(self.request.user, 'assigned_policies'):
                    if su_role[0] in self.request.user.assigned_policies():
                        self.is_admin = True
            if self.request.user in org_admins:
                self.is_admin = True
        return self.is_admin

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['is_administrator'] = self.is_administrator
        return context
