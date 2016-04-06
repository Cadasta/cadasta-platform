from django.conf import settings
from django.utils.text import slugify
from django.db.models import Q
from django.core.mail import send_mail
from django.utils.translation import ugettext as _
from django.template.loader import get_template
from django.template import Context
from rest_framework import serializers
from django_countries.serializer_fields import CountryField

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

    def create(self, *args, **kwargs):
        org = super(OrganizationSerializer, self).create(*args, **kwargs)

        OrganizationRole.objects.create(
            organization=org,
            user=self.context['request'].user
        )

        return org


class ProjectSerializer(DetailSerializer, serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)
    organization = OrganizationSerializer(read_only=True)
    country = CountryField(required=False)

    class Meta:
        model = Project
        fields = ('id', 'organization', 'country', 'name', 'description',
                  'archived', 'urls', 'contacts', 'users', 'access',)
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
    role = serializers.CharField()

    def to_representation(self, instance):
        if isinstance(instance, User):
            rep = UserSerializer(instance).data
            rep['role'] = self.get_role_json(instance)
            return rep

    def to_internal_value(self, data):
        data['role'] = self.set_roles(data.get('role', None))
        return super(EntityUserSerializer, self).to_internal_value(data)

    def validate_username(self, value):
        error = ""
        if not self.instance:
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

    def create(self, validated_data):
        obj = self.context[self.Meta.context_key]

        create_kwargs = {
            self.Meta.role_key: validated_data['role'],
            self.Meta.context_key: obj,
            'user': self.user,
        }

        self.role = self.Meta.role_model.objects.create(**create_kwargs)

        if hasattr(self, 'send_invitaion_email'):
            self.send_invitaion_email()

        return self.user

    def update(self, instance, validated_data):
        role = self.get_roles_object(instance)

        if 'role' in validated_data:
            setattr(role, self.Meta.role_key, validated_data['role'])

        role.save()

        return instance


class OrganizationUserSerializer(EntityUserSerializer):
    class Meta:
        role_model = OrganizationRole
        context_key = 'organization'
        role_key = 'admin'

    def get_roles_object(self, instance):
        if not hasattr(self, 'role'):
            self.role = OrganizationRole.objects.get(
                user=instance,
                organization=self.context['organization'])

        return self.role

    def get_role_json(self, instance):
        role = self.get_roles_object(instance)
        return 'Admin' if role.admin else 'User'

    def set_roles(self, data):
        admin = False

        if self.instance:
            role = self.get_roles_object(self.instance)
            admin = role.admin

        if data:
            admin = data

        return admin

    def send_invitaion_email(self):
        template = get_template('organization/email/org_invite.txt')
        organization = self.context['organization']
        context = Context({
            'site_name': self.context['sitename'],
            'organization': organization.name,
            'domain': self.context['domain'],
            'url': 'organizations/{}/leave'.format(organization.slug),
        })
        message = template.render(context)
        print(message)

        subject = _("You have been added to organization "
                    "{organization}").format(
                        organization=self.context['organization'].name
                    )
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None),
        send_mail(subject, message, from_email, [self.user.email])


class ProjectUserSerializer(EntityUserSerializer):
    class Meta:
        role_model = ProjectRole
        context_key = 'project'
        role_key = 'role'

    def validate_username(self, value):
        super(ProjectUserSerializer, self).validate_username(value)
        project = self.context[self.Meta.context_key]

        if self.user not in project.organization.users.all():
            raise serializers.ValidationError(
                _("User {username} is not member of the project\'s "
                  "organization").format(username=value))

    def get_roles_object(self, instance):
        if not hasattr(self, 'role'):
            self.role = ProjectRole.objects.get(
                user=instance,
                project=self.context['project'])

        return self.role

    def get_role_json(self, instance):
        role = self.get_roles_object(instance)
        return role.role

    def set_roles(self, data):
        user_role = 'PU'

        if self.instance:
            role = self.get_roles_object(self.instance)
            user_role = role.role

        if data:
            user_role = data

        return user_role


class UserAdminSerializer(UserSerializer):
    organizations = OrganizationSerializer(
        many=True, read_only=True, fields=('id', 'name'))

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email',
                  'organizations', 'last_login', 'is_active')
