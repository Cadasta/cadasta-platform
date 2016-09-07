from shapely.geometry import LineString, Point, Polygon
from shapely.wkt import dumps

from django.core.exceptions import ValidationError
from django.core.files.storage import get_storage_class
from django.db import transaction
from django.utils.translation import ugettext as _
from party.models import Party, TenureRelationship, TenureRelationshipType
from pyxform.xform2json import XFormToDict
from questionnaires.models import Questionnaire
from resources.models import Resource
from spatial.models import SpatialUnit
from xforms.exceptions import InvalidXMLSubmission
from xforms.models import XFormSubmission


class ModelHelper():
    """
    todo:
    Update storage after upgrading to latest django-buckets
    """

    def __init__(self, *arg):
        self.arg = arg

    def create_models(self, data):
        questionnaire = self.get_questionnaire(
            id_string=data['id'], version=data['version']
        )
        project = questionnaire.project

        if project.current_questionnaire != questionnaire.id:
            raise InvalidXMLSubmission(_('Form out of date'))

        party = self.create_party(
            data=data,
            project=project
        )

        location = self.create_spatial_unit(
            data=data,
            project=project,
            questionnaire=questionnaire,
            party=party
        )

        self.create_tenure_relationship(
            data=data,
            project=project,
            party=party,
            location=location
        )

        return questionnaire, party.id, location.id

    def create_party(self, data, project):
        try:
            party = Party.objects.create(
                project=project,
                name=data['party_name'],
                type=data['party_type'],
                attributes=self.get_attributes(data, 'party')
            )
        except Exception as e:
            raise InvalidXMLSubmission(_(
                "Party error: {}".format(e)))
        return party

    def create_spatial_unit(self, data, project, questionnaire, party=None):
        if 'location_geotrace' in data.keys():
            location_geometry = data['location_geotrace']
            geoshape = False
        elif 'location_geoshape' in data.keys():
            location_geometry = data['location_geoshape']
            geoshape = True
        else:
            location_geometry = data['location_geometry']
            geoshape = False
        try:
            location = SpatialUnit.objects.create(
                project=project,
                type=data['location_type'],
                geometry=self._format_geometry(location_geometry, geoshape),
                attributes=self.get_attributes(data, 'location')
            )
        except Exception as e:
            raise InvalidXMLSubmission(_(
                'Location error: {}'.format(e)))
        return location

    def create_tenure_relationship(self, data, party, location, project):
        try:
            TenureRelationship.objects.create(
                project=project,
                party=party,
                spatial_unit=location,
                tenure_type=TenureRelationshipType.objects.get(
                    id=data['tenure_type']),
                attributes=self.get_attributes(data, 'tenure_relationship')
            )
        except Exception as e:
            raise InvalidXMLSubmission(_(
                "Tenure relationship error: {}".format(e)))

    def add_file_to_resource(self, data, user, project, content_object=None):
        Storage = get_storage_class()
        storage = Storage()
        url = storage.save('resources/' + data.name, data.file.read())
        try:
            resource = Resource.objects.create(
                name=data.name,
                file=url,
                content_object=content_object,
                mime_type=data.content_type,
                contributor=user,
                project=project,
                original_file=data.name
            )
            resource.full_clean()
        except Exception as e:
            raise InvalidXMLSubmission(_("{}".format(e)))

    def _format_geometry(self, coords, geoshape=False):
        if coords == '':
            return ''
        if '\n' in coords:
            coords = coords.replace('\n', '')
        coords = coords.split(';')
        if (coords[-1] == ''):
            coords.pop()
        # fixes bug in geoshape:
        # Geoshape copies the second point, not the first.
        if geoshape:
            coords.pop()
            coords.append(coords[0])

        if len(coords) > 1:
            points = []
            for coord in coords:
                coord = coord.split(' ')
                coord = [x for x in coord if x]
                latlng = [float(coord[1]),
                          float(coord[0])]
                points.append(tuple(latlng))
            if (coords[0] != coords[-1] or len(coords) == 2):
                return dumps(LineString(points))
            else:
                return dumps(Polygon(points))
        else:
            latlng = coords[0].split(' ')
            latlng = [x for x in latlng if x]
            return dumps(Point(float(latlng[1]), float(latlng[0])))

    def get_questionnaire(self, id_string, version):
        try:
            return Questionnaire.objects.get(
                id_string=id_string, version=int(version)
            )
        except Questionnaire.DoesNotExist:
            raise ValidationError(_('Questionnaire not found.'))

    def get_attributes(self, data, model_type):
        attributes = {}
        for attr_group in data:
            if '{model}_attributes'.format(model=model_type) in attr_group:
                for item in data[attr_group]:
                    attributes[item] = data[attr_group][item]
        return attributes

    # ~~~~~~~~~~~~~~~
    # To Do:
    # Add location<->location and party<->party relationship
    # ~~~~~~~~~~~~~~~
    def upload_submission_data(self, request):
        if 'xml_submission_file' not in request.data.keys():
            raise InvalidXMLSubmission(_('XML submission not found'))

        xml_submission_file = request.data['xml_submission_file'].read()
        full_submission = XFormToDict(
            xml_submission_file.decode('utf-8')
        ).get_dict()

        submission = full_submission[list(full_submission.keys())[0]]

        with transaction.atomic():
            questionnaire, party, location = self.create_models(submission)
            location_photo = submission.get('location_photo', None)
            party_photo = submission.get('party_photo', None)

            resource_data = {
                'project': questionnaire.project,
                'location_photo': location_photo,
                'location': location,
                'party_photo': party_photo,
                'party_id': party
            }
            self.upload_files(request, resource_data)

        return XFormSubmission(
            json_submission=full_submission,
            user=request.user,
            questionnaire=questionnaire)

    def upload_files(self, request, data):
        user = request.user
        files = request.FILES
        files.pop('xml_submission_file')
        project = data['project']
        for file_name in files:
            content_object = None
            if file_name == data['location_photo']:
                content_object = SpatialUnit.objects.get(
                    id=data['location'])
            elif file_name == data['party_photo']:
                content_object = Party.objects.get(
                    id=data['party_id'])

            self.add_file_to_resource(data=files[file_name],
                                      user=user,
                                      project=project,
                                      content_object=content_object)
