from django.utils.text import slugify
from rest_framework import serializers

from core.serializers import DetailSerializer
from accounts.models import User
from accounts.serializers import UserSerializer
from .models import Organization, Project


class OrganizationSerializer(DetailSerializer, serializers.ModelSerializer):
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


class ProjectUserSerializer(serializers.Serializer):
    username = serializers.CharField()
    roles = serializers.JSONField()

    def set_roles(self, user, roles):
        pass

    def to_internal_value(self, data):
        if data and data.get('roles'):
            default_roles = {
                'manager': False,
                'collector': False
            }

            if self.instance:
                pass
                # TODO: Find the roles for the user
                # 1. Read the current roles for the user and save as default
                # 2. Read the new roles from data and update default_roles
                #    accordingly

                default_roles = {
                    'manager': True,
                    'collector': True
                }

            new_roles = {
                'manager': data['roles'].get(
                    'manager', default_roles['manager']),
                'collector': data['roles'].get(
                    'collector', default_roles['collector'])
            }

            data['roles'] = new_roles
            self.roles_json = new_roles

        return data

    def to_representation(self, instance):
        rep = UserSerializer(instance).data

        if not hasattr(self, 'roles_json'):
            self.roles_json = {
                'manager': False,
                'collector': False
            }
            # TODO: Find roles for the user
        rep['roles'] = self.roles_json

        return rep

    def create(self, validated_data):
        user = User.objects.get(username=validated_data['username'])
        project = self.context['project']
        project.users.add(user)

        # TODO: Find the relevant policy according to roles and assign it
        # to the user
        self.set_roles(user, validated_data.get('roles'))

        return user

    def update(self, instance, validated_data):
        # TODO: Update the policy according to roles
        self.set_roles(instance, validated_data.get('roles'))

        return instance
