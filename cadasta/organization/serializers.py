from django.conf import settings
from django.db.models import Q
from django.core.urlresolvers import reverse
from core.util import slugify
from django.utils.translation import ugettext as _
from rest_framework import serializers
from rest_framework_gis import serializers as geo_serializers
from django_countries.serializer_fields import CountryField

from core.form_mixins import SuperUserCheck
from core import serializers as core_serializers
from accounts.models import User
from accounts.serializers import UserSerializer
from .models import Organization, Project, OrganizationRole, ProjectRole
from .forms import create_update_or_delete_project_role


class OrganizationSerializer(core_serializers.SanitizeFieldSerializer,
                             core_serializers.DetailSerializer,
                             core_serializers.FieldSelectorSerializer,
                             serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Organization
        fields = ('id', 'slug', 'name', 'description', 'archived', 'urls',
                  'contacts', 'users',)
        read_only_fields = ('id', 'slug',)
        detail_only_fields = ('users',)

    def validate_name(self, value):
        invalid_names = settings.CADASTA_INVALID_ENTITY_NAMES
        if slugify(value, allow_unicode=True) in invalid_names:
            raise serializers.ValidationError(
                _("Organization name cannot be “Add” or “New”."))
        return value

    def create(self, *args, **kwargs):
        org = super(OrganizationSerializer, self).create(*args, **kwargs)

        OrganizationRole.objects.create(
            organization=org,
            user=self.context['request'].user,
            admin=True
        )

        return org

    def update(self, *args, **kwargs):
        org = super(OrganizationSerializer, self).update(*args, **kwargs)
        data = args[1]
        if 'archived' in data.keys():
            for project in org.projects.all():
                project.archived = data['archived']
                project.save()

        return org


class ProjectSerializer(core_serializers.SanitizeFieldSerializer,
                        core_serializers.DetailSerializer,
                        serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)
    organization = OrganizationSerializer(hide_detail=True, read_only=True)
    country = CountryField(required=False)

    def validate_name(self, value):

        # Check that name is not restricted
        invalid_names = settings.CADASTA_INVALID_ENTITY_NAMES
        if slugify(value, allow_unicode=True) in invalid_names:
            raise serializers.ValidationError(
                _("Project name cannot be “Add” or “New”."))

        # Check that name is unique org-wide
        # (Explicit validation: see comment in the Meta class)
        is_create = not self.instance
        if is_create:
            org_slug = self.context['organization'].slug
        else:
            org_slug = self.instance.organization.slug
        queryset = Project.objects.filter(
            organization__slug=org_slug,
            name=value,
        )
        if is_create:
            not_unique = queryset.exists()
        else:
            not_unique = queryset.exclude(id=self.instance.id).exists()
        if not_unique:
            raise serializers.ValidationError(
                _("Project with this name already exists "
                  "in this organization."))

        return value

    class Meta:
        model = Project
        fields = ('id', 'organization', 'country', 'name', 'description',
                  'archived', 'urls', 'contacts', 'users', 'access', 'slug',
                  'extent',)
        read_only_fields = ('id', 'country', 'slug')
        detail_only_fields = ('users',)

        # Suppress automatic model-derived UniqueTogetherValidator because
        # organization is a read-only field in the serializer.
        # Instead, perform this validation explicitly in validate_name()
        validators = []

    def create(self, validated_data):
        organization = self.context['organization']
        return Project.objects.create(
            organization_id=organization.id,
            **validated_data
        )


class ProjectGeometrySerializer(geo_serializers.GeoFeatureModelSerializer):
    org = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = Project
        geo_field = 'extent'
        fields = ('name', 'org', 'url')

    def get_org(self, object):
        return object.organization.name

    def get_url(self, object):
        return reverse(
            'organization:project-dashboard',
            kwargs={'organization': object.organization.slug,
                    'project': object.slug})


class EntityUserSerializer(SuperUserCheck, serializers.Serializer):
    username = serializers.CharField()

    def to_representation(self, instance):
        if isinstance(instance, User):
            rep = UserSerializer(instance).data
            rep[self.Meta.role_key] = self.get_role_json(instance)
            return rep

    def to_internal_value(self, data):
        data[self.Meta.role_key] = self.set_roles(
            data.get(self.Meta.role_key, None)
        )
        return super().to_internal_value(data)

    def validate_username(self, value):
        error = ""
        if self.instance:
            self.user = self.instance
        else:
            users = User.objects.filter(Q(username=value) | Q(email=value))
            users_count = len(users)

            if users_count == 0:
                error = _("User with username or email {} does not exist")
            elif users_count > 1:
                error = _("More than one user found for username or email {}")
            else:
                self.user = users[0]

            if error:
                raise serializers.ValidationError(error.format(value))

            try:
                self.get_roles_object(self.user)
                raise serializers.ValidationError(
                    _("Not able to add member. The role already exists."))
            except self.Meta.role_model.DoesNotExist:
                pass

    def create(self, validated_data):
        obj = self.context[self.Meta.context_key]

        role_value = validated_data[self.Meta.role_key]

        create_kwargs = {
            self.Meta.role_key: role_value,
            self.Meta.context_key: obj,
            'user': self.user,
        }

        self.role = self.Meta.role_model.objects.create(**create_kwargs)
        return self.user

    def update(self, instance, validated_data):
        role = self.get_roles_object(instance)
        role_value = validated_data[self.Meta.role_key]

        if self.Meta.role_key in validated_data:
            setattr(role, self.Meta.role_key, role_value)

        role.save()

        return instance


class OrganizationUserSerializer(EntityUserSerializer):
    class Meta:
        role_model = OrganizationRole
        context_key = 'organization'
        role_key = 'admin'
    admin = serializers.BooleanField()

    def validate_admin(self, role_value):
        if 'request' in self.context:
            if self.context['request'].user == self.instance:
                if role_value != self.get_roles_object(self.instance).admin:
                    raise serializers.ValidationError(
                        _("Organization administrators cannot change their "
                          "own permissions within the organization"))
        return role_value

    def get_roles_object(self, instance):
        self.role = OrganizationRole.objects.get(
            user=instance,
            organization=self.context['organization'])

        return self.role

    def get_role_json(self, instance):
        role = self.get_roles_object(instance)
        return role.admin

    def set_roles(self, data):
        admin = False

        if self.instance:
            role = self.get_roles_object(self.instance)
            admin = role.admin

        if data:
            admin = data

        return admin


class ProjectUserSerializer(EntityUserSerializer):
    class Meta:
        role_model = ProjectRole
        context_key = 'project'
        role_key = 'role'
    role = serializers.CharField()

    def validate(self, data):
        if ((self.instance and self.is_superuser(self.instance)) or
                self.org_role.admin):
            raise serializers.ValidationError(
                _("User {username} is an organization admin, the role cannot "
                  "be updated.").format(username=self.instance.username))
        return super().validate(data)

    def validate_username(self, value):
        try:
            super(ProjectUserSerializer, self).validate_username(value)
        except OrganizationRole.DoesNotExist:
            raise serializers.ValidationError(
                _("User {username} is not member of the project\'s "
                  "organization").format(username=value))

    def get_roles_object(self, instance):
        project = self.context[self.Meta.context_key]
        self.org_role = instance.organizationrole_set.get(
            organization_id=project.organization_id)

        if not self.org_role.admin:
            return instance.projectrole_set.get(
                project=self.context['project'])

        return self.org_role

    def get_role_key(self, role):
        if hasattr(role, 'role'):
            return role.role
        else:
            return 'A' if role.admin else 'Pb'

    def get_role_json(self, instance):
        if self.is_superuser(instance):
            return 'A'

        try:
            role = self.get_roles_object(instance)
            return self.get_role_key(role)
        except ProjectRole.DoesNotExist:
            return 'Pb'

    def set_roles(self, data):
        user_role = 'Pb'

        if self.instance:
            user_role = self.get_role_json(self.instance)

        if data:
            user_role = data

        return user_role

    def update(self, instance, validated_data):
        role = validated_data[self.Meta.role_key]
        create_update_or_delete_project_role(self.context['project'].id,
                                             instance,
                                             role)

        return instance


class UserAdminSerializer(UserSerializer):
    organizations = OrganizationSerializer(
        many=True, read_only=True, fields=('id', 'name'))

    class Meta:
        model = User
        fields = ('username', 'full_name', 'email',
                  'organizations', 'last_login', 'is_active')
