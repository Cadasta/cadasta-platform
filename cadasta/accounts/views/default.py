from itertools import groupby
from collections import defaultdict
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
        groupped_orgs = defaultdict(list)

        for org, is_admin, projects in self._get_orgs(user):
            groupped_orgs[(org, is_admin)].extend(projects)

        result = [(org, is_admin, projects)
                  for ((org, is_admin), projects) in groupped_orgs.items()]

        context['user_orgs_and_projects'] = result
        return context

    @staticmethod
    def _get_orgs(user):
        # Handle Projects without in-db ProjectRoles

        # 1st call: projects for which user is org admin (including archived
        # projects and archived orgs)
        org_admin_project = Project.objects.filter(
            organization__organizationrole__user=user,
            organization__organizationrole__admin=True
        )

        public_user_projects = set()

        # 2nd call: organizations where user is a member and not admin
        user_orgs_not_admin = user.organizations.filter(
            organizationrole__user=user,
            organizationrole__admin=False,
            archived=False,
        ).prefetch_related('projects').all()

        # 3rd call: projects linked to the user
        user_projects = user.project_set.all()
        for org in user_orgs_not_admin:
            for project in org.projects.all():
                if not project.archived and project not in user_projects:
                    public_user_projects.add(project)

        is_admin__qs = (
            [True, org_admin_project],
            [False, public_user_projects]
        )
        for is_admin, qs in is_admin__qs:

            def get_org(proj):
                return proj.organization

            for org, projects in groupby(qs, get_org):
                role = _('Administrator') if is_admin else _('Public User')
                yield (
                    org, is_admin, [(proj, role) for proj in projects]
                )

        # 4rd call: Projects with in-db ProjectRoles
        proj_roles = user.projectrole_set.filter(
            project__organization__organizationrole__admin=False,
            project__organization__organizationrole__user=user,
            project__organization__archived=False,
            project__archived=False,
        )
        proj_roles = proj_roles.prefetch_related('project')
        proj_roles = proj_roles.prefetch_related('project__organization')

        def get_org(pr):
            return pr.project.organization

        for org, project_roles in groupby(proj_roles, get_org):
            yield (
                org, False,
                [(role.project, role.role_verbose) for role in project_roles]
            )

        # 5th call: Orgs without Projects
        qs = user.organizationrole_set.filter(organization__projects=None)
        qs = qs.exclude(organization__archived=True, admin=False)
        qs = qs.prefetch_related('organization')
        for org_role in qs:
            yield (org_role.organization, org_role.admin, [])
