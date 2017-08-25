from collections import OrderedDict, Sequence

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import mixins as auth_mixins
from django.contrib.auth.views import redirect_to_login
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured, PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.translation import gettext as _
from django.utils.functional import cached_property
from jsonattrs.models import Schema, compose_schemas
from organization.models import OrganizationRole
from rest_framework.exceptions import NotAuthenticated
from tutelary import mixins

from .roles import AnonymousUserRole, PublicUserRole

SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')


# tutelary
def update_permissions(permission, obj=None):
    def set_permissions(self, request, view=None):
        if (hasattr(self, 'get_organization') and
                self.get_organization().archived):
            return False
        if (hasattr(self, 'get_project') and self.get_project().archived):
            return False
        if obj and self.get_object().archived:
            return False
        return permission
    return set_permissions


# Tutelary mixin
class PermissionRequiredMixin(mixins.PermissionRequiredMixin):

    def handle_no_permission(self):
        msg = super().handle_no_permission()
        messages.add_message(self.request, messages.WARNING,
                             msg[0] if len(msg) > 0 and len(msg[0]) > 0
                             else _("You don't have permission "
                                    "for this action."))

        referer = self.request.META.get('HTTP_REFERER')
        redirect_url = self.request.META.get('HTTP_REFERER', '/')

        if (referer and '/account/login/' in referer and
                not self.request.user.is_anonymous):

            if 'organization' in self.kwargs and 'project' in self.kwargs:
                redirect_url = reverse(
                    'organization:project-dashboard',
                    kwargs={'organization': self.kwargs['organization'],
                            'project': self.kwargs['project']}
                )

        return redirect(redirect_url)


# Tutelary mixin
class LoginPermissionRequiredMixin(PermissionRequiredMixin,
                                   mixins.LoginPermissionRequiredMixin):
    pass


# Role permission mixin
class BaseRolePermissionMixin():
    """Role based permission check mixin.

       Implementers should provide one of the following:
       - a `get_permission_required` method returning an `iterable` containing
         the permissions required to access the view.
       - a `permission_required` attribute which is either a `dict` mapping
         request methods to the required permission (as a string):
            `permission_required` = {'GET': 'project.view'}
       - a `permission_required` attribute returning a single string

       Views that return a filtered queryset should implement
       `get_filtered_queryset`.

       Proivides accesss to the current users set of `OrganizationRole` and
       `ProjectRole` instances.

       Provides a `permissions` attribute which composes a unique set of all
       permissions assigned by the users organization and project roles.

       Provides role related template context variables.
    """

    def get_permission_required(self):
        if (not hasattr(self, 'permission_required') or
           self.permission_required is None):
            raise ImproperlyConfigured(
                '{0} is missing the permission_required attribute. Define '
                '{0}.permission_required, or override '
                '{0}.get_permission_required().'.format(
                    self.__class__.__name__)
            )

        perms = self.permission_required

        if isinstance(self.permission_required, dict):
            perms = self.permission_required.get(self.request.method, ())

        if isinstance(perms, str):
            perms = (perms, )

        return perms

    def get_queryset(self):
        if hasattr(self, 'get_filtered_queryset'):
            return self.get_filtered_queryset()
        else:
            return super().get_queryset()

    @cached_property
    def roles(self):
        _roles = {}
        user = self.request.user
        if user.is_anonymous:
            _roles['anonymous_user'] = AnonymousUserRole()
            return _roles
        # for org mixins get the org role
        if hasattr(self, 'get_organization'):
            try:
                role = OrganizationRole.objects.get(
                    organization=self.get_organization(),
                    user=self.request.user,
                )
                _roles['org_role'] = role
            except OrganizationRole.DoesNotExist:
                pass
        # for project mixins get org and project roles
        if hasattr(self, 'get_org_role') and self.get_org_role():
            if self._org_role not in _roles:
                _roles['org_role'] = self._org_role
        if hasattr(self, 'get_prj_role') and self.get_prj_role():
            _roles['prj_role'] = self._prj_role
        # set he default public role
        _roles['public_role'] = PublicUserRole()
        return _roles

    @cached_property
    def permissions(self):
        """Compose permissions for all roles."""
        self._perms = []
        [self._perms.extend(role.permissions) for role in self.roles.values()]
        perms = sorted(set(self._perms))
        return perms

    def get_context_data(self, *args, **kwargs):
        """Add user permissions and roles to template context."""
        context = super().get_context_data(*args, **kwargs)
        org_role = self.roles.get('org_role', None)
        prj_role = self.roles.get('prj_role', None)
        context['permissions'] = self.permissions
        context['is_superuser'] = self.request.user.is_superuser
        context['is_anonymous_user'] = self.request.user.is_anonymous()
        context['is_public_user'] = (
            True if self.roles.get('public_role', False) else False)
        context['is_org_member'] = True if org_role else False
        context['is_org_admin'] = (
            True if org_role and org_role.admin else False)
        context['is_project_member'] = True if prj_role else False
        context['is_project_user'] = (
            True if prj_role and prj_role.is_project_user else False)
        context['is_data_collector'] = (
            True if prj_role and prj_role.is_data_collector else False)
        context['is_mobile_user'] = (
            True if prj_role and prj_role.is_mobile_user else False)
        context['is_project_manager'] = (
            True if prj_role and prj_role.is_project_manager else False)
        return context


