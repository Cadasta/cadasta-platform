from django.utils import timezone

from django.utils.translation import ugettext as _

from rest_framework.serializers import EmailField
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
            'first_name',
            'last_name',
            'email',
            'password',
            'email_verified',
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True, 'unique': True}
        }


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
            'first_name',
            'last_name',
            'email',
            'email_verified',
        )
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True, 'unique': True},
            'email_verified': {'read_only': True}
        }


class AccountLoginSerializer(djoser_serializers.LoginSerializer):
    def validate(self, attrs):
        attrs = super(AccountLoginSerializer, self).validate(attrs)

        if (not self.user.email_verified and
                timezone.now() > self.user.verify_email_by):
            raise EmailNotVerifiedError

        return attrs
