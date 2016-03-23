import itertools
import json
from django import forms
from django.contrib.postgres import forms as pg_forms
from django.contrib.gis import forms as gisforms
from leaflet.forms.widgets import LeafletWidget
from django.utils.translation import ugettext as _
from django.utils.text import slugify
from tutelary.models import Role

from accounts.models import User
from .models import Organization, OrganizationRole, ProjectRole
from .choices import ADMIN_CHOICES, ROLE_CHOICES

FORM_CHOICES = ROLE_CHOICES + (('Pb', 'Public User'),)


class OrganizationForm(forms.ModelForm):
    urls = pg_forms.SimpleArrayField(forms.URLField(), required=False)
    contacts = forms.CharField(required=False)

    class Meta:
        model = Organization
        fields = ['name', 'description', 'urls', 'contacts']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(OrganizationForm, self).__init__(*args, **kwargs)

    def to_list(self, value):
        if value:
            return [value]
        else:
            return []

    def clean_urls(self):
        return self.to_list(self.data.get('urls'))

    def clean_contacts(self):
        contacts = self.data.get('contacts')
        if contacts:
            return json.loads(contacts)
        return contacts

    def save(self, *args, **kwargs):
        print('save')
        instance = super(OrganizationForm, self).save(commit=False)
        create = not instance.id

        # ensuring slug is unique
        if not instance.slug:
            instance.slug = orig = slugify(instance.name)
            for x in itertools.count(1):
                if not Organization.objects.filter(
                        slug=instance.slug).exists():
                    break
                instance.slug = '{}-{}'.format(orig, x)

        instance.save()

        if create:
            OrganizationRole.objects.create(
                organization=instance,
                user=self.user
            )

        return instance


class AddOrganizationMemberForm(forms.Form):
    identifier = forms.CharField()

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        self.instance = kwargs.pop('instance', None)
        super(AddOrganizationMemberForm, self).__init__(*args, **kwargs)

    def clean_identifier(self):
        identifier = self.data.get('identifier')
        try:
            self.user = User.objects.get_from_username_or_email(
                identifier=identifier)
        except (User.DoesNotExist, User.MultipleObjectsReturned) as e:
            raise forms.ValidationError(e)

    def save(self):
        if self.errors:
            raise ValueError(
                "The role could not be assigned because the data didn't "
                "validate."
            )

        self.instance = OrganizationRole.objects.create(
            user=self.user,
            organization=self.organization
        )
        return self.instance


class EditOrganizationMemberForm(forms.Form):
    org_role = forms.ChoiceField(choices=ADMIN_CHOICES)

    def __init__(self, data, organization, user, *args, **kwargs):
        super(EditOrganizationMemberForm, self).__init__(data, *args, **kwargs)
        self.data = data
        self.organization = organization
        self.user = user

        self.org_role_instance = OrganizationRole.objects.get(
            user=user,
            organization=self.organization)

        self.initial['org_role'] = 'A' if self.org_role_instance.admin else 'M'

        project_roles = ProjectRole.objects.filter(
            project__organization=organization,
            user=user)

        for p in self.organization.projects.values_list('id', 'name'):
            try:
                role = project_roles.get(project_id=p[0]).role
            except ProjectRole.DoesNotExist:
                role = 'Pb'

            self.fields[p[0]] = forms.ChoiceField(
                choices=FORM_CHOICES,
                label=p[1],
                required=False,
                initial=role
            )

    def save(self):
        self.org_role_instance.admin = self.data.get('org_role') == 'A'
        self.org_role_instance.save()

        for f in [field for field in self.fields if field != 'org_role']:
            role = self.data.get(f)
            if role != 'Pb':
                ProjectRole.objects.update_or_create(
                    user=self.user,
                    project_id=f,
                    defaults={'role': role})
            else:
                ProjectRole.objects.filter(user=self.user,
                                           project_id=f).delete()


class ProjectAddExtents(forms.Form):
    location = gisforms.PolygonField(widget=LeafletWidget, required=False)


class ProjectAddDetails(forms.Form):
    organization = forms.ChoiceField()
    name = forms.CharField(max_length=100)
    description = forms.CharField(required=False, widget=forms.Textarea)
    public = forms.BooleanField(initial=True)
    url = forms.URLField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['organization'].choices = [
            (o.slug, o.name) for o in Organization.objects.order_by('name')
        ]


class ProjectAddPermissions(forms.Form):
    def __init__(self, organization, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if organization is not None:
            self.organization = organization
            org = Organization.objects.get(slug=organization)
            su_role = Role.objects.get(name='superuser')
            oa_role = Role.objects.get(name=organization + '-oa')
            self.members = []
            for user, idx in zip(org.users.all(), itertools.count()):
                is_admin = False
                for pol in user.assigned_policies():
                    if (isinstance(pol, Role) and
                       (pol == su_role or pol == oa_role)):
                        is_admin = True
                        break
                f = None
                if not is_admin:
                    f = forms.ChoiceField(choices=ROLE_CHOICES)
                    self.fields[user.username] = f
                self.members.append({
                    'index': idx, 'field': f,
                    'username': user.username, 'email': user.email,
                    'name': user.first_name + ' ' + user.last_name,
                    'is_admin': is_admin})
