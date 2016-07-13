from shapely.geometry import Point, Polygon, LineString
from shapely.wkt import dumps
from django.forms import ValidationError
from django.core.files.storage import get_storage_class

from questionnaires.models import Questionnaire, Question
from party.models import Party, TenureRelationship, TenureRelationshipType
from resources.models import Resource
from spatial.models import SpatialUnit


class ModelHelper():
    """
    todo:
    Update storage after upgrading to latest django-buckets
    """
    def __init__(self, *arg):
        self.arg = arg

    def add_data_to_models(self, data):
        questionnaire = self.get_questionnaire(data=data['id'])
        project = questionnaire.project
        party = self.add_data_to_party(data, project)
        location = self.add_data_to_spatial_unit(data, project, questionnaire)
        self.add_data_to_tenure_relationship(data, party, location, project)
        return {'project': project, 'party': party, 'location': location}

    def add_data_to_party(self, data, project):
        party = Party.objects.create(
            project=project,
            name=data['party_name'],
            type=data['party_type'],
            attributes=self.get_attributes(data, 'party')
        )
        return party

    def add_data_to_spatial_unit(self, data, project, questionnaire):
        geoshape = Question.objects.filter(
             questionnaire=questionnaire, type='GS').exists()
        location = SpatialUnit.objects.create(
            project=project,
            type=data['location_type'],
            geometry=self._format_geometry(
                data['location_geometry'], geoshape),
            attributes=self.get_attributes(data, 'location')
        )
        return location

    def add_data_to_tenure_relationship(self, data, party, location, project):
        TenureRelationship.objects.create(
            project=project,
            party=party,
            spatial_unit=location,
            tenure_type=TenureRelationshipType.objects.get(
                            id=data['tenure_type']),
            attributes=self.get_attributes(data, 'tenure_relationship')
        )

    def add_data_to_resource(self, data, user, project, content_object=None):
        Storage = get_storage_class()
        storage = Storage()
        url = storage.save('resources/' + data.name, data.file.read())

        Resource.objects.create(
            name=data.name,
            file=url,
            content_object=content_object,
            contributor=user,
            project=project
        )

    def _format_geometry(self, coords, geoshape=False):
        if coords == '':
            return ''
        if '\n' in coords:
            coords = coords.replace('\n', '')
        coords = coords.split(';')
        if (coords[-1] == ''):
            coords.pop()
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

    def get_questionnaire(self, data):
        try:
            return Questionnaire.objects.get(name=data)
        except Questionnaire.DoesNotExist:
            try:
                return Questionnaire.objects.get(id_string=data)
            except Questionnaire.DoesNotExist:
                raise ValidationError('Questionnaire not found.')

    def get_attributes(self, data, model_type):
        """
        Used to combine all possible attribute groups together
        based on model type.

        location_attributes_default = {'name': 'whatever'}
        location_attributes_individual = {'foo': 'bar'}

        returned:
            attributes = {'name':'whatever', 'foo':'bar'}
        """
        attributes = {}
        for key in data:
            if '{}_attributes'.format(model_type) in key:
                for item in data[key]:
                    attributes[item] = data[key][item]
        return attributes

    # ~~~~~~~~~~~~~~~
    # Adding location<->location and party<->party relationship's later
    # ~~~~~~~~~~~~~~~

    def upload_files(self, data, survey):
        user = data.user
        data = data.FILES
        project = self.get_questionnaire(data=survey['formid']).project
        for i in data:
            content_object = None
            if i != 'xml_submission_file':
                if i == survey['location_photo']:
                    content_object = SpatialUnit.objects.get(
                                    id=survey['location'])
                elif i == survey['party_photo']:
                    content_object = Party.objects.get(
                                    id=survey['party'])

                self.add_data_to_resource(data=data[i],
                                          user=user,
                                          project=project,
                                          content_object=content_object)
