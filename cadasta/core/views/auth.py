from django.contrib.auth.models import Group
from django.contrib.auth import mixins as auth_mixins
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied, ImproperlyConfigured

from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext as _
from organization.models import Organization, OrganizationRole


class LoginRequiredMixin(auth_mixins.LoginRequiredMixin):
    """
    This mixin should be added to views that require a logged-in user.

    We are overwriting Django's default LoginRequiredMixin because it handles
    unauthenticated users in handle_no_permission, which we overwrite in
    PermissionRequiredMixin to handle specific redirections based on the users
    HTTP referer. Both LoginRequiredMixin and PermissionRequiredMixin are used
    together in many views.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            if hasattr(self, 'raise_exception') and self.raise_exception:
                raise PermissionDenied(self.get_permission_denied_message())

            return redirect_to_login(self.request.get_full_path(),
                                     self.get_login_url(),
                                     self.get_redirect_field_name())

        return super().dispatch(request, *args, **kwargs)


class PermissionRequiredMixin(auth_mixins.UserPassesTestMixin):
    """
    The mixin should be added to views where a set of permissions need to be
    fulfilled to access the view. It extends Django's UserPassesTestMixin,
    which allows us to implement a custom `test_func` to validate permissions.

    Views that use the mixin must implement the method `get_perms`.
    """
    permission_denied_message = _("You don't have permission for this action.")

    def handle_no_permission(self):
        """
        If permission to access a view was denied the user is redirected to:

        - The previous page if the user did not arrive from the login page.

        Otherwise:

        - The platform dashboard if the user tried to access an organization
          dashboard
        - The organization dashboard if the user tried to access an
          organization page or a project dashbaord.
        - The project dashboard if the user tried to access a project page.
        """
        if hasattr(self, 'raise_exception') and self.raise_exception:
            raise PermissionDenied(self.permission_denied_message)

        messages.add_message(self.request,
                             messages.WARNING,
                             self.permission_denied_message)

        referer = self.request.META.get('HTTP_REFERER')
        redirect_url = self.request.META.get('HTTP_REFERER', '/')

        if (referer and '/account/login/' in referer and
                not self.request.user.is_anonymous):

            if 'organization' in self.kwargs and 'project' in self.kwargs:
                # The user arrived from a project page;
                # redirect to the project dashboard
                redirect_url = reverse(
                    'organization:project-dashboard',
                    kwargs={'organization': self.kwargs['organization'],
                            'project': self.kwargs['project']}
                )
                if redirect_url == self.request.get_full_path():
                    # The user arrived from the project dashboard;
                    # redirect to the project's organization dashboard
                    redirect_url = reverse(
                        'organization:dashboard',
                        kwargs={'slug': self.kwargs['organization']}
                    )

            elif 'slug' in self.kwargs:
                # The user arrived from an organization page;
                # redirect to the organization dashboard
                redirect_url = reverse(
                    'organization:dashboard',
                    kwargs={'slug': self.kwargs['slug']}
                )
                if redirect_url == self.request.get_full_path():
                    redirect_url = reverse('core:dashboard')

        return redirect(redirect_url)

    def get_permission_required(self):
        """
        Returns the permissions required for this view.

        For complex permission requirements (i.e. if the required permissions
        depend on a object's state) this method can be overwritten. Otherwise,
        the attribute `permission_required` must be defined for the view.
        """
        if not hasattr(self, 'permission_required'):
            raise ImproperlyConfigured(
                'Instances of PermissionRequiredMixin require either a '
                'definition of "permission_required" or an implementation of '
                '"get_permission_required')
        return self.permission_required

    def get_perms(self):
        """
        An abstract method, which must be overwritten by the implementing view.

        If implemented it should return a list of permission code names the
        user has for the given view.
        """
        raise ImproperlyConfigured(
            'Instances of PermissionRequiredMixin must implement method '
            '"get_perms"')

    def has_permission(self):
        """
        Returns True if all required permissions are met by the user's
        permissions as returned by `get_perms`.
        """
        permissions_required = self.get_permission_required()
        if not isinstance(permissions_required, (list, tuple)):
            permissions_required = (permissions_required, )

        perms = self.get_perms()
        return all(perm in perms for perm in permissions_required)

    def test_func(self):
        """
        `test_func` is the entry point for UserPassesTestMixin to validate
        user's permissions on a view.

        It always returns `True` if the user is a superuser (superuser can do
        everything in the platform); otherwise it returns the value of
        `has_permission`.
        """
        user = self.request.user
        if not user.is_anonymous and user.is_superuser:
            return True

        return self.has_permission()


class OrganizationPermissionMixin(PermissionRequiredMixin):
    """
    Mixin that provides the user's permissions for within organization.
    """
    org_slug = 'slug'

    def get_perms(self):
        if self.request.user.is_anonymous():
            # The user is not authenticated.
            group = Group.objects.get(name='AnonymousUser')
            return group.permissions.values_list('codename', flat=True)

        org = Organization.objects.get(slug=self.kwargs[self.org_slug])
        try:
            # The user is member of the organization.
            role = OrganizationRole.objects.get(organization=org,
                                                user=self.request.user)
            return role.group.permissions.values_list('codename', flat=True)
        except OrganizationRole.DoesNotExist:
            # The user is authenticated but not member of the organization.
            group = Group.objects.get(name='PublicUser')
            return group.permissions.values_list('codename', flat=True)
