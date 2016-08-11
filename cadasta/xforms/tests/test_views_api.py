import io
import os

import pytest
from lxml import etree

from accounts.tests.factories import UserFactory
from buckets.test.storage import FakeS3Storage
from core.tests.base_test_case import UserTestCase
from core.tests.util import make_dirs  # noqa
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from organization.models import OrganizationRole
from organization.tests.factories import OrganizationFactory, ProjectFactory
from party.models import Party
from questionnaires.managers import create_attrs_schema
from questionnaires.models import Questionnaire
from questionnaires.tests.factories import (QuestionFactory,
                                            QuestionnaireFactory)
from resources.models import Resource
from rest_framework.test import APIRequestFactory, force_authenticate
from spatial.models import SpatialUnit
from tutelary.models import Role
from xforms.tests.files.test_resources import images, responses

from ..views import api
from .attr_schemas import (default_party_xform_group,
                           individual_party_xform_group, location_xform_group,
                           tenure_relationship_xform_group)

path = os.path.dirname(settings.BASE_DIR)


@pytest.mark.usefixtures('make_dirs')
class XFormListTest(UserTestCase):

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.org = OrganizationFactory.create()
        self.prj = ProjectFactory.create(organization=self.org)
        OrganizationRole.objects.create(
            organization=self.org, user=self.user, admin=True)
        self.url = '/v1/collect/'
        self.superuser_role = Role.objects.get(name='superuser')

    def _get_form(self, form_name):
        storage = FakeS3Storage()
        file = open(
            path + '/questionnaires/tests/files/{}.xlsx'.format(form_name),
            'rb'
        ).read()
        form = storage.save('{}.xlsx'.format(form_name), file)
        return form

    def _get(self, user=None, status=None, project=None):
        if user is None:
            user = self.user

        request = APIRequestFactory().get(self.url)
        force_authenticate(request, user=user)
        response = api.XFormListView.as_view({'get': 'list'})(
            request).render()
        content = response.content.decode('utf-8')

        if status is not None:
            assert response.status_code == status

        return content

    def test_get_xforms(self):
        questionnaire = QuestionnaireFactory.create(
            project=self.prj, xls_form=self._get_form('xls-form'))
        content = self._get(status=200)
        assert questionnaire.md5_hash in content
        assert str(questionnaire.version) in content
        assert questionnaire.xml_form.url in content

    def test_get_xforms_with_unauthroized_user(self):
        user = UserFactory.create()
        questionnaire = QuestionnaireFactory.create(
            project=self.prj, xls_form=self._get_form('xls-form'))
        content = self._get(user=user, status=200)

        assert questionnaire.md5_hash not in content
        assert questionnaire.xml_form.url not in content

    def test_get_xforms_with_superuser(self):
        superuser = UserFactory.create()
        superuser.assign_policies(self.superuser_role)
        questionnaire = QuestionnaireFactory.create(
            project=self.prj, xls_form=self._get_form('xls-form'))
        content = self._get(user=superuser, status=200)

        assert questionnaire.md5_hash in content
        assert questionnaire.xml_form.url in content

    def test_get_xforms_with_no_superuser(self):
        user = UserFactory.create()
        OrganizationRole.objects.create(
            organization=self.org, user=user, admin=False)
        version = 2016072516330112
        q1 = QuestionnaireFactory.create(
            project=self.prj, xls_form=self._get_form('xls-form'),
            version=version, id_string='test_form_1'
        )
        q2 = QuestionnaireFactory.create(
            project=self.prj, xls_form=self._get_form('xls-form'),
            version=version + 1, id_string='test_form_2'
        )
        assert Questionnaire.objects.all().count() == 2
        assert q1.version != q2.version

        content = self._get(user=user, status=200)
        xml = etree.fromstring(content.encode('utf-8'))
        ns = {'xf': 'http://openrosa.org/xforms/xformsList'}
        # expect one xform element in response
        assert len(xml.xpath('.//xf:xform', namespaces=ns)) == 1
        assert xml.find(
            './/xf:xform/xf:version', namespaces=ns
        ).text == str(version + 1)
        assert xml.find(
            './/xf:xform/xf:formID', namespaces=ns
        ).text == 'test_form_2'

    def test_get_without_data(self):
        request = APIRequestFactory().get(self.url)
        force_authenticate(request, user=self.user)
        response = api.XFormListView.as_view({'get': 'list'})(request).render()
        content = response.content.decode('utf-8')
        assert 'formID' not in content
        assert 'downloadUrl' not in content
        assert 'hash' not in content


