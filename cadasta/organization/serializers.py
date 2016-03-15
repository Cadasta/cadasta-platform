from django.utils.text import slugify
from rest_framework.serializers import ModelSerializer, ValidationError

from core.serializers import DetailSerializer
from accounts.serializers import UserSerializer
from accounts.models import User
from .models import Organization


class OrganizationSerializer(DetailSerializer, ModelSerializer):
    users = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Organization
        fields = ('id', 'slug', 'name', 'description', 'archived', 'urls',
                  'contacts', 'users')
        read_only_fields = ('id',)
        detail_only_fields = ('users',)

    def to_internal_value(self, data):
        if not data.get('slug'):
            data['slug'] = slugify(data.get('name'))

        return super(OrganizationSerializer, self).to_internal_value(data)


class UserOrganizationSerializer(ModelSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'name')
        read_only_fields = ('id', 'name')


class UserAdminSerializer(ModelSerializer):
    organizations = UserOrganizationSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',
                  'organizations', 'last_login', 'is_active')

    def validate_username(self, username):
        instance = self.instance
        if instance is not None:
            if (username is not None and
               username != instance.username):
                raise ValidationError('Cannot update username')
        return username

    def validate_last_login(self, last_login):
        instance = self.instance
        if instance is not None:
            if (last_login is not None and
               last_login != instance.last_login):
                raise ValidationError('Cannot update last_login')
        return last_login
