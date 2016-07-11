from jsonattrs.forms import AttributeModelForm
from .models import Party, TenureRelationshipType, TenureRelationship


class PartyForm(AttributeModelForm):
    attributes_field = 'attributes'

    class Meta:
        model = Party
        fields = ['name', 'type']

    def __init__(self, project_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_id = project_id

    def save(self):
        instance = super().save(commit=False)
        instance.project_id = self.project_id
        instance.save()
        return instance


class TenureRelationshipEditForm(AttributeModelForm):
    attributes_field = 'attributes'

    class Meta:
        model = TenureRelationship
        fields = ['tenure_type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tenure_types = TenureRelationshipType.objects.values_list('id',
                                                                  'label')
        self.fields['tenure_type'].choices = tenure_types

    def save(self):
        return super().save()
