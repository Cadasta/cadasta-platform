from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext as _

from tutelary import mixins


class PermissionRequiredMixin(mixins.PermissionRequiredMixin):
    def handle_no_permission(self):
        msg = super().handle_no_permission()
        messages.add_message(self.request, messages.WARNING,
                             msg[0] if len(msg) > 0 and len(msg[0]) > 0
                             else _("PERMISSION DENIED"))
        return redirect(self.request.META.get('HTTP_REFERER', '/'))


class LoginPermissionRequiredMixin(PermissionRequiredMixin,
                                   mixins.LoginPermissionRequiredMixin):
    pass
