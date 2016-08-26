from django import forms
from django.contrib.gis import forms as gisforms
from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType

from jsonattrs.models import Schema, compose_schemas
from jsonattrs.forms import form_field_from_name, AttributeModelForm

from leaflet.forms.widgets import LeafletWidget
from core.util import ID_FIELD_LENGTH
from party.models import Party, TenureRelationship, TenureRelationshipType
from .models import SpatialUnit
from .widgets import SelectPartyWidget, NewEntityWidget


class LocationForm(AttributeModelForm):
    geometry = gisforms.GeometryField(
        widget=LeafletWidget(),
        error_messages={
            'required': _('No map location was provided. Please use the tools '
                          'provided on the left side of the map to mark your '
                          'new location.')}
    )
    attributes_field = 'attributes'

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

    def __init__(self, project, spatial_unit, schema_selectors=(),
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['id'].widget = SelectPartyWidget(project.id)
        tenure_types = TenureRelationshipType.objects.values_list('id',
                                                                  'label')
        self.fields['tenure_type'].choices = tenure_types
        self.project = project
        self.spatial_unit = spatial_unit
        self.add_attribute_fields(schema_selectors)

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

    def create_model_fields(self, model, field_prefix, selectors,
                            new_item=False):
        content_type = ContentType.objects.get_for_model(model)
        schemas = Schema.objects.lookup(
            content_type=content_type, selectors=selectors
        )
        attrs, _, _ = compose_schemas(*schemas)
        for name, attr in attrs.items():
            fieldname = field_prefix + '::' + name
            atype = attr.attr_type
            initial = self.data.get(fieldname, '')
            args = {
                'label': attr.long_name,
                'required': False,
                'initial': initial
            }
            field = form_field_from_name(atype.form_field)
            # if atype.form_field == 'CharField':
            #     args['max_length'] = 32
            if (atype.form_field == 'ChoiceField' or
               atype.form_field == 'MultipleChoiceField'):
                args['choices'] = list(map(lambda c: (c, c), attr.choices))
            if atype.form_field == 'BooleanField':
                args['required'] = False
                if len(attr.default) > 0:
                    args['initial'] = (attr.default != 'False')
            else:
                if attr.required and new_item:
                    args['required'] = True
                if len(attr.default) > 0 and len(initial) == 0:
                    args['initial'] = attr.default
            self.fields[fieldname] = field(**args)

    def add_attribute_fields(self, schema_selectors):
        selectors = [s['selector'] for s in schema_selectors]

        new_item = self.data.get('new_item') == 'on'
        self.create_model_fields(Party, 'party', selectors, new_item=new_item)
        self.create_model_fields(TenureRelationship, 'relationship', selectors)

    def process_attributes(self, key):
        attributes = {}
        length = len(key + '::')
        for k, v in self.cleaned_data.items():
            if k.startswith(key + '::'):
                k = k[length::]
                attributes[k] = v
        return attributes

    def save(self):
        if self.cleaned_data['new_entity']:
            party = Party.objects.create(
                name=self.cleaned_data['name'],
                type=self.cleaned_data['party_type'],
                project=self.project,
                attributes=self.process_attributes('party')
            )
        else:
            party = Party.objects.get(pk=self.cleaned_data['id'])

        t = TenureRelationship.objects.create(
            party=party,
            spatial_unit=self.spatial_unit,
            tenure_type_id=self.cleaned_data['tenure_type'],
            project=self.project,
            attributes=self.process_attributes('relationship')
        )
        return t
