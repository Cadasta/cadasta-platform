from django import forms
from django.contrib.gis import forms as gisforms
from django.utils.translation import ugettext as _

from leaflet.forms.widgets import LeafletWidget
from core.util import ID_FIELD_LENGTH
from party.models import Party, TenureRelationship, TenureRelationshipType
from .models import SpatialUnit
from .widgets import SelectPartyWidget, NewEntityWidget


class LocationForm(forms.ModelForm):
    geometry = gisforms.GeometryField(widget=LeafletWidget())

    class Meta:
        model = SpatialUnit
        fields = ['geometry', 'type']

    def __init__(self, project_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_id = project_id

    def save(self):
        instance = super().save(commit=False)
        instance.project_id = self.project_id
        instance.save()
        return instance


REL_TYPE_CHOICES = (
    ('', 'Please select'),
    ('L', 'Location'),
    ('P', 'Party')
)


class TenureRelationshipForm(forms.Form):
    id = forms.CharField(
        required=False,
        max_length=ID_FIELD_LENGTH)
    new_entity = forms.BooleanField(required=False, widget=NewEntityWidget())
    name = forms.CharField(required=False, max_length=200)
    party_type = forms.ChoiceField(choices=Party.TYPE_CHOICES)
    tenure_type = forms.ChoiceField(choices=[])

    class Media:
        js = ('/static/js/rel_tenure.js',)

    def __init__(self, project, spatial_unit, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id'].widget = SelectPartyWidget(project.id)
        tenure_types = TenureRelationshipType.objects.values_list('id',
                                                                  'label')
        self.fields['tenure_type'].choices = tenure_types
        self.project = project
        self.spatial_unit = spatial_unit

    def clean_id(self):
        new_entity = self.data.get('new_entity', None)
        id = self.cleaned_data.get('id', '')

        if not new_entity and not id:
            raise forms.ValidationError(_("This field is required."))
        return id

    def clean_name(self):
        new_entity = self.cleaned_data.get('new_entity', None)
        name = self.cleaned_data.get('name', None)

        if new_entity and not name:
            raise forms.ValidationError(_("This field is required."))
        return name

    def save(self):
        if self.cleaned_data['new_entity']:
            party = Party.objects.create(
                name=self.cleaned_data['name'],
                type=self.cleaned_data['party_type'],
                project=self.project
            )
        else:
            party = Party.objects.get(pk=self.cleaned_data['id'])

        t = TenureRelationship.objects.create(
            party=party,
            spatial_unit=self.spatial_unit,
            tenure_type_id=self.cleaned_data['tenure_type'],
            project=self.project
        )
        return t
