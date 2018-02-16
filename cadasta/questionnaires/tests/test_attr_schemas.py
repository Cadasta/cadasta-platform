import pytest

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase
from jsonattrs.models import Attribute, Schema
from core.tests.utils.cases import UserTestCase, FileStorageTestCase
from core.tests.utils.files import make_dirs  # noqa
from organization.tests.factories import ProjectFactory
from party.tests.factories import (PartyFactory, PartyRelationshipFactory,
                                   TenureRelationshipFactory)
from spatial.tests.factories import (SpatialRelationshipFactory,
                                     SpatialUnitFactory)

from .. import models
from ..managers import create_attrs_schema, get_attr_type_ids
from ..exceptions import InvalidQuestionnaire
from .attr_schemas import (location_xform_group,
                           party_relationship_xform_group,
                           individual_party_xform_group)
from .factories import QuestionnaireFactory


@pytest.mark.usefixtures('make_dirs')
class CreateAttributeSchemaTest(UserTestCase, FileStorageTestCase, TestCase):
    def test_create_attribute_schemas(self):
        file = self.get_file(
            '/questionnaires/tests/files/xls-form-attrs.xlsx', 'rb')
        form = self.storage.save('xls-forms/xls-form-attrs.xlsx', file.read())
        file.close()
        project = ProjectFactory.create()
        models.Questionnaire.objects.create_from_form(
            xls_form=form,
            project=project
        )
        # test for expected schema and attribute creation
        assert 6 == Schema.objects.all().count()
        assert 10 == Attribute.objects.all().count()

    def test_party_attribute_schema(self):
        project = ProjectFactory.create(name='TestProject')
        QuestionnaireFactory.create(project=project)
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        create_attrs_schema(
            project=project, question_group_dict=individual_party_xform_group,
            content_type=content_type, errors=[],
            attr_type_ids=get_attr_type_ids())
        party = PartyFactory.create(
            name='TestParty', project=project,
            type='IN',
            attributes={
                'homeowner': 'yes',
                'dob': '1980-01-01'
            }
        )
        assert 1 == Schema.objects.all().count()
        schema = Schema.objects.get(content_type=content_type)
        assert schema is not None
        assert schema.selectors == [
            project.organization.pk, project.pk,
            project.current_questionnaire, party.type]
        assert 'homeowner' in party.attributes.attributes
        assert 'dob' in party.attributes.attributes
        assert 'gender' in party.attributes.attributes
        assert 3 == Attribute.objects.filter(schema=schema).count()
        assert party.attributes['homeowner'] == 'yes'
        assert party.attributes['dob'] == '1980-01-01'

    def test_party_invalid_attribute(self):
        project = ProjectFactory.create(name='TestProject')
        QuestionnaireFactory.create(project=project)
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        create_attrs_schema(
            project=project, question_group_dict=individual_party_xform_group,
            content_type=content_type, errors=[],
            attr_type_ids=get_attr_type_ids())
        assert 1 == Schema.objects.all().count()
        with pytest.raises(ValidationError):
            PartyFactory.create(
                name='TestParty', project=project,
                attributes={
                    'invalid_attribute': 'yes',
                    'dob': '1980-01-01'
                }
            )

    def test_party_invalid_attribute_type(self):
        project = ProjectFactory.create(name='TestProject')
        QuestionnaireFactory.create(project=project)
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        with pytest.raises(InvalidQuestionnaire) as e:
            create_attrs_schema(
                project=project,
                question_group_dict=individual_party_xform_group,
                content_type=content_type, errors=[], attr_type_ids={})
        assert e.value.errors == [
            "'select_one' (found in the 'gender' question) is not a "
            "supported attribute type."]

    def test_spatial_unit_attribute_schema(self):
        project = ProjectFactory.create(name='TestProject')
        QuestionnaireFactory.create(project=project)
        content_type = ContentType.objects.get(
            app_label='spatial', model='spatialunit')
        create_attrs_schema(
            project=project, question_group_dict=location_xform_group,
            content_type=content_type, errors=[],
            attr_type_ids=get_attr_type_ids())
        spatial_unit = SpatialUnitFactory.create(
            project=project,
            attributes={
                'quality': 'polygon_high',
                'infrastructure': ['water', 'food']
            }
        )
        assert 1 == Schema.objects.all().count()
        schema = Schema.objects.get(content_type=content_type)
        assert schema is not None
        assert schema.selectors == [
            project.organization.pk, project.pk, project.current_questionnaire]
        assert 'quality' in spatial_unit.attributes.attributes
        assert 'polygon_high' == spatial_unit.attributes['quality']
        assert 'infrastructure' in spatial_unit.attributes.attributes
        assert 'water' in spatial_unit.attributes['infrastructure']
        # notes field is omitted in xform
        assert 'notes' not in spatial_unit.attributes.attributes

    def test_spatial_unit_invalid_attribute(self):
        project = ProjectFactory.create(name='TestProject')
        QuestionnaireFactory.create(project=project)
        content_type = ContentType.objects.get(
            app_label='spatial', model='spatialunit')
        create_attrs_schema(
            project=project, question_group_dict=location_xform_group,
            content_type=content_type, errors=[],
            attr_type_ids=get_attr_type_ids())
        assert 1 == Schema.objects.all().count()
        with pytest.raises(ValidationError):
            SpatialUnitFactory.create(
                project=project,
                attributes={
                    'invalid_attribute': 'yes',
                }
            )

    def test_spatial_relationship_schema(self):
        project = ProjectFactory.create(name='TestProject')
        QuestionnaireFactory.create(project=project)
        content_type = ContentType.objects.get(
            app_label='spatial', model='spatialrelationship')
        create_attrs_schema(
            project=project, content_type=content_type, errors=[],
            question_group_dict=party_relationship_xform_group,
            attr_type_ids=get_attr_type_ids())
        sur = SpatialRelationshipFactory.create(
            project=project, attributes={
                'notes': 'Some additional textual info'}
        )
        assert 1 == Schema.objects.all().count()
        schema = Schema.objects.get(content_type=content_type)
        assert schema is not None
        assert schema.selectors == [
            project.organization.pk, project.pk, project.current_questionnaire]
        assert 'notes' in sur.attributes.attributes

    def test_spatial_relationship_invalid_attribute(self):
        project = ProjectFactory.create(name='TestProject')
        QuestionnaireFactory.create(project=project)
        content_type = ContentType.objects.get(
            app_label='spatial', model='spatialrelationship')
        create_attrs_schema(
            project=project, content_type=content_type, errors=[],
            question_group_dict=party_relationship_xform_group,
            attr_type_ids=get_attr_type_ids())
        assert 1 == Schema.objects.all().count()
        with pytest.raises(ValidationError):
            SpatialRelationshipFactory.create(
                project=project,
                attributes={
                    'invalid_attribute': 'yes',
                }
            )

    def test_party_relationship_schema(self):
        project = ProjectFactory.create(name='TestProject')
        QuestionnaireFactory.create(project=project)
        content_type = ContentType.objects.get(
            app_label='party', model='partyrelationship')
        create_attrs_schema(
            project=project, content_type=content_type, errors=[],
            question_group_dict=party_relationship_xform_group,
            attr_type_ids=get_attr_type_ids())
        pr = PartyRelationshipFactory.create(
            project=project, attributes={
                'notes': 'Some additional textual info'}
        )
        assert 1 == Schema.objects.all().count()
        schema = Schema.objects.get(content_type=content_type)
        assert schema is not None
        assert schema.selectors == [
            project.organization.pk, project.pk, project.current_questionnaire]
        assert 'notes' in pr.attributes.attributes

    def test_party_relationship_invalid_attribute(self):
        project = ProjectFactory.create(name='TestProject')
        QuestionnaireFactory.create(project=project)
        content_type = ContentType.objects.get(
            app_label='party', model='partyrelationship')
        create_attrs_schema(
            project=project, content_type=content_type, errors=[],
            question_group_dict=party_relationship_xform_group,
            attr_type_ids=get_attr_type_ids())
        assert 1 == Schema.objects.all().count()
        with pytest.raises(ValidationError):
            PartyRelationshipFactory.create(
                project=project,
                attributes={
                    'invalid_attribute': 'yes',
                }
            )

    def test_tenure_relationship_schema(self):
        project = ProjectFactory.create(name='TestProject')
        QuestionnaireFactory.create(project=project)
        content_type = ContentType.objects.get(
            app_label='party', model='tenurerelationship')
        create_attrs_schema(
            project=project, content_type=content_type, errors=[],
            question_group_dict=party_relationship_xform_group,
            attr_type_ids=get_attr_type_ids())
        tr = TenureRelationshipFactory.create(
            project=project, attributes={
                'notes': 'Some additional textual info'}
        )
        assert 1 == Schema.objects.all().count()
        schema = Schema.objects.get(content_type=content_type)
        assert schema is not None
        assert schema.selectors == [
            project.organization.pk, project.pk, project.current_questionnaire]
        assert 'notes' in tr.attributes.attributes

    def test_tenure_relationship_invalid_attribute(self):
        project = ProjectFactory.create(name='TestProject')
        QuestionnaireFactory.create(project=project)
        content_type = ContentType.objects.get(
            app_label='party', model='tenurerelationship')
        create_attrs_schema(
            project=project, content_type=content_type, errors=[],
            question_group_dict=party_relationship_xform_group,
            attr_type_ids=get_attr_type_ids())
        assert 1 == Schema.objects.all().count()
        with pytest.raises(ValidationError):
            TenureRelationshipFactory.create(
                project=project,
                attributes={
                    'invalid_attribute': 'yes',
                }
            )

    def test_omit_attribute(self):
        project = ProjectFactory.create(name='TestProject')
        QuestionnaireFactory.create(project=project)
        content_type = ContentType.objects.get(
            app_label='spatial', model='spatialunit')
        create_attrs_schema(
            project=project, question_group_dict=location_xform_group,
            content_type=content_type, errors=[],
            attr_type_ids=get_attr_type_ids())
        with pytest.raises(ValidationError):
            SpatialUnitFactory.create(
                project=project,
                attributes={
                    'notes': 'Some textual content',
                }
            )

    def test_required_attribute(self):
        project = ProjectFactory.create(name='TestProject')
        QuestionnaireFactory.create(project=project)
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        create_attrs_schema(
            project=project, question_group_dict=individual_party_xform_group,
            content_type=content_type, errors=[],
            attr_type_ids=get_attr_type_ids())
        # with pytest.raises(ValidationError):
        #     PartyFactory.create(
        #         project=project,
        #         attributes={}
        #     )

        # should raise validation error as dob value is required?
        PartyFactory.create(
            project=project,
            attributes={}
        )
        schema = Schema.objects.get(content_type=content_type)
        attr = Attribute.objects.get(schema=schema, name='dob')
        assert attr.required

    def test_invalid_choice_attribute(self):
        project = ProjectFactory.create(name='TestProject')
        QuestionnaireFactory.create(project=project)
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        create_attrs_schema(
            project=project, question_group_dict=individual_party_xform_group,
            content_type=content_type, errors=[],
            attr_type_ids=get_attr_type_ids())
        assert 1 == Schema.objects.all().count()
        with pytest.raises(ValidationError):
            PartyFactory.create(
                name='TestParty', project=project,
                attributes={
                    'homeowner': 'blah!',
                    'dob': '1980-01-01'
                }
            )

    def test_update_questionnaire_attribute_schema(self):
        file = self.get_file(
            '/questionnaires/tests/files/xls-form-attrs.xlsx', 'rb')
        form = self.storage.save('xls-forms/xls-form.xlsx', file.read())
        file.close()
        project = ProjectFactory.create(name='TestProject')
        q1 = models.Questionnaire.objects.create_from_form(
            xls_form=form,
            project=project
        )

        q2 = models.Questionnaire.objects.create_from_form(
            xls_form=form,
            project=project
        )

        assert 12 == Schema.objects.all().count()

        content_type = ContentType.objects.get(
            app_label='party', model='party')
        assert q1.id != q2.id

        s1 = Schema.objects.get(
            content_type=content_type, selectors=(
                project.organization.pk, project.pk, q1.id)
        )
        assert s1 is not None
        s2 = Schema.objects.get(
            content_type=content_type, selectors=(
                project.organization.pk, project.pk,
                project.current_questionnaire)
        )
        assert s2 is not None
        assert s1 != s2


