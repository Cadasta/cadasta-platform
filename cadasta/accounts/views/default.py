from django.core.urlresolvers import reverse_lazy
from django.views.generic import UpdateView

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

from ..models import User
from ..forms import ProfileForm


class AccountProfile(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('account:profile')

    def get_object(self, *args, **kwargs):
        return self.request.user

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS,
                             "Successfully updated profile information")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR,
                             "Failed to update profile information")
        return super().form_invalid(form)
