from collections import defaultdict
from itertools import groupby
import operator as op

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.utils import translation
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.api import get_messages
from django.views.generic import FormView
from django.shortcuts import redirect
from django.utils.html import format_html

from core.views.generic import UpdateView, ListView, CreateView
from core.views.mixins import SuperUserCheckMixin

import allauth.account.views as allauth_views
from allauth.account.views import ConfirmEmailView, LoginView
from allauth.account.utils import send_email_confirmation
from allauth.account.models import EmailAddress
from allauth.account import signals

from ..models import User, VerificationDevice
from .. import forms
from organization.models import Project
from ..messages import account_inactive, unverified_identifier


class AccountRegister(CreateView):
    model = User
    form_class = forms.RegisterForm
    template_name = 'account/signup.html'
    success_url = reverse_lazy('account:verify_phone')

    def form_valid(self, form):
        user = form.save(self.request)

        user_lang = form.cleaned_data['language']
        if user_lang != translation.get_language():
            translation.activate(user_lang)
            self.request.session[translation.LANGUAGE_SESSION_KEY] = user_lang

        if user.email:
            send_email_confirmation(self.request, user)

        if user.phone:
            device = VerificationDevice.objects.create(
                user=user, unverified_phone=user.phone)
            device.generate_challenge()
            message = _("Verification token sent to {phone}")
            message = message.format(phone=user.phone)
            messages.add_message(self.request, messages.INFO, message)

        self.request.session['phone_verify_id'] = user.id

        message = _("We have created your account. You should have"
                    " received an email or a text to verify your account.")
        messages.add_message(self.request, messages.SUCCESS, message)

        return super().form_valid(form)


class PasswordChangeView(LoginRequiredMixin,
                         SuperUserCheckMixin,
                         allauth_views.PasswordChangeView):
    success_url = reverse_lazy('account:profile')
    form_class = forms.ChangePasswordForm


class PasswordResetView(SuperUserCheckMixin,
                        allauth_views.PasswordResetView):
    form_class = forms.ResetPasswordForm


class PasswordResetDoneView(FormView, allauth_views.PasswordResetDoneView):
    """ If the user opts to reset password with phone, this view will display
     a form to verify the password reset token. """
    form_class = forms.TokenVerificationForm
    success_url = reverse_lazy('account:account_reset_password_from_phone')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['phone'] = self.request.session.get('phone', None)
        return context

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        phone = self.request.session.get('phone', None)
        try:
            form_kwargs['device'] = VerificationDevice.objects.get(
                unverified_phone=phone, label='password_reset')
        except VerificationDevice.DoesNotExist:
            pass
        return form_kwargs

    def form_valid(self, form):
        device = form.device
        message = _("Successfully Verified Token."
                    " You can now reset your password.")
        messages.add_message(self.request, messages.SUCCESS, message)
        self.request.session.pop('phone', None)
        self.request.session['password_reset_id'] = device.user_id
        device.delete()
        return super().form_valid(form)


class PasswordResetFromKeyView(SuperUserCheckMixin,
                               allauth_views.PasswordResetFromKeyView):
    form_class = forms.ResetPasswordKeyForm


class PasswordResetFromPhoneView(FormView, SuperUserCheckMixin):
    """ This view will allow user to reset password once a user has
     successfully verified the password reset token. """
    form_class = forms.ResetPasswordKeyForm
    template_name = 'account/password_reset_from_key.html'
    success_url = reverse_lazy("account:account_reset_password_from_key_done")

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        try:
            user_id = self.request.session['password_reset_id']
            user = User.objects.get(id=user_id)
            form_kwargs['user'] = user
        except KeyError:
            message = _(
                "You must first verify your token before resetting password."
                " Click <a href='{url}'>here</a> to get the password reset"
                " verification token. ")
            message = format_html(message.format(
                url=reverse_lazy('account:account_reset_password')))
            messages.add_message(self.request, messages.ERROR, message)

        return form_kwargs

    def form_valid(self, form):
        form.save()
        self.request.session.pop('password_reset_id', None)
        signals.password_reset.send(sender=form.user.__class__,
                                    request=self.request,
                                    user=form.user)
        return super().form_valid(form)


class AccountProfile(LoginRequiredMixin, UpdateView):
    model = User
    form_class = forms.ProfileForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('account:dashboard')

    def get_object(self, *args, **kwargs):
        self.instance_phone = self.request.user.phone
        return self.request.user

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        emails_to_verify = EmailAddress.objects.filter(
            user=self.object, verified=False).exists()
        phones_to_verify = VerificationDevice.objects.filter(
            user=self.object, verified=False).exists()

        context['emails_to_verify'] = emails_to_verify
        context['phones_to_verify'] = phones_to_verify
        return context

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        form_kwargs['request'] = self.request
        return form_kwargs

    def form_valid(self, form):
        phone = form.data.get('phone')
        messages.add_message(self.request, messages.SUCCESS,
                             _("Successfully updated profile information"))

        if (phone != self.instance_phone and phone):
            message = _("Verification Token sent to {phone}")
            message = message.format(phone=phone)
            messages.add_message(self.request, messages.INFO, message)
            self.request.session['phone_verify_id'] = self.object.id
            self.success_url = reverse_lazy('account:verify_phone')

        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR,
                             _("Failed to update profile information"))
        return super().form_invalid(form)


class AccountLogin(LoginView):
    success_url = reverse_lazy('account:dashboard')

    def form_valid(self, form):
        login = form.cleaned_data['login']
        user = form.user

        if (login == user.username and
                not user.phone_verified and
                not user.email_verified):
            user.is_active = False
            user.save()
            messages.add_message(
                self.request, messages.ERROR, account_inactive)
            return redirect(reverse_lazy('account:resend_token'))

        if(login == user.email and not user.email_verified or
                login == user.phone and not user.phone_verified):
            messages.add_message(
                self.request, messages.ERROR, unverified_identifier)
            return redirect(reverse_lazy('account:resend_token'))
        else:
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