@pytest.mark.usefixtures('make_dirs')
class ConditionalAttributeSchemaTest(UserTestCase, FileStorageTestCase,
                                     TestCase):
    def setUp(self):
        super().setUp()
        file = self.get_file(
            '/questionnaires/tests/files/xls-form-attrs.xlsx', 'rb')
        form = self.storage.save('xls-forms/xls-form-attrs.xlsx', file.read())
        file.close()
        self.content_type = ContentType.objects.get(
            app_label='party', model='party')
        self.project = ProjectFactory.create(name='TestProject')
        models.Questionnaire.objects.create_from_form(
            xls_form=form,
            project=self.project
        )

    def test_create_party_attribute_schemas(self):
        # should create 3 attribute schemas,
        # one for each of default, individual and group respectively
        schemas = Schema.objects.filter(content_type=self.content_type)
        assert 3 == schemas.count()
        # default schema
        schemas = Schema.objects.filter(
            content_type=self.content_type,
            selectors=(
                self.project.organization.pk, self.project.pk,
                self.project.current_questionnaire
            )
        )
        assert 1 == schemas.count()
        assert 1 == schemas[0].attributes.count()
        # individual schema
        schemas = Schema.objects.filter(
            content_type=self.content_type,
            selectors=(
                self.project.organization.pk, self.project.pk,
                self.project.current_questionnaire, 'IN'
            )
        )
        assert 1 == schemas.count()
        assert 3 == schemas[0].attributes.count()
        # group schema
        schemas = Schema.objects.filter(
            content_type=self.content_type,
            selectors=(
                self.project.organization.pk, self.project.pk,
                self.project.current_questionnaire, 'GR'
            )
        )
        assert 1 == schemas.count()
        assert 2 == schemas[0].attributes.count()

    def test_default_party_attribute_schema(self):
        schema = Schema.objects.get(
            content_type=self.content_type,
            selectors=(self.project.organization.pk, self.project.pk,
                       self.project.current_questionnaire)
        )
        assert schema is not None
        assert 1 == schema.attributes.count()
        party = PartyFactory.create(
            name='TestParty', project=self.project,
            attributes={
                'notes': 'Some textual stuff',
                'dob': '2016-12-01'
            }
        )
        assert 'notes' in party.attributes.attributes
        assert 'Some textual stuff' == party.attributes['notes']

    def test_individual_party_attribute_schema(self):
        schema = Schema.objects.get(
            content_type=self.content_type,
            selectors=(self.project.organization.pk, self.project.pk,
                       self.project.current_questionnaire, 'IN')
        )
        assert schema is not None
        assert 3 == schema.attributes.count()
        party = PartyFactory.create(
            name='TestParty', project=self.project,
            type="IN",
            attributes={
                "notes": "Some notes",
                "gender": "m",
                "dob": "1908-01-01",
                "homeowner": "yes"
            }
        )
        # attribute schema composed from
        # default and individual attribute schemas
        assert 'gender' in party.attributes.attributes
        assert 'homeowner'in party.attributes.attributes
        assert 'notes' in party.attributes.attributes
        assert 'dob' in party.attributes.attributes

    def test_group_party_attribute_schema(self):
        schema = Schema.objects.get(
            content_type=self.content_type,
            selectors=(self.project.organization.pk, self.project.pk,
                       self.project.current_questionnaire, 'GR')
        )
        assert schema is not None
        assert 2 == schema.attributes.count()
        party = PartyFactory.create(
            name='TestParty', project=self.project,
            type="GR",
            attributes={
                "number_of_members": "100",
                "date_formed": "2000-01-01"
            }
        )
        # attribute schema composed from
        # default and group attribute schemas
        assert 'notes' in party.attributes.attributes
        assert 'number_of_members' in party.attributes.attributes
        assert 'date_formed' in party.attributes.attributes
