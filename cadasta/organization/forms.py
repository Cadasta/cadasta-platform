import itertools
import json
from django import forms
from django.contrib.postgres import forms as pg_forms
from django.contrib.gis import forms as gisforms
from leaflet.forms.widgets import LeafletWidget
from django.utils.translation import ugettext as _
from django.utils.text import slugify
from tutelary.models import Role

from .models import Organization


class OrganizationForm(forms.ModelForm):
    urls = pg_forms.SimpleArrayField(forms.URLField(), required=False)
    contacts = forms.CharField(required=False)

    class Meta:
        model = Organization
        fields = ['name', 'description', 'urls', 'contacts']

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
        instance = super(OrganizationForm, self).save(commit=False)

        # ensuring slug is unique
        if not instance.slug:
            instance.slug = orig = slugify(instance.name)
            for x in itertools.count(1):
                if not Organization.objects.filter(
                        slug=instance.slug).exists():
                    break
                instance.slug = '{}-{}'.format(orig, x)

        instance.save()

        return instance


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
    ROLE_CHOICES = (('PU', 'Project User'),
                    ('DC', 'Data Collector'),
                    ('PM', 'Project Manager'))

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
                    f = forms.ChoiceField(choices=self.ROLE_CHOICES)
                    self.fields[user.username] = f
                self.members.append({
                    'index': idx, 'field': f,
                    'username': user.username, 'email': user.email,
                    'name': user.first_name + ' ' + user.last_name,
                    'is_admin': is_admin})
