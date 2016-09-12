import io
import os

import pytest
from lxml import etree

from django.test import TestCase
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from skivvy import APITestCase

from accounts.tests.factories import UserFactory
from core.tests.utils.cases import UserTestCase
from core.tests.utils.files import make_dirs  # noqa
from organization.models import OrganizationRole
from organization.tests.factories import OrganizationFactory, ProjectFactory
from party.models import Party
from questionnaires.managers import create_attrs_schema
from questionnaires.models import Questionnaire
from questionnaires.tests.factories import (QuestionFactory,
                                            QuestionnaireFactory)
from questionnaires.tests.utils import get_form
from resources.models import Resource
from spatial.models import SpatialUnit
from tutelary.models import Role
from xforms.tests.files.test_resources import responses

from ..views import api
from .attr_schemas import (default_party_xform_group,
                           individual_party_xform_group, location_xform_group,
                           tenure_relationship_xform_group)

path = os.path.dirname(settings.BASE_DIR)


@pytest.mark.usefixtures('make_dirs')
class XFormListTest(APITestCase, UserTestCase, TestCase):
    view_class = api.XFormListView
    viewset_actions = {'get': 'list'}

    def setup_models(self):
        self.user = UserFactory.create()
        self.org = OrganizationFactory.create()
        self.prj = ProjectFactory.create(organization=self.org)
        self.superuser_role = Role.objects.get(name='superuser')

    def _get_questionnaire(self, id=None, version=None):
        form = get_form('xls-form')

        kwargs = {'project': self.prj, 'xls_form': form}
        if id:
            kwargs.update({'id_string': id})
        if version:
            kwargs.update({'version': version})

        return QuestionnaireFactory.create(**kwargs)

    def test_get_xforms(self):
        OrganizationRole.objects.create(
            organization=self.org, user=self.user, admin=True)
        questionnaire = self._get_questionnaire()
        response = self.request(user=self.user)

        assert response.status_code == 200
        assert questionnaire.md5_hash in response.content
        assert questionnaire.xml_form.url in response.content
        assert str(questionnaire.version) in response.content

    def test_get_xforms_with_unauthroized_user(self):
        questionnaire = self._get_questionnaire()
        response = self.request(user=self.user)

        assert response.status_code == 200
        assert questionnaire.md5_hash not in response.content
        assert questionnaire.xml_form.url not in response.content

    def test_get_xforms_with_superuser(self):
        self.user.assign_policies(self.superuser_role)
        questionnaire = self._get_questionnaire()
        response = self.request(user=self.user)

        assert response.status_code == 200
        assert questionnaire.md5_hash in response.content
        assert questionnaire.xml_form.url in response.content

    def test_get_xforms_with_no_superuser(self):
        OrganizationRole.objects.create(
            organization=self.org, user=self.user, admin=False)
        q1 = self._get_questionnaire(id='form_1', version=2016072516330112)
        q2 = self._get_questionnaire(id='form_2', version=2016072516330113)
        assert Questionnaire.objects.all().count() == 2
        assert q1.version != q2.version

        response = self.request(user=self.user)
        assert response.status_code == 200
        print(response.content)

        xml = etree.fromstring(response.content.encode('utf-8'))
        ns = {'xf': 'http://openrosa.org/xforms/xformsList'}
        # expect one xform element in response
        assert len(xml.xpath('.//xf:xform', namespaces=ns)) == 1
        assert xml.find(
            './/xf:xform/xf:version', namespaces=ns).text == '2016072516330113'
        assert xml.find(
            './/xf:xform/xf:formID', namespaces=ns).text == 'form_2'

    def test_get_without_data(self):
        OrganizationRole.objects.create(
            organization=self.org, user=self.user, admin=True)
        response = self.request(user=self.user)
        assert 'formID' not in response
        assert 'downloadUrl' not in response
        assert 'hash' not in response


