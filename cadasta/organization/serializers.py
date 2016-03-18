from django.utils.text import slugify
from rest_framework import serializers

from core.serializers import DetailSerializer, FieldSelectorSerializer
from accounts.models import User
from accounts.serializers import UserSerializer
from .models import Organization, Project, OrganizationRole, ProjectRole


class OrganizationSerializer(DetailSerializer, FieldSelectorSerializer,
                             serializers.ModelSerializer):
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


class ProjectSerializer(DetailSerializer, serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)
    organization = OrganizationSerializer(read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'organization', 'country', 'name', 'description',
                  'archived', 'urls', 'contacts', 'users')
        read_only_fields = ('id', 'country',)
        detail_only_fields = ('users',)

    def create(self, validated_data):
        organization = self.context['organization']
        return Project.objects.create(
            organization_id=organization.id,
            **validated_data
        )


class EntityUserSerializer(serializers.Serializer):
    username = serializers.CharField()
    roles = serializers.JSONField()

    def to_representation(self, instance):
        if isinstance(instance, User):
            rep = UserSerializer(instance).data
            rep['roles'] = self.get_roles_json(instance)
            return rep

    def to_internal_value(self, data):
        data['roles'] = self.set_roles(data.get('roles', None))
        return super(EntityUserSerializer, self).to_internal_value(data)

    def validate_username(self, value):
        if not self.instance:
            try:
                self.user = User.objects.get(username=value)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    'User {} does not exist'.format(value))

    def create(self, validated_data):
        obj = self.context[self.Meta.context_key]

        create_kwargs = validated_data['roles']
        create_kwargs['user'] = self.user
        create_kwargs[self.Meta.context_key] = obj

        self.role = self.Meta.role_model.objects.create(**create_kwargs)

        return self.user

    def update(self, instance, validated_data):
        role = self.get_roles_object(instance)

        for key in validated_data['roles'].keys():
            setattr(role, key, validated_data['roles'][key])

        role.save()

        return instance


class OrganizationUserSerializer(EntityUserSerializer):
    class Meta:
        role_model = OrganizationRole
        context_key = 'organization'

    def get_roles_object(self, instance):
        if not hasattr(self, 'role'):
            self.role = OrganizationRole.objects.get(
                user=instance,
                organization=self.context['organization'])

        return self.role

    def get_roles_json(self, instance):
        role = self.get_roles_object(instance)

        return {
            'admin': role.admin
        }

    def set_roles(self, data):
        roles = {
            'admin': False
        }

        if self.instance:
            role = self.get_roles_object(self.instance)
            roles['admin'] = role.admin

        if data:
            roles['admin'] = data.get('admin', roles['admin'])

        return roles


class ProjectUserSerializer(EntityUserSerializer):
    class Meta:
        role_model = ProjectRole
        context_key = 'project'

    def get_roles_object(self, instance):
        if not hasattr(self, 'role'):
            self.role = ProjectRole.objects.get(
                user=instance,
                project=self.context['project'])

        return self.role

    def get_roles_json(self, instance):
        role = self.get_roles_object(instance)

        return {
            'manager': role.manager,
            'collector': role.collector
        }

    def set_roles(self, data):
        roles = {
            'manager': False,
            'collector': False
        }

        if self.instance:
            role = self.get_roles_object(self.instance)
            roles['manager'] = role.manager
            roles['collector'] = role.collector

        if data:
            roles['manager'] = data.get('manager', roles['manager'])
            roles['collector'] = data.get('collector', roles['collector'])

        return roles


class UserAdminSerializer(UserSerializer):
    organizations = OrganizationSerializer(
        many=True, read_only=True, fields=('id', 'name'))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',
                  'organizations', 'last_login', 'is_active')
