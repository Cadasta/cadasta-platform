import json
import io

import pytest
from lxml import etree

from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile
from skivvy import APITestCase
from tutelary.models import Policy

from accounts.tests.factories import UserFactory
from core.messages import SANITIZE_ERROR
from core.tests.utils.cases import UserTestCase, FileStorageTestCase
from core.tests.utils.files import make_dirs  # noqa
from organization.models import OrganizationRole
from organization.tests.factories import OrganizationFactory, ProjectFactory
from party.models import Party, TenureRelationship
from questionnaires.managers import create_attrs_schema
from questionnaires.models import Questionnaire
from questionnaires.tests.factories import (QuestionFactory,
                                            QuestionnaireFactory)
from resources.models import Resource
from spatial.models import SpatialUnit
from tutelary.models import Role
from xforms.tests.files.test_resources import responses
from xforms.models import XFormSubmission

from ..views import api
from .attr_schemas import (default_party_xform_group,
                           individual_party_xform_group, location_xform_group,
                           tenure_relationship_xform_group)


@pytest.mark.usefixtures('make_dirs')
class XFormListTest(APITestCase, UserTestCase, FileStorageTestCase, TestCase):
    view_class = api.XFormListView
    viewset_actions = {'get': 'list'}
    request_meta = {'SERVER_PROTOCOL': 'HTTP/1.1'}

    def setup_models(self):
        self.user = UserFactory.create()
        self.org = OrganizationFactory.create()
        self.prj = ProjectFactory.create(organization=self.org)
        self.superuser_role = Role.objects.get(name='superuser')

    def _get_questionnaire(self, id=None, version=None):
        form = self.get_form('xls-form')

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
        assert ('/collect/formList/{}/'.format(
                    questionnaire.id) in response.content)
        assert str(questionnaire.version) in response.content

    def test_get_xforms_with_unauthroized_user(self):
        questionnaire = self._get_questionnaire()
        response = self.request(user=self.user)

        assert response.status_code == 200
        assert questionnaire.md5_hash not in response.content
        assert ('/collect/formList/{}/'.format(
                    questionnaire.id) not in response.content)

    def test_get_xforms_with_superuser(self):
        self.user.assign_policies(self.superuser_role)
        questionnaire = self._get_questionnaire()
        response = self.request(user=self.user)

        assert response.status_code == 200
        assert questionnaire.md5_hash in response.content
        assert ('/collect/formList/{}/'.format(
                    questionnaire.id) in response.content)

    def test_get_xforms_with_no_superuser(self):
        OrganizationRole.objects.create(
            organization=self.org, user=self.user, admin=False)
        q1 = self._get_questionnaire(id='form_1', version=2016072516330112)
        q2 = self._get_questionnaire(id='form_2', version=2016072516330113)
        assert Questionnaire.objects.all().count() == 2
        assert q1.version != q2.version

        response = self.request(user=self.user)
        assert response.status_code == 200

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


