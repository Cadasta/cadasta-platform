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
        questionnaire = self.get_questionnaire(
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

        return (questionnaire,
                party_resources,
                location_resources,
                tenure_resources)

    def create_party(self, data, project):
        party_objects = []
        party_resources = []
        try:
            if 'party_repeat' in data:
                party_groups = self.format_repeat(data, model_type='party')
            else:
                party_groups = [data]

            for group in party_groups:
                party = Party.objects.create(
                    project=project,
                    name=group['party_name'],
                    type=group['party_type'],
                    attributes=self.get_attributes(group, 'party')
                )
                pr = {'id': party.id, 'resources': []}

                # for legacy xlsforms
                if 'party_photo' in group.keys():
                    pr['resources'].append(
                        group['party_photo'])

                for key in group.keys():
                    if 'party_resource' in key:
                        pr['resources'].append(
                            group[key])

                party_resources.append(pr)
                party_objects.append(party)

        except Exception as e:
            raise InvalidXMLSubmission(_(
                "Party error: {}".format(e)))
        return party_objects, party_resources

    def create_spatial_unit(self, data, project, questionnaire, party=None):
        location_resources = []
        location_objects = []
        try:
            if 'location_repeat' in data.keys():
                location_group = self.format_repeat(
                                                data, model_type='location')
            else:
                location_group = [data]

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
                    attributes=self.get_attributes(
                        group,
                        'location'
                    )
                )
                lr = {'id': location.id, 'resources': []}

                # for legacy xlsforms
                if 'location_photo' in group:
                    lr['resources'].append(
                        group['location_photo'])

                for key in group.keys():
                    if 'location_resource' in key:
                        lr['resources'].append(
                            group[key])

                location_resources.append(lr)
                location_objects.append(location)

        except Exception as e:
            raise InvalidXMLSubmission(_(
                'Location error: {}'.format(e)))
        return location_objects, location_resources

    def create_tenure_relationship(self, data, party, location, project):
        tenure_resources = []
        try:
            tenure_group = False
            if data.get('tenure_type'):
                tenure_group = data

            if 'party_repeat' in data:
                party_group = self.format_repeat(data, model_type='party')

                for i in range(len(party_group)):
                    if not tenure_group:
                        tenure_group = party_group[i]

                    tenure = TenureRelationship.objects.create(
                        project=project,
                        party=party[i],
                        spatial_unit=location[0],
                        tenure_type=TenureRelationshipType.objects.get(
                            id=tenure_group['tenure_type']),
                        attributes=self.get_attributes(
                            tenure_group,
                            'tenure_relationship')
                    )
                    tr = {'id': tenure.id, 'resources': []}

                    for key in tenure_group.keys():
                        if 'tenure_resource' in key:
                            tr['resources'].append(
                                tenure_group[key])

                    tenure_resources.append(tr)
                    if tenure_group != data:
                        tenure_group = False

            elif 'location_repeat' in data:
                location_group = self.format_repeat(
                                                data, model_type='location')
                for i in range(len(location_group)):
                    if not tenure_group:
                        tenure_group = location_group[i]
                    tenure = TenureRelationship.objects.create(
                        project=project,
                        party=party[0],
                        spatial_unit=location[i],
                        tenure_type=TenureRelationshipType.objects.get(
                            id=tenure_group['tenure_type']),
                        attributes=self.get_attributes(
                            tenure_group,
                            'tenure_relationship')
                    )
                    tr = {'id': tenure.id, 'resources': []}

                    for key in tenure_group.keys():
                        if 'tenure_resource' in key:
                            tr['resources'].append(
                                tenure_group[key])

                    tenure_resources.append(tr)
                    if tenure_group != data:
                        tenure_group = False
            else:
                tenure = TenureRelationship.objects.create(
                    project=project,
                    party=party[0],
                    spatial_unit=location[0],
                    tenure_type=TenureRelationshipType.objects.get(
                        id=data['tenure_type']),
                    attributes=self.get_attributes(
                            tenure_group,
                            'tenure_relationship')
                )

                tr = {'id': tenure.id, 'resources': []}

                for key in data.keys():
                    if 'tenure_resource' in key:
                        tr['resources'].append(
                            data[key])

                tenure_resources.append(tr)

        except Exception as e:
            raise InvalidXMLSubmission(_(
                "Tenure relationship error: {}".format(e)))
        return tenure_resources

    def add_file_to_resource(self, data, user, project, content_object=None):
        Storage = get_storage_class()
        storage = Storage()
        file = data.file.read()
        if file == b'':
            resource = Resource.objects.get(name=data.name,
                                            contributor=user,
                                            mime_type=data.content_type,
                                            project=project,
                                            original_file=data.name)
            resource.content_objects.create(content_object=content_object)
        else:
            url = storage.save('resources/' + data.name, file)
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

    def format_repeat(self, data, model_type):
        if type(data['{}_repeat'.format(model_type)]) != list:
            return [data['{}_repeat'.format(model_type)]]
        else:
            return data['{}_repeat'.format(model_type)]

    def get_resources(self, data, model_type):
        resources = []
        for file_name in data.keys():
            if ("{}_resource".format(model_type) in file_name or
               "{}_photo".format(model_type) in file_name):
                resources.append(data[file_name])
        return resources

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
            questionnaire, party, location, tenure = self.create_models(
                                                                    submission)
            party_resources = []
            location_resources = []
            tenure_resources = []

            if 'party_repeat' in submission.keys():
                party_submission = self.format_repeat(submission, 'party')

                location_resources.extend(
                    self.get_resources(submission, 'location')
                )
                if 'tenure_type' in submission.keys():
                    tenure_resources.extend(
                        self.get_resources(submission, 'tenure')
                    )
                for group in party_submission:
                    party_resources.extend(
                        self.get_resources(group, 'party')
                    )
                    if 'tenure_type' in group.keys():
                        tenure_resources.extend(
                            self.get_resources(group, 'tenure')
                        )

            elif 'location_repeat' in submission.keys():
                location_submission = self.format_repeat(
                                                    submission, 'location')

                party_resources.extend(
                    self.get_resources(
                        submission, 'party')
                )
                if 'tenure_type' in submission.keys():
                    tenure_resources.extend(
                        self.get_resources(submission, 'tenure')
                    )
                for group in location_submission:
                    location_resources.extend(
                        self.get_resources(group, 'location')
                    )
                    if 'tenure_type' in group.keys():
                        tenure_resources.extend(
                            self.get_resources(group, 'tenure')
                        )
            else:
                location_resources.extend(
                    self.get_resources(submission, 'location'))
                party_resources.extend(
                    self.get_resources(submission, 'party'))
                tenure_resources.extend(
                    self.get_resources(submission, 'tenure'))

            resource_data = {
                'project': questionnaire.project,
                'location_resources': location_resources,
                'locations': location,
                'party_resources': party_resources,
                'parties': party,
                'tenure_resources': tenure_resources,
                'tenures': tenure,
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
            if file_name in data['location_resources']:
                for location in data['locations']:
                    if file_name in location['resources']:
                        content_object = SpatialUnit.objects.get(
                            id=location['id'])

                        self.add_file_to_resource(data=files[file_name],
                                                  user=user,
                                                  project=project,
                                                  content_object=content_object
                                                  )

            elif file_name in data['party_resources']:
                for party in data['parties']:
                    if file_name in party['resources']:
                        content_object = Party.objects.get(
                            id=party['id'])

                        self.add_file_to_resource(data=files[file_name],
                                                  user=user,
                                                  project=project,
                                                  content_object=content_object
                                                  )

            elif file_name in data['tenure_resources']:
                for tenure in data['tenures']:
                    if file_name in tenure['resources']:
                        content_object = TenureRelationship.objects.get(
                            id=tenure['id'])
                        self.add_file_to_resource(
                            data=files[file_name],
                            user=user,
                            project=project,
                            content_object=content_object
                        )
            else:
                self.add_file_to_resource(data=files[file_name],
                                          user=user,
                                          project=project,
                                          content_object=None
                                          )
