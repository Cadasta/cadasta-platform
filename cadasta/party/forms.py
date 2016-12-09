from core.form_mixins import AttributeModelForm
from .models import Party, TenureRelationshipType, TenureRelationship


class PartyForm(AttributeModelForm):
    attributes_field = 'attributes'

    class Meta:
        model = Party
        fields = ['name', 'type']

    class Media:
        js = ('/static/js/party_attrs.js',)

    def __init__(self, project, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.add_attribute_fields()

    def clean(self):
        # remove validation errors for required fields
        # which are not related to the current type
        party_type = self.cleaned_data.get('type', None)
        if party_type:
            ptype = party_type.lower()
            for name, field in self.fields.items():
                if (name.startswith('party::') and not
                        name.startswith('party::%s' % ptype)):
                    if (field.required and self.errors.get(name, None)
                            is not None):
                        del self.errors[name]

    def save(self, *args, **kwargs):
        entity_type = self.cleaned_data['type']
        kwargs['entity_type'] = entity_type
        kwargs['project_id'] = self.project.pk
        return super().save(*args, **kwargs)


class TenureRelationshipEditForm(AttributeModelForm):
    attributes_field = 'attributes'

    class Meta:
        model = TenureRelationship
        fields = ['tenure_type']

    def __init__(self, project=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        tenuretypes = sorted(
            TenureRelationshipType.objects.values_list('id', 'label')
        )
        self.fields['tenure_type'].choices = tenuretypes
        self.add_attribute_fields()

    def save(self, *args, **kwargs):
        entity_type = self.cleaned_data['tenure_type']
        kwargs['entity_type'] = entity_type.id
        kwargs['project_id'] = self.project.pk
        return super().save(*args, **kwargs)
