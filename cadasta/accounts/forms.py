from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _
from django.contrib.auth.password_validation import validate_password
from allauth.account.utils import send_email_confirmation
from allauth.account import forms as allauth_forms

from core.form_mixins import SanitizeFieldsForm
from .utils import send_email_update_notification
from .models import User
from .validators import check_username_case_insensitive
from parsley.decorators import parsleyfy


@parsleyfy
class RegisterForm(SanitizeFieldsForm, forms.ModelForm):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput())
    MIN_LENGTH = 10

    class Meta:
        model = User
        fields = ['username', 'email', 'password',
                  'full_name']

    class Media:
        js = ('js/sanitize.js', )

    def clean_username(self):
        username = self.data.get('username')
        check_username_case_insensitive(username)
        if username.lower() in settings.CADASTA_INVALID_ENTITY_NAMES:
            raise forms.ValidationError(
                _("Username cannot be “add” or “new”."))
        return username

    def clean_password(self):
        password = self.data.get('password')
        validate_password(password)
        errors = []

        email = self.data.get('email').split('@')
        if len(email[0]) and email[0].casefold() in password.casefold():
            errors.append(_("Passwords cannot contain your email."))

        username = self.data.get('username')
        if len(username) and username.casefold() in password.casefold():
            errors.append(
                _("The password is too similar to the username."))

        if errors:
            raise forms.ValidationError(errors)

        return password

    def clean_email(self):
        email = self.data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                _("Another user with this email already exists"))
        return email

    def save(self, *args, **kwargs):
        user = super().save(*args, **kwargs)
        user.set_password(self.cleaned_data['password'])
        user.save()
        return user


class ProfileForm(SanitizeFieldsForm, forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    language = forms.ChoiceField(
        choices=settings.LANGUAGES,
        error_messages={
            'invalid_choice': _('Language invalid or not available')
        }
    )
    measurement = forms.ChoiceField(
        choices=settings.MEASUREMENTS,
        error_messages={
            'invalid_choice': _('Measurement system invalid or not available')
        }
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'full_name', 'language',
                  'measurement']

    class Media:
        js = ('js/sanitize.js', )

    def __init__(self, *args, **kwargs):
        self._send_confirmation = False
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.current_email = self.instance.email

    def clean_username(self):
        username = self.data.get('username')
        if self.instance.username.casefold() != username.casefold():
            check_username_case_insensitive(username)
        if username.lower() in settings.CADASTA_INVALID_ENTITY_NAMES:
            raise forms.ValidationError(
                _("Username cannot be “add” or “new”."))
        return username

    def clean_password(self):
        if (self.fields['password'].required and
                not self.instance.check_password(self.data.get('password'))):
            raise forms.ValidationError(
                _("Please provide the correct password for your account."))

    def clean_email(self):
        email = self.data.get('email')
        if self.instance.email != email:
            if User.objects.filter(email=email).exists():
                raise forms.ValidationError(
                    _("Another user with this email already exists"))

        return email

    def save(self, *args, **kwargs):
        user = super().save(commit=False, *args, **kwargs)
        if self.current_email != user.email:
            current_email_set = self.instance.emailaddress_set.all()
            if current_email_set.exists():
                current_email_set.delete()

            send_email_confirmation(self.request, user)
            send_email_update_notification(self.current_email)
            user.email = self.current_email

        user.save()
        return user


class ChangePasswordMixin:
    def clean_password(self):
        if not self.user.change_pw:
            raise forms.ValidationError(_("The password for this user can not "
                                          "be changed."))

        password = self.cleaned_data['password']
        validate_password(password, user=self.user)

        username = self.user.username
        if len(username) and username.casefold() in password.casefold():
            raise forms.ValidationError(
                _("The password is too similar to the username."))

        return password

    def save(self):
        allauth_forms.get_adapter().set_password(
            self.user, self.cleaned_data['password'])


class ChangePasswordForm(ChangePasswordMixin,
                         allauth_forms.UserForm):

    oldpassword = allauth_forms.PasswordField(label=_("Current Password"))
    password = allauth_forms.SetPasswordField(label=_("New Password"))

    def clean_oldpassword(self):
        if not self.user.check_password(self.cleaned_data.get('oldpassword')):
            raise forms.ValidationError(_("Please type your current"
                                          " password."))
        return self.cleaned_data['oldpassword']


class ResetPasswordKeyForm(ChangePasswordMixin,
                           forms.Form):

    password = allauth_forms.SetPasswordField(label=_("New Password"))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.temp_key = kwargs.pop('temp_key', None)
        super().__init__(*args, **kwargs)


class ResetPasswordForm(allauth_forms.ResetPasswordForm):
    def clean_email(self):
        email = self.cleaned_data.get('email')
        self.users = User.objects.filter(email=email)
        return email
