from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _
from django.contrib.auth.password_validation import validate_password

from allauth.account.utils import send_email_confirmation
from allauth.account import forms as allauth_forms
from allauth.account.models import EmailAddress

from core.form_mixins import SanitizeFieldsForm
from . import utils
from .models import User, VerificationDevice
from .validators import check_username_case_insensitive, phone_validator
from . import messages

from parsley.decorators import parsleyfy
from phonenumbers import parse as parse_phone


@parsleyfy
class RegisterForm(SanitizeFieldsForm, forms.ModelForm):
    email = forms.EmailField(required=False)

    phone = forms.RegexField(regex=r'^\+[0-9]{5,14}$',
                             error_messages={'invalid': messages.phone_format},
                             required=False)
    password = forms.CharField(widget=forms.PasswordInput())
    MIN_LENGTH = 10

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'password',
                  'full_name', 'language']

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

        email = self.data.get('email')
        if email:
            email = email.split('@')
            if email[0].casefold() in password.casefold():
                errors.append(_("Passwords cannot contain your email."))

        username = self.data.get('username')
        if len(username) and username.casefold() in password.casefold():
            errors.append(
                _("The password is too similar to the username."))

        phone = self.data.get('phone')
        if phone and phone_validator(phone):
            phone = str(parse_phone(phone).national_number)
            if phone in password:
                errors.append(_("Passwords cannot contain your phone."))

        if errors:
            raise forms.ValidationError(errors)

        return password

    def clean_email(self):
        email = self.data.get('email')
        if email:
            email = email.casefold()
            if EmailAddress.objects.filter(email=email).exists():
                raise forms.ValidationError(
                    _("User with this Email address already exists."))
        else:
            email = None
        return email

    def clean_phone(self):
        phone = self.data.get('phone')
        if phone:
            if VerificationDevice.objects.filter(
                    unverified_phone=phone).exists():
                raise forms.ValidationError(
                    _("User with this Phone number already exists."))
        else:
            phone = None
        return phone

    def save(self, *args, **kwargs):
        user = super().save(*args, **kwargs)
        user.set_password(self.cleaned_data['password'])
        user.save()
        return user


class ProfileForm(SanitizeFieldsForm, forms.ModelForm):
    email = forms.EmailField(required=False)

    phone = forms.RegexField(regex=r'^\+[0-9]{5,14}$',
                             error_messages={'invalid': messages.phone_format},
                             required=False)
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'full_name', 'language',
                  'measurement', 'avatar']

    class Media:
        js = ('js/image-upload.js', 'js/sanitize.js', )

    def __init__(self, *args, **kwargs):
        self._send_confirmation = False
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.current_email = self.instance.email
        self.current_phone = self.instance.phone

    def clean(self):
        super(ProfileForm, self).clean()
        email = self.data.get('email')
        phone = self.data.get('phone')

        if not phone and not email:
            raise forms.ValidationError(
                _("You cannot leave both phone and email empty."))

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

    def clean_phone(self):
        phone = self.data.get('phone')
        if phone:
            if (phone != self.current_phone and
                VerificationDevice.objects.filter(unverified_phone=phone
                                                  ).exists()):
                raise forms.ValidationError(
                    _("User with this Phone number already exists."))
        else:
            phone = None
        return phone

    def clean_email(self):
        email = self.data.get('email')
        if email:
            email = email.casefold()
            if (email != self.current_email and
                    EmailAddress.objects.filter(email=email).exists()):
                raise forms.ValidationError(
                    _("User with this Email address already exists."))
        else:
            email = None

        return email

    def save(self, *args, **kwargs):
        user = super().save(commit=False, *args, **kwargs)
        email_update_message = None

        if self.current_email != user.email:
            current_email_set = self.instance.emailaddress_set.all()
            if current_email_set.exists():
                current_email_set.delete()

            if user.email:
                send_email_confirmation(self.request, user)
                email_update_message = messages.email_change

                if self.current_email:
                    utils.send_email_update_notification(self.current_email)
                    user.email = self.current_email
            else:
                user.email_verified = False
                email_update_message = messages.email_delete
                utils.send_email_deleted_notification(self.current_email)

        if self.current_phone != user.phone:
            current_phone_set = VerificationDevice.objects.filter(
                user=self.instance)
            if current_phone_set.exists():
                current_phone_set.delete()

            if user.phone:
                device = VerificationDevice.objects.create(
                    user=self.instance, unverified_phone=user.phone)
                device.generate_challenge()
                if self.current_phone:
                    utils.send_sms(self.current_phone, messages.phone_change)
                    user.phone = self.current_phone
                if user.email:
                    utils.send_phone_update_notification(user.email)
            else:
                user.phone_verified = False
                utils.send_sms(self.current_phone, messages.phone_delete)
                if user.email:
                    utils.send_phone_deleted_notification(user.email)

        if user.phone and email_update_message:
            utils.send_sms(user.phone, email_update_message)
        user.save()
        return user


class ChangePasswordMixin:

    def clean_password(self):
        if not self.user or not self.user.change_pw:
            raise forms.ValidationError(_("The password for this user can not "
                                          "be changed."))

        password = self.cleaned_data['password']
        validate_password(password, user=self.user)

        username = self.user.username
        if len(username) and username.casefold() in password.casefold():
            raise forms.ValidationError(
                _("The password is too similar to the username."))

        phone = self.user.phone
        if phone and phone_validator(phone):
            phone = str(parse_phone(phone).national_number)
            if phone in password:
                raise forms.ValidationError(
                    _("Passwords cannot contain your phone."))
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
    email = forms.EmailField(required=False)

    phone = forms.RegexField(regex=r'^\+[0-9]{5,14}$',
                             error_messages={'invalid': messages.phone_format},
                             required=False)

    def clean(self):
        if not self.data.get('email') and not self.data.get('phone'):
            raise forms.ValidationError(_(
                "You cannot leave both phone and email empty."))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email = email.casefold()
            self.users = User.objects.filter(email=email)
        else:
            email = None
        return email

    def clean_phone(self):
        phone = self.data.get('phone')
        if not phone:
            phone = None
        return phone

    def save(self, request, **kwargs):
        phone = self.data.get('phone')
        if phone:
            request.session['phone'] = phone
            try:
                user = User.objects.get(phone=phone)
                device = user.verificationdevice_set.get_or_create(
                    unverified_phone=phone, label='password_reset')
                device[0].generate_challenge()
            except User.DoesNotExist:
                pass
            return phone
        else:
            super().save(request, **kwargs)


class TokenVerificationForm(forms.Form):
    token = forms.CharField(label=_("Token"), max_length=settings.TOTP_DIGITS)

    def __init__(self, *args, **kwargs):
        self.device = kwargs.pop('device', None)
        super().__init__(*args, **kwargs)

    def clean_token(self):
        token = self.data.get('token')
        device = self.device
        if not device:
            raise forms.ValidationError(
                _("The token could not be verified."
                    " Please click on 'here' to try again."))
        try:
            token = int(token)
        except ValueError:
            raise forms.ValidationError(_("Token must be a number."))

        if device.verify_token(token):
            return token
        elif device.verify_token(token=token, tolerance=5):
            raise forms.ValidationError(
                _("The token has expired."
                  " Please click on 'here' to receive the new token."))
        else:
            raise forms.ValidationError(
                "Invalid Token. Enter a valid token.")


class ResendTokenForm(forms.Form):
    email = forms.EmailField(required=False)

    phone = forms.RegexField(regex=r'^\+[0-9]{5,14}$',
                             error_messages={'invalid': messages.phone_format},
                             required=False)