@pytest.mark.usefixtures('make_dirs')
class XFormSubmissionTest(UserTestCase):

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.org = OrganizationFactory.create()
        self.prj = ProjectFactory.create(organization=self.org)
        self.prj_2 = ProjectFactory.create(organization=self.org)
        OrganizationRole.objects.create(
            organization=self.org, user=self.user, admin=True)
        QuestionnaireFactory.create(
            project=self.prj,
            xls_form=self._get_form('test_standard_questionnaire'),
            filename='test_standard_questionnaire',
            id_string='test_standard_questionnaire',
            version=20160727122110)
        q = QuestionnaireFactory.create(
            project=self.prj_2,
            xls_form=self._get_form('test_standard_questionnaire_2'),
            filename='test_standard_questionnaire_2',
            id_string='test_standard_questionnaire_2',
            version=20160727122111)

        QuestionFactory.create(
            name='location_geometry',
            label='Location of Parcel',
            type='GS',
            questionnaire=q)
        self.url = '/collect/submission/'
        self.superuser_role = Role.objects.get(name='superuser')

        # project 1
        create_attrs_schema(
            project=self.prj, dict=default_party_xform_group,
            content_type=ContentType.objects.get(
                app_label='party', model='party'), errors=[])
        create_attrs_schema(
            project=self.prj, dict=individual_party_xform_group,
            content_type=ContentType.objects.get(
                app_label='party', model='party'), errors=[])
        create_attrs_schema(
            project=self.prj, dict=location_xform_group,
            content_type=ContentType.objects.get(
                app_label='spatial', model='spatialunit'), errors=[])
        create_attrs_schema(
            project=self.prj, dict=tenure_relationship_xform_group,
            content_type=ContentType.objects.get(
                app_label='party', model='tenurerelationship'), errors=[])

        # project 2
        create_attrs_schema(
            project=self.prj_2, dict=default_party_xform_group,
            content_type=ContentType.objects.get(
                app_label='party', model='party'), errors=[])
        create_attrs_schema(
            project=self.prj_2, dict=individual_party_xform_group,
            content_type=ContentType.objects.get(
                app_label='party', model='party'), errors=[])
        create_attrs_schema(
            project=self.prj_2, dict=location_xform_group,
            content_type=ContentType.objects.get(
                app_label='spatial', model='spatialunit'), errors=[])
        create_attrs_schema(
            project=self.prj_2, dict=tenure_relationship_xform_group,
            content_type=ContentType.objects.get(
                app_label='party', model='tenurerelationship'), errors=[])

    def _get_form(self, form_name):
        storage = FakeS3Storage()
        file = open(
            path + '/questionnaires/tests/files/{}.xlsx'.format(form_name),
            'rb'
        ).read()
        form = storage.save('xls-forms/{}.xlsx'.format(form_name), file)
        return form

    def _get_resource(self, form_name):
        storage = FakeS3Storage()
        file = open(
            path + '/xforms/tests/files/{}.jpg'.format(form_name),
            'rb'
        ).read()
        form = storage.save('{}.jpg'.format(form_name), file)
        return form

    def _fake_submission(self, form, image={}):
        # form_response = self._get_form_response('response_test_form')
        data = {}
        if type(image) == dict:
            for i in image:
                file = InMemoryUploadedFile(
                    io.StringIO(image[i]),
                    field_name=i,
                    name='{}.png'.format(i),
                    content_type='image/png',
                    size=len(image[i]),
                    charset='utf-8',
                )
                data[file.name] = file
        else:
            file = InMemoryUploadedFile(
                io.StringIO(image),
                field_name='test_image',
                name='test_image.png',
                content_type='image/png',
                size=len(image),
                charset='utf-8',
            )
            data[file.name] = file

        form = InMemoryUploadedFile(
            io.StringIO(form),
            field_name='test_standard_questionnaire',
            name='test_standard_questionnaire.xml',
            content_type='text/xml',
            size=len(form),
            charset='utf-8',
        )
        data['xml_submission_file'] = form
        return data

    def _invalid_submission(self, form=None):
        form = InMemoryUploadedFile(
            io.StringIO(form),
            field_name='test_standard_questionnaire',
            name='test_standard_questionnaire.xml',
            content_type='text/xml',
            size=len(form),
            charset='utf-8',
        )
        return {form.name: form}

    def _post(self, status, form=None, user=None, image={}, valid=True):
        if user is None:
            user = self.user
        if valid:
            form = str.encode(responses[form]).decode('ascii')
            data = self._fake_submission(form=form, image=image)
        else:
            data = self._invalid_submission(form=form)

        request = APIRequestFactory().post(self.url, data)
        force_authenticate(request, user=user)
        response = api.XFormSubmissionViewSet.as_view({'post': 'create'})(
            request).render()
        content = response.content.decode('utf-8')

        if status is not None:
            assert response.status_code == status
        return content

    def test_survey_upload(self):
        self._post(form='form',
                   image=images['test_image'],
                   status=201)
        assert Party.objects.filter(name='Bilbo Baggins').exists()
        assert SpatialUnit.objects.filter(
            attributes={'name': 'Middle Earth'}).exists()

        party = Party.objects.get(name='Bilbo Baggins')
        location = SpatialUnit.objects.get(attributes={'name': 'Middle Earth'})

        assert location in party.tenure_relationships.all()
        assert Resource.objects.filter(name__contains='test_image').exists()
        assert location.resources[0] == Resource.objects.get(
            name__contains='test_image')
        assert len(party.resources) == 0

    def test_multiple_resource_upload(self):
        self._post(form='form_2',
                   image=images,
                   status=201)
        assert Party.objects.filter(name='Bilbo Baggins').exists()
        assert SpatialUnit.objects.filter(
            attributes={'name': 'Middle Earth'}).exists()

        party = Party.objects.get(name='Bilbo Baggins')
        location = SpatialUnit.objects.get(attributes={'name': 'Middle Earth'})

        assert location in party.tenure_relationships.all()
        assert Resource.objects.filter(name__contains='test_image').exists()
        assert Resource.objects.filter(name__contains='this-is-fine').exists()
        assert location.resources[0] == Resource.objects.get(
            name__contains='test_image')
        assert party.resources[0] == Resource.objects.get(
            name__contains='this-is-fine')

    def test_invalid_resource_upload(self):
        # testing submitting with a missing xml_submission_file
        self._post(form=images['test_image'], status=400, valid=False)
        assert not SpatialUnit.objects.filter(
            attributes={'name': 'Null Island'}).exists()

    def test_geometry_upload(self):
        self._post(form='line_form', status=201)
        self._post(form='poly_form', status=201)
        self._post(form='missing_semi_form', status=201)
        self._post(form='geoshape_form', status=201)
        polygon = SpatialUnit.objects.get(attributes={'name': 'Polygon'})
        line = SpatialUnit.objects.get(attributes={'name': 'Line'})
        point = SpatialUnit.objects.get(attributes={'name': 'Missing Semi'})
        geoshape = SpatialUnit.objects.get(attributes={'name': 'Geoshape'})

        assert polygon.geometry.geom_type == 'Polygon'
        assert line.geometry.geom_type == 'LineString'
        assert point.geometry.geom_type == 'Point'
        assert geoshape.geometry.geom_type == 'Polygon'

    def test_questionnaire_not_found(self):
        with pytest.raises(ValidationError):
            self._post(form='bad_questionnaire',
                       image=images,
                       status=400)

    def test_no_content_head(self):
        request = APIRequestFactory().head(self.url)
        force_authenticate(request, user=self.user)
        response = api.XFormSubmissionViewSet.as_view({'head': 'create'})(
            request).render()

        assert response.status_code == 204

    def test_form_not_current_questionnaire(self):
        # update the default form to a new version
        QuestionnaireFactory.create(
            project=self.prj,
            xls_form=self._get_form('test_standard_questionnaire'),
            filename='test_standard_questionnaire_updated',
            id_string='test_standard_questionnaire',
            version=20160727122111
        )
        self._post(form='form', status=410)
