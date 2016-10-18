from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from core.views.generic import UpdateView

from allauth.account.views import ConfirmEmailView, LoginView
from allauth.account.utils import send_email_confirmation

from ..models import User
from ..forms import ProfileForm


class AccountProfile(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('account:profile')

    def get_object(self, *args, **kwargs):
        return self.request.user

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs['request'] = self.request
        return form_kwargs

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS,
                             _("Successfully updated profile information"))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR,
                             _("Failed to update profile information"))
        return super().form_invalid(form)


class AccountLogin(LoginView):
    def form_valid(self, form):
        user = form.user
        if not user.email_verified and timezone.now() > user.verify_email_by:
            user.is_active = False
            user.save()
            send_email_confirmation(self.request, user)

        return super().form_valid(form)


class ConfirmEmail(ConfirmEmailView):
    def post(self, *args, **kwargs):
        response = super().post(*args, **kwargs)

        user = self.get_object().email_address.user
        user.email_verified = True
        user.is_active = True
        user.save()

        return response
