from django.test import TestCase

from organization.tests.factories import ProjectFactory
from ..models import Party, TenureRelationshipType
from .. import forms


class PartyFormTest(TestCase):
    def test_create_location(self):
        data = {
            'name': 'Cadasta',
            'type': 'IN'
        }
        project = ProjectFactory.create()
        form = forms.PartyForm(project_id=project.id, data=data)
        form.is_valid()
        form.save()

        assert Party.objects.filter(project=project).count() == 1


class TenureRelationshipEditFormTest(TestCase):
    def test_init(self):
        form = forms.TenureRelationshipEditForm()
        tenure_types = TenureRelationshipType.objects.values_list('id',
                                                                  'label')
        assert list(form.fields['tenure_type'].choices) == list(tenure_types)
