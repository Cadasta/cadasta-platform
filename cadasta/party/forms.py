from django.forms import ChoiceField
from core.form_mixins import AttributeModelForm, SanitizeFieldsForm
from .models import Party, TenureRelationship
from .choices import TENURE_RELATIONSHIP_TYPES


class PartyForm(SanitizeFieldsForm, AttributeModelForm):
    attributes_field = 'attributes'

    class Meta:
        model = Party
        fields = ['name', 'type']

    class Media:
        js = ('/static/js/party_attrs.js',  'js/parsley/sanitize.js')

    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.add_attribute_fields()

        if self.project.current_questionnaire:
            self.set_standard_field('party_name', field_name='name')
            self.set_standard_field('party_type', field_name='type')

    def clean(self):
        # remove validation errors for required fields
        # which are not related to the current type
        cleaned_data = super().clean()
        party_type = cleaned_data.get('type', None)
        if party_type:
            ptype = party_type.lower()
            for name, field in self.fields.items():
                if (name.startswith('party::') and not
                        name.startswith('party::%s' % ptype)):
                    if (field.required and self.errors.get(name, None)
                            is not None):
                        del self.errors[name]
        return cleaned_data

    def save(self, *args, **kwargs):
        entity_type = self.cleaned_data['type']
        kwargs['entity_type'] = entity_type
        kwargs['project_id'] = self.project.pk
        return super().save(*args, **kwargs)


class TenureRelationshipEditForm(SanitizeFieldsForm, AttributeModelForm):
    tenure_type = ChoiceField(choices=TENURE_RELATIONSHIP_TYPES)
    attributes_field = 'attributes'

    class Meta:
        model = TenureRelationship
        fields = ['tenure_type']

    class Media:
        js = ('js/parsley/sanitize.js', )

    def __init__(self, project=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project

        if self.project.current_questionnaire:
            self.set_standard_field('tenure_type')

        self.add_attribute_fields()

    def save(self, *args, **kwargs):
        kwargs['project_id'] = self.project.pk
        return super().save(*args, **kwargs)