class XFormSubmissionTest(APITestCase, UserTestCase, TestCase):
    view_class = api.XFormSubmissionViewSet
    viewset_actions = {'post': 'create', 'head': 'create'}

    def setup_models(self):
        self.user = UserFactory.create()
        self.org = OrganizationFactory.create()
        self.prj = ProjectFactory.create(organization=self.org)
        self.prj_2 = ProjectFactory.create(organization=self.org)
        self.prj_3 = ProjectFactory.create(organization=self.org)

        OrganizationRole.objects.create(
            organization=self.org, user=self.user, admin=True)

        QuestionnaireFactory.create(
            project=self.prj,
            xls_form=get_form('test_standard_questionnaire'),
            filename='test_standard_questionnaire',
            id_string='test_standard_questionnaire',
            version=20160727122110)

        questionnaire = QuestionnaireFactory.create(
            project=self.prj_2,
            xls_form=get_form('test_standard_questionnaire_2'),
            filename='test_standard_questionnaire_2',
            id_string='test_standard_questionnaire_2',
            version=20160727122111)

        QuestionFactory.create(
            name='location_geometry',
            label='Location of Parcel',
            type='GS',
            questionnaire=questionnaire)

        QuestionnaireFactory.create(
            project=self.prj_3,
            xls_form=get_form('test_standard_questionnaire_bad'),
            filename='test_standard_questionnaire_bad',
            id_string='test_standard_questionnaire_bad',
            version=20160727122112)

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

    def _get_resource(self, file_name, file_type):
        file = open(
            path + '/xforms/tests/files/{}.{}'.format(file_name, file_type),
            'rb'
        ).read()
        return file

    def _make_form_file(self, content):
        return InMemoryUploadedFile(
            io.StringIO(content),
            field_name='test_standard_questionnaire',
            name='test_standard_questionnaire.xml',
            content_type='text/xml',
            size=len(content),
            charset='utf-8',
        )

    def _submission(self, form, image=[], file=False):
        form_content = str.encode(responses[form]).decode('ascii')

        data = {}
        for image_name in image:
            img = self._get_resource(file_name=image_name, file_type='png')
            img = InMemoryUploadedFile(
                file=io.BytesIO(img),
                field_name=image_name,
                name='{}.png'.format(image_name),
                content_type='image/png',
                size=len(img),
                charset='utf-8',
            )
            data[img.name] = img

        if file:
            file = InMemoryUploadedFile(
                io.StringIO(file),
                field_name='test_bad_resource',
                name='test_bad_resource.html',
                content_type='text/html',
                size=len(file),
                charset='utf-8',
            )
            data[file.name] = file

        form_file = self._make_form_file(form_content)
        data['xml_submission_file'] = form_file
        return data

    def _invalid_submission(self, form=None):
        form = self._make_form_file(form)
        return {form.name: form}

    def _getResponseMessage(self, response):
        xml = etree.fromstring(response.content)
        ns = {'or': 'http://openrosa.org/http/response'}
        return xml.find('.//or:message', namespaces=ns).text

    def test_submission_upload(self):
        data = self._submission(form='form',
                                image=['test_image_one', 'test_image_two'])

        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 201

        party = Party.objects.get(name='Bilbo Baggins')
        location = SpatialUnit.objects.get(attributes={'name': 'Middle Earth'})
        assert location in party.tenure_relationships.all()
        assert len(location.resources) == 1
        assert location.resources[0] == Resource.objects.get(
            name__contains='test_image_one')
        assert len(party.resources) == 1
        assert party.resources[0] == Resource.objects.get(
            name__contains='test_image_two')

    def test_line_upload(self):
        data = self._submission(form='line_form')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')

        geom = SpatialUnit.objects.get(attributes={'name': 'Line'})
        assert response.status_code == 201
        assert geom.geometry.geom_type == 'LineString'

    def test_polygon_upload(self):
        data = self._submission(form='poly_form')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')

        geom = SpatialUnit.objects.get(attributes={'name': 'Polygon'})
        assert response.status_code == 201
        assert geom.geometry.geom_type == 'Polygon'

    def test_point_upload(self):
        data = self._submission(form='missing_semi_form')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')

        geom = SpatialUnit.objects.get(attributes={'name': 'Missing Semi'})
        assert response.status_code == 201
        assert geom.geometry.geom_type == 'Point'

    def test_geoshape_upload(self):
        data = self._submission(form='geoshape_form')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')

        geom = SpatialUnit.objects.get(attributes={'name': 'Geoshape'})
        assert response.status_code == 201
        assert geom.geometry.geom_type == 'Polygon'

    def test_invalid_submission_upload(self):
        # testing submitting with a missing xml_submission_file
        data = self._invalid_submission(form='This is not an xml form!')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 400
        msg = self._getResponseMessage(response)
        assert msg == "XML submission not found"

        data = self._submission(form='bad_location_form')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 400
        msg = self._getResponseMessage(response)
        assert msg == "Location error: 'location_type'"

        data = self._submission(form='bad_party_form')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 400
        msg = self._getResponseMessage(response)
        assert msg == "Party error: 'party_name'"

        data = self._submission(form='bad_tenure_form')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 400
        msg = self._getResponseMessage(response)
        assert msg == "Tenure relationship error: 'tenure_type'"

        bad_file = open(
            path + '/xforms/tests/files/test_bad_resource.html',
            'rb'
        ).read()
        bad_file = bad_file.decode('utf-8')

        data = self._submission(form='bad_resource_form',
                                image=['test_image_one'],
                                file=bad_file)
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 400
        msg = self._getResponseMessage(response)
        exp = "{'mime_type': ['Files of type text/html are not accepted.']}"
        assert msg == exp

        assert len(Party.objects.all()) == 0
        assert len(SpatialUnit.objects.all()) == 0
        assert len(Resource.objects.all()) == 0

    def test_anonymous_user(self):
        data = self._submission(form='form')
        response = self.request(method='POST', post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 403

    def test_questionnaire_not_found(self):
        with pytest.raises(ValidationError):
            data = self._submission(form='bad_questionnaire')
            response = self.request(method='POST',
                                    post_data=data,
                                    user=self.user,
                                    content_type='multipart/form-data')
            assert response.status_code == 400

    def test_no_content_head(self):
        response = self.request(method='HEAD', user=self.user)
        assert response.status_code == 204

    def test_form_not_current_questionnaire(self):
        # update the default form to a new version
        QuestionnaireFactory.create(
            project=self.prj,
            xls_form=get_form('test_standard_questionnaire'),
            filename='test_standard_questionnaire_updated',
            id_string='test_standard_questionnaire',
            version=20160727122111
        )
        data = self._submission(form='form')
        response = self.request(method='POST', post_data=data,
                                user=self.user,
                                content_type='multipart/form-data')
        msg = self._getResponseMessage(response)
        assert msg == 'Form out of date'
