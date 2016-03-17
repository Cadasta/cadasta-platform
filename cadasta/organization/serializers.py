from django.utils.text import slugify
from rest_framework.serializers import ModelSerializer

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


class UserAdminSerializer(UserSerializer):
    organizations = UserOrganizationSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',
                  'organizations', 'last_login', 'is_active')
