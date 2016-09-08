from django.contrib.contenttypes.models import ContentType
from jsonattrs.models import Attribute, AttributeType, Schema

from core.tests.base_test_case import UserTestCase
from organization.tests.factories import ProjectFactory
from ..models import Party, TenureRelationshipType
from .. import forms


class PartyFormTest(UserTestCase):
    def test_create_party(self):
        data = {
            'name': 'Cadasta',
            'type': 'IN'
        }
        project = ProjectFactory.create()
        form = forms.PartyForm(project_id=project.id,
                               data=data,
                               schema_selectors=())
        form.is_valid()
        form.save()

        assert Party.objects.filter(project=project).count() == 1

    def test_create_party_with_attributes(self):
        data = {
            'name': 'Cadasta',
            'type': 'IN',
            'attributes::fname': 'test'
        }
        project = ProjectFactory.create()

        content_type = ContentType.objects.get(
            app_label='party', model='party')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, ))

        Attribute.objects.create(
            schema=schema,
            name='fname',
            long_name='Test field',
            attr_type=AttributeType.objects.get(name='text'),
            index=0
        )

        form = forms.PartyForm(project_id=project.id,
                               data=data,
                               schema_selectors=(
                                    {'name': 'organization',
                                     'value': project.organization,
                                     'selector': project.organization.id},
                                    {'name': 'project',
                                     'value': project,
                                     'selector': project.id}
                               ))
        form.is_valid()
        form.save()

        assert Party.objects.filter(project=project).count() == 1
        party = Party.objects.filter(project=project).first()
        assert party.attributes.get('fname') == 'test'


class TenureRelationshipEditFormTest(UserTestCase):
    def test_init(self):
        form = forms.TenureRelationshipEditForm(schema_selectors=())
        tenuretypes = sorted(
            TenureRelationshipType.objects.values_list('id', 'label')
        )
        assert len(tenuretypes) > 0
        assert list(form.fields['tenure_type'].choices) == list(tenuretypes)
