from django import forms
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis import forms as gisforms
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as __

from leaflet.forms.widgets import LeafletWidget

from core.form_mixins import AttributeForm, AttributeModelForm
from core.util import ID_FIELD_LENGTH
from party.models import Party, TenureRelationship, TenureRelationshipType

from .models import TYPE_CHOICES, SpatialUnit
from .widgets import NewEntityWidget, SelectPartyWidget


class LocationForm(AttributeModelForm):
    attributes_field = 'attributes'

    geometry = gisforms.GeometryField(
        widget=LeafletWidget(),
        error_messages={
            'required': __('No map location was provided. Please use the '
                           'tools provided on the left side of the map to '
                           'mark your new location.')}
    )
    type = forms.ChoiceField(
        choices=filter(lambda c: c[0] != 'PX', (
            [('', __('Please select a location type'))] +
            list(TYPE_CHOICES)
        ))
    )

    class Meta:
        model = SpatialUnit
        fields = ['geometry', 'type']

    def __init__(self, project=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.add_attribute_fields()

        if self.project.current_questionnaire:
            self.set_standard_field('location_type',
                                    _('Please select a location type'),
                                    field_name='type')

    def save(self, *args, **kwargs):
        entity_type = self.cleaned_data['type']
        kwargs['entity_type'] = entity_type
        kwargs['project_id'] = self.project.pk
        return super().save(*args, **kwargs)


class TenureRelationshipForm(AttributeForm):
    # new_entity should be first because the other fields depend on it
    new_entity = forms.BooleanField(required=False, widget=NewEntityWidget())
    id = forms.CharField(required=False, max_length=ID_FIELD_LENGTH)
    name = forms.CharField(required=False, max_length=200)
    party_type = forms.ChoiceField(required=False, choices=[])
    tenure_type = forms.ChoiceField(required=True, choices=[])

    class Media:
        js = ('/static/js/rel_tenure.js', '/static/js/party_attrs.js')

    def __init__(self, project, spatial_unit, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project

        self.fields['id'].widget = SelectPartyWidget(project.id)
        self.fields['party_type'].choices = (
            [('', _("Please select a party type"))] + list(Party.TYPE_CHOICES))
        self.fields['tenure_type'].choices = (
            [('', _("Please select a relationship type"))] +
            sorted([
                (choice[0], _(choice[1])) for choice in
                TenureRelationshipType.objects.values_list('id', 'label')]))

        if self.project.current_questionnaire:
            self.set_standard_field('party_name',
                                    _('Please select a party type'),
                                    field_name='name')
            self.set_standard_field('party_type',
                                    _('Please select a party type'))
            self.set_standard_field('tenure_type',
                                    _('Please select a relationship type'))

        self.spatial_unit = spatial_unit
        self.party_ct = ContentType.objects.get(
            app_label='party', model='party')
        self.tenure_ct = ContentType.objects.get(
            app_label='party', model='tenurerelationship')
        self.add_attribute_fields(self.party_ct)
        self.add_attribute_fields(self.tenure_ct)

    def clean_id(self):
        new_entity = self.cleaned_data.get('new_entity', None)
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

    def clean_party_type(self):
        new_entity = self.cleaned_data.get('new_entity', None)
        party_type = self.cleaned_data.get('party_type', None)

        if new_entity and not party_type:
            raise forms.ValidationError(_("This field is required."))
        return party_type

    def clean(self):
        # remove validation errors for required fields
        # which are not related to the current party type
        new_entity = self.cleaned_data.get('new_entity', False)
        if not new_entity:
            for name, field in self.fields.items():
                if name.startswith('party::'):
                    if (field.required and
                            self.errors.get(name, None) is not None):
                        del self.errors[name]

        party_type = self.cleaned_data.get('party_type', None)
        if party_type:
            ptype = party_type.lower()
            for name, field in self.fields.items():
                if (name.startswith('party::') and not
                        name.startswith('party::%s' % ptype)):
                    if (field.required and self.errors.get(name, None)
                            is not None):
                        del self.errors[name]

    def save(self):
        if self.cleaned_data['new_entity']:
            party = Party.objects.create(
                name=self.cleaned_data['name'],
                type=self.cleaned_data['party_type'],
                project=self.project,
                attributes=self.process_attributes(
                    self.party_ct.model, self.cleaned_data['party_type']
                )
            )
        else:
            party = Party.objects.get(pk=self.cleaned_data['id'])

        tenurerelationship = TenureRelationship.objects.create(
            party=party,
            spatial_unit=self.spatial_unit,
            tenure_type_id=self.cleaned_data['tenure_type'],
            project=self.project,
            attributes=self.process_attributes(
                self.tenure_ct.model, self.cleaned_data['tenure_type']
            )
        )
        return tenurerelationship
