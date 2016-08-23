from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.utils.translation import gettext as _

from tutelary import mixins


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
                not self.request.user.is_anonymous()):

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


class LoginPermissionRequiredMixin(PermissionRequiredMixin,
                                   mixins.LoginPermissionRequiredMixin):
    pass


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