# Role permission mixin
class RolePermissionRequiredMixin(BaseRolePermissionMixin,
                                  auth_mixins.PermissionRequiredMixin):
    """Determine if the user has view permissions."""

    def has_permission(self):
        if self.request.user.is_superuser:
                return True

        perms = self.get_permission_required()

        # replace when we eventually use role authorization backend
        # user = self.request.user
        # return all(False for perm in perms
        #            if not user.has_perm(perm, obj=self.permissions))

        return False if not perms else all(
            perm in self.permissions for perm in perms)

    def handle_no_permission(self):
        msg = _("You don't have permission to perform this action.")
        if hasattr(self, 'permission_denied_message'):
            msg = self.get_permission_denied_message()
        messages.add_message(
            self.request, messages.WARNING, msg)

        referer = self.request.META.get('HTTP_REFERER')
        redirect_url = self.request.META.get('HTTP_REFERER', '/')

        if (referer and '/account/login/' in referer and
                not self.request.user.is_anonymous):

            if 'organization' in self.kwargs and 'project' in self.kwargs:
                redirect_url = reverse(
                    'organization:project-dashboard',
                    kwargs={'organization': self.kwargs['organization'],
                            'project': self.kwargs['project']}
                )
                if redirect_url == self.request.get_full_path():
                    redirect_url = reverse(
                        'organization:dashboard',
                        kwargs={'slug': self.kwargs['organization']}
                    )

            elif 'slug' in self.kwargs:
                redirect_url = reverse(
                    'organization:dashboard',
                    kwargs={'slug': self.kwargs['slug']}
                )
                if redirect_url == self.request.get_full_path():
                    redirect_url = reverse('core:dashboard')

        return redirect(redirect_url)


# Role permission mixin
class RoleLoginPermissionRequiredMixin(RolePermissionRequiredMixin):
    """Ensure user is logged in."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            if getattr(self, 'raise_exception', False):
                raise PermissionDenied(self.get_permission_denied_message())
            return redirect_to_login(self.request.get_full_path(),
                                     self.get_login_url(),
                                     self.get_redirect_field_name())
        return super().dispatch(request, *args, **kwargs)


class PermissionFilterMixin:
    """Provide permission filtering of API list views.

       Objects can be filtered based on user permssions provided as
       http GET request parameters, eg `/projects/?permissions=party.create`
       will list all project where the user has 'party.create' permissions.

       Implementers should provide a `permission_filter_queryset` method.
    """

    def dispatch(self, request, *args, **kwargs):
        permissions = request.GET.get('permissions', None)
        if permissions:
            actions = tuple(permissions.split(','))
            self.permission_filter = actions

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if hasattr(self, 'permission_filter_queryset'):
            return self.permission_filter_queryset()
        return super().get_filtered_queryset()


# Role permission mixin
class APIPermissionRequiredMixin(BaseRolePermissionMixin):
    """Check permission required on API views."""

    def get_permission_denied_message(self, default=None):
        if hasattr(self, 'permission_denied_message'):
            return (self.permission_denied_message,)

    def _http_method_allowed(self, request):
        if request.method not in self.allowed_methods:
            self.http_method_not_allowed(request)
        if (request.method not in SAFE_METHODS and not
                request.user.is_authenticated):
                raise NotAuthenticated

    def check_permissions(self, request):
        self._http_method_allowed(request)
        if self.request.user.is_superuser:
            return True

        perms = self.get_permission_required()
        msg = self.get_permission_denied_message(
            default="Permission denied."
        )
        if isinstance(msg, Sequence):
            msg = msg[0]
        if not perms or not all(perm in self.permissions for perm in perms):
            self.permission_denied(request, message=msg)


class SchemaSelectorMixin():

    def get_attributes(self, project):
        content_type_to_selectors = self._get_content_types_to_selectors()

        attributes_for_models = {}
        for content_type, selector_fields in content_type_to_selectors.items():
            label = '{}.{}'.format(content_type.app_label, content_type.model)
            model = content_type.model_class()
            choices = []
            selectors = OrderedDict({})
            attributes_for_models[label] = OrderedDict({})

            for selector_field in selector_fields:
                field = model._meta.get_field(selector_field.partition('.')[0])
                if field.choices:
                    choices = [choice[0] for choice in field.choices]
                else:
                    selector = project
                    sf = selector_field.partition('.')[-1]
                    sf = sf.replace('.pk', '_id')
                    selector = getattr(selector, sf, None)
                    if selector:
                        selectors[sf] = selector

            if selectors and not choices:
                defaults = list(selectors.values())
                schemas = Schema.objects.lookup(
                    content_type=content_type, selectors=defaults)
                if schemas:
                    attributes, _, _ = compose_schemas(*schemas)
                    attributes_for_models[label]['DEFAULT'] = attributes

            if selectors and choices:
                for choice in choices:
                    conditionals = list(selectors.values()) + [choice]
                    schemas = Schema.objects.lookup(
                        content_type=content_type,
                        selectors=conditionals)
                    if schemas:
                        attributes, _, _ = compose_schemas(*schemas)
                        attributes_for_models[label][choice] = attributes

        return attributes_for_models

    def get_model_attributes(self, project, content_type):
        attributes_for_models = self.get_attributes(project)
        return attributes_for_models[content_type]

    def get_conditional_selector(self, content_type):
        content_type_to_selectors = self._get_content_types_to_selectors()
        selectors = list(content_type_to_selectors[content_type])
        if '.' in selectors[-1]:
            return None
        else:
            return selectors[-1]

    def _get_content_types_to_selectors(self):
        content_type_to_selectors = dict()
        for k, v in settings.JSONATTRS_SCHEMA_SELECTORS.items():
            a, m = k.split('.')
            content_type_to_selectors[
                ContentType.objects.get(app_label=a, model=m)
            ] = v
        return content_type_to_selectors
