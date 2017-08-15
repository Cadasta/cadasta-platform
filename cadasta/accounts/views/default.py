from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone

from core.views.generic import UpdateView, ListView
from core.views.mixins import SuperUserCheckMixin

import allauth.account.views as allauth_views
from allauth.account.views import ConfirmEmailView, LoginView
from allauth.account.utils import send_email_confirmation
from allauth.account.models import EmailAddress

from ..models import User
from .. import forms
from organization.models import ProjectRole


class PasswordChangeView(LoginRequiredMixin,
                         SuperUserCheckMixin,
                         allauth_views.PasswordChangeView):
    success_url = reverse_lazy('account:profile')
    form_class = forms.ChangePasswordForm


class PasswordResetView(SuperUserCheckMixin,
                        allauth_views.PasswordResetView):
    form_class = forms.ResetPasswordForm


class PasswordResetFromKeyView(SuperUserCheckMixin,
                               allauth_views.PasswordResetFromKeyView):
    form_class = forms.ResetPasswordKeyForm


class AccountProfile(LoginRequiredMixin, UpdateView):
    model = User
    form_class = forms.ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('account:profile')

    def get_object(self, *args, **kwargs):
        return self.request.user

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        emails_to_verify = EmailAddress.objects.filter(
            user=self.object, verified=False).exists()
        context['emails_to_verify'] = emails_to_verify
        return context

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
        user.email = self.get_object().email_address.email
        user.email_verified = True
        user.is_active = True
        user.save()

        return response


class AccountListProjects(ListView):
    model = User
    template_name = 'accounts/user_dashboard.html'

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)
        context['user_orgs_and_projects'] = list(self._get_orgs(user))
        return context

    @staticmethod
    def _get_orgs(user):
        orgs_by_name = user.organizations.order_by('name').all()
        for org in orgs_by_name:
            is_admin = user.organizationrole_set.get(organization=org).admin
            if is_admin:
                projects = list(
                    AccountListProjects._get_all_projects(org))
                yield (org, is_admin, projects)

            elif not org.archived:
                projects = list(
                    AccountListProjects._get_unarchived_projects(org, user))
                yield (org, is_admin, projects)

    @staticmethod
    def _get_unarchived_projects(org, user):
        unarchived_projects = org.all_projects().filter(archived=False)
        for proj in unarchived_projects:
            try:
                role_object = user.projectrole_set.get(project=proj)
            except ProjectRole.DoesNotExist:
                role = _('Public User')
            else:
                role = role_object.role_verbose
            yield (proj, role)

    @staticmethod
    def _get_all_projects(org):
        role = _('Administrator')
        for proj in org.all_projects():
            yield (proj, role)
