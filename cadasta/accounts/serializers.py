from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.contrib.auth.password_validation import validate_password

from rest_framework.serializers import ChoiceField, EmailField, ValidationError
from rest_framework.validators import UniqueValidator
from djoser import serializers as djoser_serializers

from core.serializers import SanitizeFieldSerializer
from .models import User
from .validators import check_username_case_insensitive
from .exceptions import EmailNotVerifiedError


class RegistrationSerializer(SanitizeFieldSerializer,
                             djoser_serializers.UserRegistrationSerializer):
    email = EmailField(
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message=_("Another user is already registered with this "
                      "email address")
        )]
    )

    class Meta:
        model = User
        fields = (
            'username',
            'full_name',
            'email',
            'password',
            'email_verified',
            'language',
            'measurement',
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True, 'unique': True}
        }

    def validate_username(self, username):
        check_username_case_insensitive(username)
        if username.lower() in settings.CADASTA_INVALID_ENTITY_NAMES:
            raise ValidationError(
                _('Username cannot be “add” or “new”.'))
        return username

    def validate_password(self, password):
        validate_password(password)

        errors = []
        if self.initial_data.get('email'):
            email = self.initial_data.get('email').split('@')
            if len(email[0]) and email[0].casefold() in password.casefold():
                errors.append(_("Passwords cannot contain your email."))

        username = self.initial_data.get('username')
        if len(username) and username.casefold() in password.casefold():
            errors.append(
                _("The password is too similar to the username."))

        if errors:
            raise ValidationError(errors)

        return password


class UserSerializer(SanitizeFieldSerializer,
                     djoser_serializers.UserSerializer):
    email = EmailField(
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message=_("Another user is already registered with this "
                      "email address")
        )]
    )
    language = ChoiceField(
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
        error_messages={
            'invalid_choice': _('Language invalid or not available')
        }
    )
    measurement = ChoiceField(
        choices=settings.MEASUREMENTS,
        default=settings.MEASUREMENT_DEFAULT,
        error_messages={
            'invalid_choice': _('Measurement system invalid or not available')
        }
    )

    class Meta:
        model = User
        fields = (
            'username',
            'full_name',
            'email',
            'email_verified',
            'last_login',
            'language',
            'measurement',
        )
        extra_kwargs = {
            'email': {'required': True, 'unique': True},
            'email_verified': {'read_only': True}
        }

    def validate_username(self, username):
        instance = self.instance
        if instance is not None:
            if (username is not None and
                username != instance.username and
                    self.context['request'].user != instance):
                raise ValidationError('Cannot update username')
            if instance.username.casefold() != username.casefold():
                check_username_case_insensitive(username)
        if username.lower() in settings.CADASTA_INVALID_ENTITY_NAMES:
            raise ValidationError(
                _('Username cannot be “add” or “new”.'))
        return username

    def validate_last_login(self, last_login):
        instance = self.instance
        if instance is not None:
            if (last_login is not None and
                    last_login != instance.last_login):
                raise ValidationError(_('Cannot update last_login'))
        return last_login


class AccountLoginSerializer(djoser_serializers.LoginSerializer):
    def validate(self, attrs):
        attrs = super(AccountLoginSerializer, self).validate(attrs)

        if (not self.user.email_verified and
                timezone.now() > self.user.verify_email_by):
            raise EmailNotVerifiedError

        return attrs


class ChangePasswordSerializer(djoser_serializers.SetPasswordRetypeSerializer):
    def validate(self, attrs):

        if not self.context['request'].user.change_pw:
            raise ValidationError(_("The password for this user can not "
                                    "be changed."))
        return super().validate(attrs)

    def validate_new_password(self, password):
        user = self.context['request'].user
        validate_password(password, user=user)

        username = user.username
        if len(username) and username.casefold() in password.casefold():
            raise ValidationError(
                _("The password is too similar to the username."))

        return password
