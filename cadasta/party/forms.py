from jsonattrs.forms import AttributeModelForm
from .models import Party, TenureRelationshipType, TenureRelationship
from questionnaires.forms import OptionLabelsFix


class PartyForm(OptionLabelsFix, AttributeModelForm):
    attributes_field = 'attributes'

    class Meta:
        model = Party
        fields = ['name', 'type']

    def __init__(self, project_id=None, *args, **kwargs):
        self.project_id = project_id
        super().__init__(*args, **kwargs)

    def save(self):
        instance = super().save(commit=False)
        instance.project_id = self.project_id
        instance.save()
        return instance


class TenureRelationshipEditForm(OptionLabelsFix, AttributeModelForm):
    attributes_field = 'attributes'

    class Meta:
        model = TenureRelationship
        fields = ['tenure_type']

    def __init__(self, *args, **kwargs):
        self.project_id = kwargs.pop('project_id', None)
        super().__init__(*args, **kwargs)
        tenuretypes = sorted(
            TenureRelationshipType.objects.values_list('id', 'label')
        )
        self.fields['tenure_type'].choices = tenuretypes

    def save(self):
        return super().save()
