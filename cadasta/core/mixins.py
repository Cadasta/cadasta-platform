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


# tutelary object permission check
def check_perms(user, actions, objs, method=None):
    if actions is False:
        return False
    if actions is not None:
        for a in actions:
            for o in objs:
                test_obj = None
                if o is not None:
                    test_obj = o.get_permissions_object(a)
                if not user.has_perm(a, test_obj):
                    return False
    return True


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


# Tutelary mixin
class LoginPermissionRequiredMixin(PermissionRequiredMixin,
                                   mixins.LoginPermissionRequiredMixin):
    pass


# Role permission mixin
class BaseRolePermissionMixin():

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

    def set_user_roles(self):
        """Set user roles."""
        self._roles = []
        user = self.request.user
        if user.is_anonymous:
            self._roles.append(AnonymousUserRole())
            return
        # for org mixins get the org role
        if hasattr(self, 'get_organization'):
            try:
                role = OrganizationRole.objects.get(
                    organization=self.get_organization(),
                    user=self.request.user,
                )
                self._roles.append(role)
            except OrganizationRole.DoesNotExist:
                pass
        # for project mixins get org and project roles
        if hasattr(self, 'get_org_role') and self.get_org_role():
            if self._org_role not in self._roles:
                self._roles.append(self._org_role)
        if hasattr(self, 'get_prj_role') and self.get_prj_role():
            self._roles.append(self._prj_role)
        # set he default public role
        self._roles.append(PublicUserRole())

    @cached_property
    def permissions(self):
        # compose permissions for all roles
        self._perms = []
        if hasattr(self, '_roles'):
            [self._perms.extend(role.permissions) for role in self._roles]
        perms = sorted(set(self._perms))
        return perms


# Role permission mixin
class RolePermissionRequiredMixin(BaseRolePermissionMixin,
                                  auth_mixins.PermissionRequiredMixin):
    def has_permission(self):
        if self.request.user.is_superuser:
                return True
        if not hasattr(self, '_roles'):
            self.set_user_roles()

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
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            if hasattr(self, 'raise_exception') and self.raise_exception:
                raise PermissionDenied(self.get_permission_denied_message())
            return redirect_to_login(self.request.get_full_path(),
                                     self.get_login_url(),
                                     self.get_redirect_field_name())

        return super().dispatch(request, *args, **kwargs)


# Role permission mixin
class APIPermissionRequiredMixin(BaseRolePermissionMixin):

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
        if not hasattr(self, '_roles'):
            self.set_user_roles()

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
