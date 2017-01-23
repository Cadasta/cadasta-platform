from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.contrib.auth.password_validation import validate_password

from rest_framework.serializers import EmailField, ValidationError
from rest_framework.validators import UniqueValidator
from djoser import serializers as djoser_serializers

from .models import User
from .exceptions import EmailNotVerifiedError


class RegistrationSerializer(djoser_serializers.UserRegistrationSerializer):
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
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True, 'unique': True}
        }

    def validate_username(self, username):
        if username.lower() in settings.CADASTA_INVALID_ENTITY_NAMES:
            raise ValidationError(
                _("Username cannot be “add” or “new”."))
        return username

    def validate_password(self, password):
        validate_password(password)

        errors = []
        if self.initial_data.get('email'):
            email = self.initial_data.get('email').lower().split('@')
            if email[0] in password:
                errors.append(_("Passwords cannot contain your email."))

        if self.initial_data.get('username') in password:
            errors.append(
                _("The password is too similar to the username."))

        if errors:
            raise ValidationError(errors)

        return password


class UserSerializer(djoser_serializers.UserSerializer):
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
            'email_verified',
            'last_login',
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
        if username.lower() in settings.CADASTA_INVALID_ENTITY_NAMES:
            raise ValidationError(
                _("Username cannot be “add” or “new”."))
        return username

    def validate_last_login(self, last_login):
        instance = self.instance
        if instance is not None:
            if (last_login is not None and
               last_login != instance.last_login):
                raise ValidationError('Cannot update last_login')
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
