from buckets.serializers import S3Field
from django.conf import settings
from django.utils.translation import ugettext as _
from django.contrib.auth.password_validation import validate_password
from allauth.account.models import EmailAddress

from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from djoser import serializers as djoser_serializers
from phonenumbers import parse as parse_phone

from core.serializers import SanitizeFieldSerializer
from .models import User, VerificationDevice
from .validators import check_username_case_insensitive, phone_validator
from . import exceptions
from .messages import phone_format


class RegistrationSerializer(SanitizeFieldSerializer,
                             djoser_serializers.UserRegistrationSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message=_("User with this Email address already exists.")
        )],
        allow_blank=True,
        allow_null=True,
        required=False
    )
    phone = serializers.RegexField(
        regex=r'^\+(?:[0-9]?){6,14}[0-9]$',
        error_messages={'invalid': phone_format},
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message=_("User with this Phone number already exists.")
        )],
        allow_blank=True,
        allow_null=True,
        required=False
    )

    class Meta:
        model = User
        fields = (
            'username',
            'full_name',
            'email',
            'phone',
            'password',
            'language',
            'measurement',
            'avatar',
            'email_verified',
            'phone_verified'
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': False, 'unique': True,
                      'allow_null': True, 'allow_blank': True},
            'phone': {'required': False, 'unique': True,
                      'allow_null': True, 'allow_blank': True},
        }

    def validate(self, data):
        data = super(RegistrationSerializer, self).validate(data)

        email = self.initial_data.get('email')
        phone = self.initial_data.get('phone')
        if (not phone) and (not email):
            raise serializers.ValidationError(
                _("You cannot leave both phone and email empty."
                  " Signup with either phone or email or both."))
        return data

    def validate_email(self, email):
        if email:
            email = email.casefold()
            if EmailAddress.objects.filter(email=email).exists():
                raise serializers.ValidationError(
                    _("User with this Email address already exists."))
        else:
            email = None
        return email

    def validate_phone(self, phone):
        if phone:
            if VerificationDevice.objects.filter(
                    unverified_phone=phone).exists():
                raise serializers.ValidationError(
                    _("User with this Phone number already exists."))
        else:
            phone = None
        return phone

    def validate_username(self, username):
        check_username_case_insensitive(username)
        if username.lower() in settings.CADASTA_INVALID_ENTITY_NAMES:
            raise serializers.ValidationError(
                _('Username cannot be “add” or “new”.'))
        return username

    def validate_password(self, password):
        validate_password(password)

        errors = []
        email = self.initial_data.get('email')
        if email:
            email = email.split('@')
            if email[0].casefold() in password.casefold():
                errors.append(_("Passwords cannot contain your email."))

        username = self.initial_data.get('username')
        if len(username) and username.casefold() in password.casefold():
            errors.append(
                _("The password is too similar to the username."))

        phone = self.initial_data.get('phone')
        if phone:
            if phone_validator(phone):
                phone = str(parse_phone(phone).national_number)
                if phone in password:
                    errors.append(_("Passwords cannot contain your phone."))
        if errors:
            raise serializers.ValidationError(errors)

        return password


class UserSerializer(SanitizeFieldSerializer,
                     djoser_serializers.UserSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message=_("User with this Email address already exists.")
        )],
        allow_blank=True,
        allow_null=True,
        required=False

    )
    phone = serializers.RegexField(
        regex=r'^\+(?:[0-9]?){6,14}[0-9]$',
        error_messages={'invalid': phone_format},
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message=_("User with this Phone number already exists.")
        )],
        allow_blank=True,
        allow_null=True,
        required=False
    )
    avatar = S3Field(required=False)
    language = serializers.ChoiceField(
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
        error_messages={
            'invalid_choice': _('Language invalid or not available')
        }
    )
    measurement = serializers.ChoiceField(
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
            'phone',
            'last_login',
            'language',
            'measurement',
            'avatar',
            'email_verified',
            'phone_verified',
        )
        extra_kwargs = {
            'email': {'required': False, 'unique': True,
                      'allow_null': True, 'allow_blank': True},
            'phone': {'required': False, 'unique': True,
                      'allow_null': True, 'allow_blank': True},
            'email_verified': {'read_only': True},
            'phone_verified': {'read_only': True}
        }

    def validate(self, data):
        data = super(UserSerializer, self).validate(data)
        instance = self.instance
        if instance:
            email = self.initial_data.get('email', instance.email)
            phone = self.initial_data.get('phone', instance.phone)
            if (not phone) and (not email):
                raise serializers.ValidationError(
                    _("You cannot leave both phone and email empty."))
        return data

    def validate_email(self, email):
        instance = self.instance
        if (instance and email != instance.email and
                self.context['request'].user != instance):
            raise serializers.ValidationError(_("Cannot update email"))

        if instance and instance.email == email:
            return email

        if email:
            email = email.casefold()
            # make sure that the new email updated by a user is not a duplicate
            # of an unverified email already linked to a different user
            if EmailAddress.objects.filter(email=email).exists():
                raise serializers.ValidationError(
                    _("User with this Email address already exists."))
        else:
            email = None
        return email

    def validate_phone(self, phone):
        instance = self.instance
        if (instance and phone != instance.phone and
                self.context['request'].user != instance):
            raise serializers.ValidationError(_("Cannot update phone"))

        if instance and instance.phone == phone:
            return phone

        if phone:
            # make sure that the new phone updated by a user is not a duplicate
            # of an unverified phone already linked to a different user
            if VerificationDevice.objects.filter(
                    unverified_phone=phone).exists():
                raise serializers.ValidationError(
                    _("User with this Phone number already exists."))
        else:
            phone = None
        return phone

    def validate_username(self, username):
        instance = self.instance
        if instance is not None:
            if (username is not None and
                username != instance.username and
                    self.context['request'].user != instance):
                raise serializers.ValidationError('Cannot update username')
            if instance.username.casefold() != username.casefold():
                check_username_case_insensitive(username)
        if username.lower() in settings.CADASTA_INVALID_ENTITY_NAMES:
            raise serializers.ValidationError(
                _('Username cannot be “add” or “new”.'))
        return username

    def validate_last_login(self, last_login):
        instance = self.instance
        if instance is not None:
            if (last_login is not None and
                    last_login != instance.last_login):
                raise serializers.ValidationError(
                    _('Cannot update last_login'))
        return last_login


class AccountLoginSerializer(djoser_serializers.LoginSerializer):
    def validate(self, attrs):
        attrs = super(AccountLoginSerializer, self).validate(attrs)

        if ((attrs['username'] == self.user.username) and
                ((not self.user.email_verified) and
                    (not self.user.phone_verified))):
            raise exceptions.AccountInactiveError

        if (attrs['username'] == self.user.email and
                (not self.user.email_verified)):
            raise exceptions.EmailNotVerifiedError

        if (attrs['username'] == self.user.phone and
                (not self.user.phone_verified)):
            raise exceptions.PhoneNotVerifiedError

        return attrs


class ChangePasswordSerializer(djoser_serializers.SetPasswordRetypeSerializer):
    def validate(self, attrs):

        if not self.context['request'].user.change_pw:
            raise serializers.ValidationError(
                _("The password for this user can not be changed."))
        return super().validate(attrs)

    def validate_new_password(self, password):
        user = self.context['request'].user
        validate_password(password, user=user)

        username = user.username
        if len(username) and username.casefold() in password.casefold():
            raise serializers.ValidationError(
                _("The password is too similar to the username."))

        return password
