from django.contrib import messages
from django.shortcuts import redirect

import tutelary.mixins


class PermissionRequiredMixin(tutelary.mixins.PermissionRequiredMixin):
    def handle_no_permission(self):
        msg = super().handle_no_permission()
        messages.add_message(self.request, messages.WARNING,
                             msg[0] if len(msg) > 0 else "PERMISSION DEFINED")
        return redirect(self.request.META.get('HTTP_REFERER', '/'))