class UserDashboard(LoginRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_dashboard.html'

    def get_context_data(self, **kwargs):
        user = self.request.user
        context = super().get_context_data(**kwargs)

        # Group by org and admin status
        grouped_orgs = defaultdict(list)
        for org, is_admin, projects in self._get_orgs(user):
            grouped_orgs[(org, is_admin)].extend(projects)

        # Flatten data
        result = [(org, is_admin, projects)
                  for (org, is_admin), projects
                  in grouped_orgs.items()]

        # Sort data alphabetically
        def get_name(items): return items[0].name
        context['user_orgs_and_projects'] = sorted(result, key=get_name)
        return context

    @staticmethod
    def _get_orgs(user):
        # Projects for which user is org admin (including archived projects and
        # archived orgs)
        org_admin_project = Project.objects.filter(
            organization__organizationrole__user=user,
            organization__organizationrole__admin=True
        )

        # Projects for which user is not an org admin, neither project nor org
        # are archived, and user not directly associated with project (i.e.
        # user has no project role)
        public_user_projects = Project.objects.filter(
            organization__organizationrole__user=user,
            organization__organizationrole__admin=False,
            organization__archived=False,
            archived=False,
        ).exclude(users=user)

        is_admin__qs = (
            [True, org_admin_project],
            [False, public_user_projects]
        )
        for is_admin, qs in is_admin__qs:
            qs = qs.prefetch_related('organization')
            for org, projects in groupby(qs, op.attrgetter('organization')):
                role = _('Administrator') if is_admin else _('Public User')
                yield (
                    org, is_admin, [(proj, role) for proj in projects]
                )

        #  Projects with in-db ProjectRoles
        proj_roles = user.projectrole_set.filter(
            project__organization__organizationrole__admin=False,
            project__organization__organizationrole__user=user,
            project__organization__archived=False,
            project__archived=False,
        )
        proj_roles = proj_roles.prefetch_related('project')
        proj_roles = proj_roles.prefetch_related('project__organization')
        get_org = op.attrgetter('project.organization')
        for org, project_roles in groupby(proj_roles, get_org):
            yield (
                org, False,
                [(role.project, role.role_verbose) for role in project_roles]
            )

        # Orgs without Projects
        org_roles = user.organizationrole_set.filter(
            organization__projects=None,
            organization__archived=False
        ).prefetch_related('organization')
        for org_role in org_roles:
            yield (org_role.organization, org_role.admin, [])


class ConfirmPhone(FormView):
    template_name = 'accounts/account_verification.html'
    form_class = forms.TokenVerificationForm
    success_url = reverse_lazy('account:login')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        user_id = self.request.session.get('phone_verify_id', None)

        emails_to_verify = EmailAddress.objects.filter(
            user_id=user_id, verified=False).exists()
        phones_to_verify = VerificationDevice.objects.filter(
            user_id=user_id, label='phone_verify').exists()
        context['phone'] = phones_to_verify
        context['email'] = emails_to_verify

        return context

    def get_form_kwargs(self, *args, **kwargs):
        form_kwargs = super().get_form_kwargs(*args, **kwargs)
        user_id = self.request.session.get('phone_verify_id', None)
        try:
            form_kwargs['device'] = VerificationDevice.objects.get(
                user_id=user_id, label='phone_verify')
        except VerificationDevice.DoesNotExist:
            pass
        return form_kwargs

    def form_valid(self, form):
        device = form.device
        user = device.user
        if user.phone != device.unverified_phone:
            user.phone = device.unverified_phone
        user.phone_verified = True
        user.is_active = True
        user.save()
        device.delete()
        message = _("Successfully verified {phone}")
        message = message.format(phone=user.phone)
        messages.add_message(self.request, messages.SUCCESS, message)
        self.request.session.pop('phone_verify_id', None)
        return super().form_valid(form)


class ResendTokenView(FormView):
    form_class = forms.ResendTokenForm
    template_name = 'accounts/resend_token_page.html'
    success_url = reverse_lazy('account:verify_phone')

    def form_valid(self, form):
        phone = form.data.get('phone')
        email = form.data.get('email')
        if phone:
            try:
                phone_device = VerificationDevice.objects.get(
                    unverified_phone=phone, verified=False)
                phone_device.generate_challenge()
                self.request.session['phone_verify_id'] = phone_device.user_id
            except VerificationDevice.DoesNotExist:
                pass
            message = _(
                "Your phone number has been submitted."
                " If it matches your account on Cadasta Platform, you will"
                " receive a verification token to confirm your phone.")
            messages.add_message(self.request, messages.SUCCESS, message)

        if email:
            email = email.casefold()
            try:
                email_device = EmailAddress.objects.get(
                    email=email, verified=False)
                user = email_device.user
                if not user.email_verified:
                    user.email = email
                send_email_confirmation(self.request, user)
                self.request.session['phone_verify_id'] = email_device.user.id
            except EmailAddress.DoesNotExist:
                pass

            # This is a gross hack, removing all messages previously added to
            # the message queue so we don't reveal whether the email address
            # existed in the system or not. (See issue #1869)
            get_messages(self.request)._queued_messages = []

            message = _(
                "Your email address has been submitted."
                " If it matches your account on Cadasta Platform, you will"
                " receive a verification link to confirm your email.")
            messages.add_message(self.request, messages.SUCCESS, message)

        return super().form_valid(form)
