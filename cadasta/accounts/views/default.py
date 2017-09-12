from itertools import groupby
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
from organization.models import Project


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
        all_active_user_orgs = set(user.organizations.order_by('name').all(
            ).exclude(archived=True))

        # projects for which user is org admin
        all_projects_user_is_org_admin = Project.objects.filter(
            organization__organizationrole__user=user,
            organization__organizationrole__admin=True
        )

        # projects for which user has a project role
        all_projects_where_user_has_projectrole = Project.objects.filter(
            organization__organizationrole__user=user,
            organization__organizationrole__admin=False,
            organization__archived=False,
            archived=False,
        ).exclude(projectrole__role__isnull=True
                  ).exclude(projectrole__role__exact='')

        # projects for which user is a project public user
        public_user_projects = Project.objects.filter(
            organization__users=user,
            organization__organizationrole__admin=False,
            projectrole__role__isnull=True,
            organization__archived=False,
            archived=False,
        ).prefetch_related('organization')

        is_admin__qs = (
            [True, False, all_projects_user_is_org_admin],
            [False, True, all_projects_where_user_has_projectrole],
            [False, False, public_user_projects]
        )

        for is_admin, pr_exist, qs in is_admin__qs:

            def get_org(proj): return proj.organization
            for org, projects in groupby(qs, get_org):

                if is_admin:
                    admin_role = _('Administrator')
                    yield (
                        org, is_admin,
                        [(proj, admin_role) for proj in projects]
                    )
                elif pr_exist:
                    yield (
                        org, is_admin,
                        [(proj, user.projectrole_set.get(
                            project=proj).role_verbose)
                            for proj in projects]
                    )
                else:
                    yield (
                        org, is_admin,
                        [(pr, _('Public User')) for pr in projects]
                    )
                all_active_user_orgs.discard(org)

        if len(all_active_user_orgs) != 0:
            for org in all_active_user_orgs:
                yield (org, user.organizationrole_set.get(
                    organization=org).admin, [])