class XFormSubmissionTest(APITestCase, UserTestCase, FileStorageTestCase,
                          TestCase):
    view_class = api.XFormSubmissionViewSet
    viewset_actions = {'post': 'create', 'head': 'create'}

    def setup_models(self):
        self.user = UserFactory.create()
        self.org = OrganizationFactory.create()
        self.prj = ProjectFactory.create(organization=self.org)

        OrganizationRole.objects.create(
            organization=self.org, user=self.user, admin=True)

    def _create_questionnaire(self, questionnaire_name, version,
                              schema=True):
        questionnaire = QuestionnaireFactory.create(
            project=self.prj,
            xls_form=self.get_form(questionnaire_name),
            filename=questionnaire_name,
            id_string=questionnaire_name,
            version=(20160727122110 + version))

        if schema:
            self._create_attrs_schema(self.prj)

        return questionnaire

    def _create_attrs_schema(self, prj):
        create_attrs_schema(
            project=prj, dict=default_party_xform_group,
            content_type=ContentType.objects.get(
                app_label='party', model='party'), errors=[])
        create_attrs_schema(
            project=prj, dict=individual_party_xform_group,
            content_type=ContentType.objects.get(
                app_label='party', model='party'), errors=[])
        create_attrs_schema(
            project=prj, dict=location_xform_group,
            content_type=ContentType.objects.get(
                app_label='spatial', model='spatialunit'), errors=[])
        create_attrs_schema(
            project=prj, dict=tenure_relationship_xform_group,
            content_type=ContentType.objects.get(
                app_label='party', model='tenurerelationship'), errors=[])

    def _get_resource(self, file_name, file_type):
        file = self.get_file(
            '/xforms/tests/files/{}.{}'.format(file_name, file_type), 'rb')
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

    def _submission(self, form, image=[], audio=[], file=False):
        form_content = str.encode(responses[form]).decode('ascii')

        data = {}
        for image_name in image:
            img_file = self._get_resource(
                file_name=image_name,
                file_type='png')
            img_stream = img_file.read()
            img = InMemoryUploadedFile(
                file=io.BytesIO(img_stream),
                field_name=image_name,
                name='{}.png'.format(image_name),
                content_type='image/png',
                size=len(img_stream),
                charset='utf-8',
            )
            img_file.close()
            data[img.name] = img

        for audio_name in audio:
            audio_file = self._get_resource(
                file_name=audio_name,
                file_type='mp3')
            audio_stream = audio_file.read()
            audio = InMemoryUploadedFile(
                file=io.BytesIO(audio_stream),
                field_name=audio_name,
                name='{}.mp3'.format(audio_name),
                content_type='audio/mp3',
                size=len(audio_stream),
                charset='utf-8',
            )
            data[audio.name] = audio
            audio_file.close()

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

    def _test_resource(self, resource, model):
        assert Resource.objects.get(
            name__contains=resource) in model.resources

    def test_submission_upload(self):
        questionnaire = self._create_questionnaire('t_questionnaire', 0)
        data = self._submission(form='submission',
                                image=['test_image_one',
                                       'test_image_two',
                                       'test_image_three'],
                                audio=['test_audio_one'])

        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 201

        party = Party.objects.get(name='Bilbo Baggins')
        location = SpatialUnit.objects.get(
            attributes={'name': 'Middle Earth',
                        'infrastructure': ['water', 'food', 'electricity']})
        tenure = TenureRelationship.objects.get(party=party)
        assert tenure.spatial_unit == location
        self._test_resource('test_image_one', location)
        self._test_resource('test_image_two', party)
        self._test_resource('test_audio_one', party)
        self._test_resource('test_image_three', tenure)

        response = XFormSubmission.objects.get(user=self.user)
        assert response.questionnaire == questionnaire
        assert ('Bilbo Baggins' in
                response.json_submission['t_questionnaire']['party_name'])

    def test_line_upload(self):
        self._create_questionnaire('t_questionnaire', 0)
        data = self._submission(form='submission_line')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')

        geom = SpatialUnit.objects.get(attributes={'name': 'Line'})
        assert response.status_code == 201
        assert geom.geometry.geom_type == 'LineString'

    def test_polygon_upload(self):
        self._create_questionnaire('t_questionnaire', 0)
        data = self._submission(form='submission_poly',
                                audio=['test_audio_one'])
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')

        assert response.status_code == 201

        geom = SpatialUnit.objects.get(attributes={'name': 'Polygon'})
        assert geom.geometry.geom_type == 'Polygon'

        tenure = TenureRelationship.objects.get(tenure_type='LH')
        self._test_resource('test_audio_one', tenure)

    def test_point_upload(self):
        self._create_questionnaire('t_questionnaire', 0)
        data = self._submission(form='submission_missing_semi')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')

        geom = SpatialUnit.objects.get(attributes={'name': 'Missing Semi'})
        assert response.status_code == 201
        assert geom.geometry.geom_type == 'Point'

    def test_geoshape_upload(self):
        questionnaire = self._create_questionnaire(
            't_questionnaire_geotype_select', 1)
        QuestionFactory.create(
            name='location_geometry',
            label='Location of Parcel',
            type='GS',
            questionnaire=questionnaire)

        data = self._submission(form='submission_geotype_select')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')

        geom = SpatialUnit.objects.get(attributes={'name': 'Geoshape'})
        assert response.status_code == 201
        assert geom.geometry.geom_type == 'Polygon'

    def test_geotrace_as_poly_upload(self):
        questionnaire = self._create_questionnaire(
            't_questionnaire_geotype_select', 1)
        QuestionFactory.create(
            name='location_geometry',
            label='Location of Parcel',
            type='GS',
            questionnaire=questionnaire)

        data = self._submission(form='submission_geotrace_as_poly')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')

        geom = SpatialUnit.objects.get(attributes={'name': 'geotrace_poly'})
        assert response.status_code == 201
        assert geom.geometry.geom_type == 'Polygon'

    def test_geoshape_as_location_geometry_upload(self):
        questionnaire = self._create_questionnaire(
            't_questionnaire_geotype_select', 1)
        QuestionFactory.create(
            name='location_geometry',
            label='Location of Parcel',
            type='GS',
            questionnaire=questionnaire)

        data = self._submission(form='submission_geotype_neither')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')

        geom = SpatialUnit.objects.get(attributes={'name': 'Geoshape'})
        assert response.status_code == 201
        assert geom.geometry.geom_type == 'Polygon'

    def test_invalid_submission_upload(self):
        questionnaire = self._create_questionnaire('t_questionnaire', 0)
        QuestionFactory.create(name='party_name',
                               questionnaire=questionnaire,
                               type='TX')
        # testing submitting with a missing xml_submission_file
        data = self._invalid_submission(form='This is not an xml form!')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 400
        msg = self._getResponseMessage(response)
        assert msg == "XML submission not found"

        data = self._submission(form='submission_bad_location')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 400
        msg = self._getResponseMessage(response)
        assert msg == "Location error: 'location_type'"

        data = self._submission(form='submission_bad_party')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 400
        msg = self._getResponseMessage(response)
        assert msg == "Party error: 'party_name'"

        data = self._submission(form='submission_bad_tenure')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 400
        msg = self._getResponseMessage(response)
        assert msg == "Tenure relationship error: 'tenure_type'"

        data = self._submission(form='submission_not_sane')
        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 400
        msg = self._getResponseMessage(response)
        assert msg == SANITIZE_ERROR

        file = self.get_file(
            '/xforms/tests/files/test_bad_resource.html', 'rb')
        bad_file = file.read().decode('utf-8')
        file.close()

        self._create_questionnaire('t_questionnaire_bad', 2, False)
        data = self._submission(form='submission_bad_resource',
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
        self._create_questionnaire('t_questionnaire', 0)
        data = self._submission(form='submission')
        response = self.request(method='POST', post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 403

    def test_unauthorized_user(self):
        self._create_questionnaire('t_questionnaire', 0)
        data = self._submission(form='submission')
        user = UserFactory.create()
        response = self.request(method='POST', post_data=data, user=user,
                                content_type='multipart/form-data')
        assert response.status_code == 403
        assert ("You don't have permission to contribute data to this project."
                in response.content)

    def test_questionnaire_not_found(self):
        with pytest.raises(ValidationError):
            data = self._submission(form='submission_bad_questionnaire')
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
        self._create_questionnaire('t_questionnaire', 0)
        self._create_questionnaire('t_questionnaire', 1)

        data = self._submission(form='submission')
        response = self.request(method='POST', post_data=data,
                                user=self.user,
                                content_type='multipart/form-data')
        msg = self._getResponseMessage(response)
        assert msg == 'Form out of date'

    def test_form_with_repeat_party(self):
        self._create_questionnaire('t_questionnaire_repeat_party', 3)
        data = self._submission(form='submission_party_repeat',
                                image=['test_image_one',
                                       'test_image_two',
                                       'test_image_three'],
                                audio=['test_audio_one'])

        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')

        data = self._submission(form='submission_party_repeat',
                                image=['test_image_four',
                                       'test_image_five'])

        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 201

        assert Party.objects.all().count() == 2
        assert SpatialUnit.objects.all().count() == 1
        assert TenureRelationship.objects.all().count() == 2
        assert Resource.objects.all().count() == 6

        party_one = Party.objects.get(name='Bilbo Baggins')
        party_two = Party.objects.get(name='Samwise Gamgee')
        location = SpatialUnit.objects.get(type='MI')
        tenure = TenureRelationship.objects.get(party=party_one)
        assert tenure.spatial_unit == location
        self._test_resource('test_audio_one', location)
        self._test_resource('test_image_one', location)
        self._test_resource('test_image_two', party_one)
        self._test_resource('test_image_three', party_one)
        self._test_resource('test_image_four', tenure)
        self._test_resource('test_image_five', party_two)

        assert XFormSubmission.objects.filter(user=self.user).count() == 1

    def test_form_repeat_with_one_party(self):
        self._create_questionnaire('t_questionnaire_repeat_party', 3)
        data = self._submission(form='submission_party_one_repeat',
                                image=['test_image_one',
                                       'test_image_two'])

        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')

        data = self._submission(form='submission_party_one_repeat',
                                image=['test_image_three',
                                       'test_image_four'],
                                audio=['test_audio_one'])

        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 201

        assert Party.objects.all().count() == 1
        assert SpatialUnit.objects.all().count() == 1
        assert TenureRelationship.objects.all().count() == 1
        assert Resource.objects.all().count() == 5

        party = Party.objects.get(name='Bilbo Baggins')
        location = SpatialUnit.objects.get(type='MI')
        tenure = TenureRelationship.objects.get(
            party=party)
        assert tenure.spatial_unit == location
        self._test_resource('test_audio_one', location)
        self._test_resource('test_image_one', location)
        self._test_resource('test_image_two', party)
        self._test_resource('test_image_three', party)
        self._test_resource('test_image_four', tenure)

    def test_form_with_repeat_location(self):
        self._create_questionnaire('t_questionnaire_repeat_location', 4)
        data = self._submission(form='submission_location_repeat',
                                image=['test_image_one',
                                       'test_image_two',
                                       'test_image_three'],
                                audio=['test_audio_one'])

        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')

        data = self._submission(form='submission_location_repeat',
                                image=['test_image_four',
                                       'test_image_five'])

        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 201

        assert Party.objects.all().count() == 1
        assert SpatialUnit.objects.all().count() == 2
        assert TenureRelationship.objects.all().count() == 2
        assert Resource.objects.all().count() == 6

        party = Party.objects.get(name='Bilbo Baggins')
        location_one = SpatialUnit.objects.get(type='MI')
        location_two = SpatialUnit.objects.get(type='CB')
        tenure_one = TenureRelationship.objects.get(
            spatial_unit=location_one)
        assert tenure_one.party == party
        tenure = TenureRelationship.objects.get(
            spatial_unit=location_two)

        assert tenure.party == party
        self._test_resource('test_audio_one', location_one)
        self._test_resource('test_image_one', location_one)
        self._test_resource('test_image_two', tenure_one)
        self._test_resource('test_image_three', location_two)
        self._test_resource('test_image_four', party)
        self._test_resource('test_image_five', party)

    def test_form_repeat_with_one_location(self):
        self._create_questionnaire('t_questionnaire_repeat_location', 4)
        data = self._submission(form='submission_location_one_repeat',
                                image=['test_image_one',
                                       'test_image_two'],
                                audio=['test_audio_one'])

        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')

        data = self._submission(form='submission_location_one_repeat',
                                image=['test_image_four',
                                       'test_image_five'])

        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')

        assert response.status_code == 201

        assert Party.objects.all().count() == 1
        assert SpatialUnit.objects.all().count() == 1
        assert TenureRelationship.objects.all().count() == 1
        assert Resource.objects.all().count() == 5

        party = Party.objects.get(name='Bilbo Baggins')
        location = SpatialUnit.objects.get(type='MI')
        tenure = TenureRelationship.objects.get(
            spatial_unit=location)

        assert tenure.party == party
        self._test_resource('test_audio_one', location)
        self._test_resource('test_image_one', location)
        self._test_resource('test_image_two', tenure)
        self._test_resource('test_image_four', party)
        self._test_resource('test_image_five', party)

    def test_form_repeat_minus_tenure(self):
        self._create_questionnaire('t_questionnaire_repeat_minus_tenure', 5)
        data = self._submission(form='submission_repeat_minus_tenure',
                                image=['test_image_one',
                                       'test_image_two',
                                       'test_image_three'],
                                audio=['test_audio_one'])

        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')

        data = self._submission(form='submission_repeat_minus_tenure',
                                image=['test_image_four',
                                       'test_image_five'])

        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 201

        assert Party.objects.all().count() == 1
        assert SpatialUnit.objects.all().count() == 2
        assert TenureRelationship.objects.all().count() == 2
        assert Resource.objects.all().count() == 6

        party = Party.objects.get(name='Bilbo Baggins')
        location_one = SpatialUnit.objects.get(type='MI')
        location_two = SpatialUnit.objects.get(type='CB')
        tenure_one = TenureRelationship.objects.get(
            spatial_unit=location_one)
        tenure_two = TenureRelationship.objects.get(
            spatial_unit=location_two)
        assert tenure_one.party == party and tenure_two.party == party

        self._test_resource('test_audio_one', location_one)
        self._test_resource('test_image_one', location_one)
        self._test_resource('test_image_two', tenure_one)
        self._test_resource('test_image_two', tenure_two)
        self._test_resource('test_image_three', location_two)
        self._test_resource('test_image_four', party)
        self._test_resource('test_image_five', party)

    def test_form_repeat_party_minus_tenure(self):
        self._create_questionnaire(
            't_questionnaire_repeat_party_minus_tenure', 6)
        data = self._submission(form='submission_repeat_party_minus_tenure',
                                image=['test_image_one',
                                       'test_image_two',
                                       'test_image_three'],
                                audio=['test_audio_one'])

        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')

        data = self._submission(form='submission_repeat_party_minus_tenure',
                                image=['test_image_four',
                                       'test_image_five'])

        response = self.request(method='POST', user=self.user, post_data=data,
                                content_type='multipart/form-data')
        assert response.status_code == 201

        assert Party.objects.all().count() == 2
        assert SpatialUnit.objects.all().count() == 1
        assert TenureRelationship.objects.all().count() == 2
        assert Resource.objects.all().count() == 6

        party_one = Party.objects.get(name='Bilbo Baggins')
        party_two = Party.objects.get(name='Samwise Gamgee')
        location = SpatialUnit.objects.get(type='MI')
        tenure_one = TenureRelationship.objects.get(party=party_one)
        tenure_two = TenureRelationship.objects.get(party=party_two)
        assert tenure_one.spatial_unit == location
        assert tenure_two.spatial_unit == location

        self._test_resource('test_audio_one', location)
        self._test_resource('test_image_one', location)
        self._test_resource('test_image_two', tenure_one)
        self._test_resource('test_image_two', tenure_two)
        self._test_resource('test_image_three', party_one)
        self._test_resource('test_image_four', party_one)
        self._test_resource('test_image_five', party_two)


class XFormDownloadView(APITestCase, UserTestCase, TestCase):
    view_class = api.XFormDownloadView

    def setup_models(self):
        clause = {
            'clause': [
                {
                    'effect': 'allow',
                    'object': ['project/*/*'],
                    'action': ['questionnaire.*']
                }
            ]
        }
        policy = Policy.objects.create(
            name='test-policy',
            body=json.dumps(clause))
        self.user = UserFactory.create()
        self.user.assign_policies(policy)

        self.questionnaire = QuestionnaireFactory.create()

    def setup_url_kwargs(self):
        return {'questionnaire': self.questionnaire.id}

    def test_get_questionnaire_as_xform(self):
        response = self.request(user=self.user)
        assert response.status_code == 200
        assert (response.headers['content-type'][1] ==
                'application/xml; charset=utf-8')
        assert '<{id} id="{id}" version="{v}"/>'.format(
                id=self.questionnaire.id_string,
                v=self.questionnaire.version) in response.content

    def test_get_questionnaire_that_does_not_exist(self):
        response = self.request(user=self.user,
                                url_kwargs={'questionnaire': 'abc'})
        assert response.status_code == 404
        assert '<detail>Questionnaire not found.</detail>' in response.content

    def test_get_questionnaire_with_unauthorized_user(self):
        user = UserFactory.create()
        response = self.request(user=user)
        assert response.status_code == 403
        assert ('<detail>You do not have permission to perform this '
                'action.</detail>' in response.content)

    def test_get_questionnaire_with_authenticated_user(self):
        response = self.request(user=None)
        assert response.status_code == 401
        assert ('<detail>Authentication credentials were '
                'not provided.</detail>' in response.content)
