from django.core.urlresolvers import reverse_lazy
from django.views.generic import UpdateView

from django.contrib.auth.mixins import LoginRequiredMixin

from ..models import User
from ..forms import ProfileForm


class AccountProfile(LoginRequiredMixin, UpdateView):
    model = User
    form_class = ProfileForm
    template_name = 'profile.html'
    success_url = reverse_lazy('account:profile')

    def get_object(self, *args, **kwargs):
        return self.request.user
