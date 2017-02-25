from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from allauth.account.utils import send_email_confirmation
from allauth.account import forms as allauth_forms

from .models import User, now_plus_48_hours
from parsley.decorators import parsleyfy


@parsleyfy
class RegisterForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())
    MIN_LENGTH = 10

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2',
                  'full_name']

    def clean_username(self):
        username = self.data.get('username')
        if username.lower() in settings.CADASTA_INVALID_ENTITY_NAMES:
            raise forms.ValidationError(
                _("Username cannot be “add” or “new”."))
        return username

    def clean_password1(self):
        password = self.data.get('password1')
        validate_password(password)
        errors = []

        if password != self.data.get('password2'):
            raise forms.ValidationError(_("Passwords do not match"))

        email = self.data.get('email').lower().split('@')
        if email[0] in password:
            errors.append(_("Passwords cannot contain your email."))

        if self.data.get('username') in password:
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
        user = super(RegisterForm, self).save(*args, **kwargs)
        user.set_password(self.cleaned_data['password1'])
        user.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'full_name']

    def __init__(self, *args, **kwargs):
        self._send_confirmation = False
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.data.get('username')
        if (self.instance.username != username and
                User.objects.filter(username=username).exists()):
            raise forms.ValidationError(
                _("Another user with this username already exists"))
        if username.lower() in settings.CADASTA_INVALID_ENTITY_NAMES:
            raise forms.ValidationError(
                _("Username cannot be “add” or “new”."))
        return username

    def clean_email(self):
        email = self.data.get('email')
        if self.instance.email != email:
            self._send_confirmation = True

            if User.objects.filter(email=email).exists():
                raise forms.ValidationError(
                    _("Another user with this email already exists"))
        return email

    def save(self, *args, **kwargs):
        user = super().save(commit=False, *args, **kwargs)

        if self._send_confirmation:
            send_email_confirmation(self.request, user)
            self._send_confirmation = False
            user.email_verified = False
            user.verify_email_by = now_plus_48_hours()

        user.save()
        return user


class ChangePasswordMixin:
    def clean_password1(self):
        if not self.user.change_pw:
            raise forms.ValidationError(_("The password for this user can not "
                                          "be changed."))

        password = self.cleaned_data['password1']
        validate_password(password, user=self.user)
        send_mail('Subject here','Password has changed','from@example.com',["adasd"],fail_silently=False,)
        return password


class ChangePasswordForm(ChangePasswordMixin,
                         allauth_forms.ChangePasswordForm):
    pass


class ResetPasswordKeyForm(ChangePasswordMixin,
                           allauth_forms.ResetPasswordKeyForm):
    pass
