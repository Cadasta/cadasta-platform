from shapely.geometry import LineString, Point, Polygon
from shapely.wkt import dumps

from django.core.exceptions import ValidationError
from django.core.files.storage import get_storage_class
from django.db import transaction
from django.utils.translation import ugettext as _
from party.models import Party, TenureRelationship, TenureRelationshipType
from pyxform.xform2json import XFormToDict
from questionnaires.models import Questionnaire, Question
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
        questionnaire = self._get_questionnaire(
            id_string=data['id'], version=data['version']
        )
        project = questionnaire.project

        if project.current_questionnaire != questionnaire.id:
            raise InvalidXMLSubmission(_('Form out of date'))

        party, party_resources = self.create_party(
            data=data,
            project=project
        )

        location, location_resources = self.create_spatial_unit(
            data=data,
            project=project,
            questionnaire=questionnaire,
            party=party
        )

        tenure_resources = self.create_tenure_relationship(
            data=data,
            project=project,
            party=party,
            location=location
        )

        return (questionnaire, party_resources, location_resources,
                tenure_resources)

    def create_party(self, data, project):
        party_objects = []
        party_resources = []
        try:
            party_groups = self._format_repeat(data, ['party'])
            for group in party_groups:
                party = Party.objects.create(
                    project=project,
                    name=group['party_name'],
                    type=group['party_type'],
                    attributes=self._get_attributes(group, 'party')
                )

                party_resources.append(
                    self._get_resource_names(group, party, 'party')
                )
                party_objects.append(party)

        except Exception as e:
            raise InvalidXMLSubmission(_(
                "Party error: {}".format(e)))
        return party_objects, party_resources

    def create_spatial_unit(self, data, project, questionnaire, party=None):
        location_resources = []
        location_objects = []
        try:
            location_group = self._format_repeat(data, ['location'])

            for group in location_group:
                if 'location_geotrace' in group.keys():
                    location_geometry = group['location_geotrace']
                    geoshape = False
                elif 'location_geoshape' in group.keys():
                    location_geometry = group['location_geoshape']
                    geoshape = True
                else:
                    location_geometry = group['location_geometry']
                    geoshape = Question.objects.filter(
                        questionnaire=questionnaire, type='GS').exists()

                location = SpatialUnit.objects.create(
                    project=project,
                    type=group['location_type'],
                    geometry=self._format_geometry(
                        location_geometry,
                        geoshape
                    ),
                    attributes=self._get_attributes(group, 'location')
                )

                location_resources.append(
                    self._get_resource_names(group, location, 'location')
                )
                location_objects.append(location)

        except Exception as e:
            raise InvalidXMLSubmission(_(
                'Location error: {}'.format(e)))
        return location_objects, location_resources

    def create_tenure_relationship(self, data, party, location, project):
        tenure_resources = []
        try:
            if data.get('tenure_type'):
                tenure_group = [data]
            else:
                tenure_group = self._format_repeat(data, ['party', 'location'])

            for p in range(len(party)):
                for l in range(len(location)):
                    t = 0
                    if len(tenure_group) > 1:
                        if p > l:
                            t = p
                        else:
                            t = l
                    tenure = TenureRelationship.objects.create(
                        project=project,
                        party=party[p],
                        spatial_unit=location[l],
                        tenure_type=TenureRelationshipType.objects.get(
                            id=tenure_group[t]['tenure_type']),
                        attributes=self._get_attributes(
                            tenure_group[t],
                            'tenure_relationship')
                        )
                    tenure_resources.append(
                        self._get_resource_names(
                            tenure_group[t], tenure, 'tenure')
                    )

        except Exception as e:
            raise InvalidXMLSubmission(_(
                "Tenure relationship error: {}".format(e)))
        return tenure_resources

    def create_resource(self, data, user, project, content_object=None):
        Storage = get_storage_class()
        file = data.file.read()
        if file == b'':
            Resource.objects.get(
                name=data.name,
                contributor=user,
                mime_type=data.content_type,
                project=project,
                original_file=data.name
            ).content_objects.create(
                content_object=content_object
            )
        else:
            url = Storage().save('resources/' + data.name, file)
            try:
                Resource.objects.create(
                    name=data.name,
                    file=url,
                    content_object=content_object,
                    mime_type=data.content_type,
                    contributor=user,
                    project=project,
                    original_file=data.name
                ).full_clean()
            except Exception as e:
                raise InvalidXMLSubmission(_("{}".format(e)))

    def upload_submission_data(self, request):
        if 'xml_submission_file' not in request.data.keys():
            raise InvalidXMLSubmission(_('XML submission not found'))

        xml_submission_file = request.data['xml_submission_file'].read()
        full_submission = XFormToDict(
            xml_submission_file.decode('utf-8')).get_dict()

        submission = full_submission[list(full_submission.keys())[0]]

        with transaction.atomic():
            questionnaire, party, location, tenure = self.create_models(
                                                                    submission)

            party_submission = [submission]
            location_submission = [submission]
            tenure_submission = [submission]

            if 'party_repeat' in submission:
                party_submission = self._format_repeat(submission, ['party'])
                if 'tenure_type' in party_submission[0]:
                    tenure_submission = party_submission

            elif 'location_repeat' in submission:
                location_submission = self._format_repeat(
                                                    submission, ['location'])
                if 'tenure_type' in location_submission[0]:
                    tenure_submission = location_submission

            party_resources = []
            location_resources = []
            tenure_resources = []

            for group in party_submission:
                party_resources.extend(
                    self._get_resource_files(group, 'party')
                )

            for group in location_submission:
                location_resources.extend(
                    self._get_resource_files(group, 'location')
                )

            for group in tenure_submission:
                tenure_resources.extend(
                    self._get_resource_files(group, 'tenure')
                )

            resource_data = {
                'project': questionnaire.project,
                'location_resources': location_resources,
                'locations': location,
                'party_resources': party_resources,
                'parties': party,
                'tenure_resources': tenure_resources,
                'tenures': tenure,
            }
            self.upload_resource_files(request, resource_data)

        return XFormSubmission(
            json_submission=full_submission,
            user=request.user,
            questionnaire=questionnaire)

    def upload_resource_files(self, request, data):
        user = request.user
        files = request.FILES
        files.pop('xml_submission_file')
        project = data['project']
        for file_name in files:
            if file_name in data['location_resources']:
                for location in data['locations']:
                    if file_name in location['resources']:
                        content_object = SpatialUnit.objects.get(
                            id=location['id'])

                        self.create_resource(data=files[file_name],
                                             user=user,
                                             project=project,
                                             content_object=content_object
                                             )

            elif file_name in data['party_resources']:
                for party in data['parties']:
                    if file_name in party['resources']:
                        content_object = Party.objects.get(
                            id=party['id'])

                        self.create_resource(data=files[file_name],
                                             user=user,
                                             project=project,
                                             content_object=content_object
                                             )

            elif file_name in data['tenure_resources']:
                for tenure in data['tenures']:
                    if file_name in tenure['resources']:
                        content_object = TenureRelationship.objects.get(
                            id=tenure['id'])

                        self.create_resource(data=files[file_name],
                                             user=user,
                                             project=project,
                                             content_object=content_object
                                             )
            else:
                self.create_resource(data=files[file_name],
                                     user=user,
                                     project=project,
                                     content_object=None
                                     )

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

    def _format_repeat(self, data, model_type):
        repeat_group = [data]
        for model in model_type:
            if '{}_repeat'.format(model) in data:
                repeat_group = data['{}_repeat'.format(model)]

        if type(repeat_group) != list:
            repeat_group = [repeat_group]

        return repeat_group

    def _get_questionnaire(self, id_string, version):
        try:
            return Questionnaire.objects.get(
                id_string=id_string, version=int(version)
            )
        except Questionnaire.DoesNotExist:
            raise ValidationError(_('Questionnaire not found.'))

    def _get_attributes(self, data, model_type):
        attributes = {}
        for attr_group in data:
            if '{model}_attributes'.format(model=model_type) in attr_group:
                for item in data[attr_group]:
                    attributes[item] = data[attr_group][item]
        return attributes

    def _get_resource_files(self, data, model_type):
        resources = []
        for file_name in data.keys():
            if ("{}_resource".format(model_type) in file_name or
               "{}_photo".format(model_type) in file_name):
                resources.append(data[file_name])
        return resources

    def _get_resource_names(self, data, model, model_type):
        resources = {'id': model.id, 'resources': []}
        # for legacy xlsforms
        if '{}_photo'.format(model_type) in data.keys():
                    resources['resources'].append(
                        data['{}_photo'.format(model_type)])

        for key in data.keys():
            if '{}_resource'.format(model_type) in key:
                resources['resources'].append(
                    data[key])
        return resources

    # ~~~~~~~~~~~~~~~
    # To Do:
    # Add location<->location and party<->party relationship
    # ~~~~~~~~~~~~~~~
