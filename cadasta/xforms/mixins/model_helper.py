from django.core.exceptions import ValidationError, PermissionDenied
from django.core.files.storage import get_storage_class
from django.db import transaction
from django.utils.translation import ugettext as _
from jsonattrs.models import Attribute, AttributeType
from tutelary.models import Policy
from party.models import Party, TenureRelationship
from pyxform.xform2json import XFormToDict
from questionnaires.models import Questionnaire, Question
from resources.models import Resource
from spatial.models import SpatialUnit
from xforms.exceptions import InvalidXMLSubmission
from xforms.models import XFormSubmission
from xforms.utils import odk_geom_to_wkt
from core.messages import SANITIZE_ERROR
from core.validators import sanitize_string


def get_policy_instance(policy_name, variables=None):
    return (Policy.objects.get(name=policy_name), variables)


class ModelHelper():
    def __init__(self, *arg):
        self.arg = arg

    def _check_perm(self, user, project):
        superuser = get_policy_instance('superuser')
        org_admin = get_policy_instance('org-admin', {
            'organization': project.organization.slug
        })
        prj_manager = get_policy_instance('project-manager', {
            'organization': project.organization.slug,
            'project': project.slug
        })
        data_collector = get_policy_instance('data-collector', {
            'organization': project.organization.slug,
            'project': project.slug
        })

        roles = [superuser, org_admin, prj_manager, data_collector]
        assigned_policies = user.assigned_policies()
        if not any(role in assigned_policies for role in roles):
            raise PermissionDenied(_("You don't have permission to contribute"
                                     " data to this project."))

    def create_models(self, data, user):
        questionnaire = self._get_questionnaire(
            id_string=data['id'], version=data['version']
        )
        self._check_perm(user, questionnaire.project)

        # If xform has already been submitted, check for additional resources
        additional_resources = self.check_for_duplicate_submission(
                        data, questionnaire)
        if additional_resources:
            return additional_resources

        project = questionnaire.project

        if project.current_questionnaire != questionnaire.id:
            raise InvalidXMLSubmission(_('Form out of date'))

        parties, party_resources = self.create_party(
            data=data,
            project=project
        )

        locations, location_resources = self.create_spatial_unit(
            data=data,
            project=project,
            party=parties
        )

        (tenure_relationships,
            tenure_resources) = self.create_tenure_relationship(
            data=data,
            project=project,
            parties=parties,
            locations=locations
        )

        return (questionnaire,
                parties, party_resources,
                locations, location_resources,
                tenure_relationships, tenure_resources)

    def check_for_duplicate_submission(self, data, questionnaire):
        previous_submission = XFormSubmission.objects.filter(
            instanceID=data['meta']['instanceID']
        )

        if not previous_submission:
            return None

        previous_submission = previous_submission[0]

        party_objects, party_resources = self.create_party(
            data=data,
            project=questionnaire.project,
            duplicate=previous_submission)

        location_objects, location_resources = self.create_spatial_unit(
            data=data,
            project=questionnaire.project,
            duplicate=previous_submission)

        tenure_objects, tenure_resources = self.create_tenure_relationship(
            data=data,
            project=questionnaire.project,
            parties=party_objects,
            locations=location_objects,
            duplicate=previous_submission)

        return (questionnaire,
                party_objects, party_resources,
                location_objects, location_resources,
                tenure_objects, tenure_resources)

    def create_party(self, data, project, duplicate=None):
        party_objects = []
        party_resources = []

        if duplicate:
            get_or_create_party = duplicate.parties.get
        else:
            get_or_create_party = Party.objects.create

        try:
            party_groups = self._format_repeat(data, ['party'])
            for group in party_groups:
                party = get_or_create_party(
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

    def create_spatial_unit(self, data, project,
                            party=None, duplicate=None):
        location_resources = []
        location_objects = []

        if duplicate:
            get_or_create_spatial_units = duplicate.spatial_units.get
        else:
            get_or_create_spatial_units = SpatialUnit.objects.create

        try:
            location_group = self._format_repeat(data, ['location'])

            for group in location_group:
                geom = self._format_geometry(group)
                location = get_or_create_spatial_units(
                    project=project,
                    type=group['location_type'],
                    geometry=geom,
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

    def create_tenure_relationship(self, data, parties, locations, project,
                                   duplicate=None):
        tenure_resources = []
        tenure_objects = []

        if duplicate:
            get_or_create_tenure_rels = duplicate.tenure_relationships.get
        else:
            get_or_create_tenure_rels = TenureRelationship.objects.create

        try:
            if data.get('tenure_type'):
                tenure_group = [data]
            else:
                tenure_group = self._format_repeat(data, ['party', 'location'])

            for p, party in enumerate(parties):
                for l, location in enumerate(locations):
                    t = 0
                    if len(tenure_group) > 1:
                        if p > l:
                            t = p
                        else:
                            t = l
                    tenure = get_or_create_tenure_rels(
                        project=project,
                        party=party,
                        spatial_unit=location,
                        tenure_type=tenure_group[t]['tenure_type'],
                        attributes=self._get_attributes(
                            tenure_group[t],
                            'tenure_relationship')
                    )
                    tenure_objects.append(tenure)
                    tenure_resources.append(
                        self._get_resource_names(
                            tenure_group[t], tenure, 'tenure')
                    )

        except Exception as e:
            raise InvalidXMLSubmission(_(
                "Tenure relationship error: {}".format(e)))
        return tenure_objects, tenure_resources

    def create_resource(self, data, user, project, content_object=None):
        Storage = get_storage_class()
        file = data.file.read()
        try:
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

    def sanitize_submission(self, submission, sanitizable_questions):
        for key, value in submission.items():
            if isinstance(value, dict):
                self.sanitize_submission(value, sanitizable_questions)

            elif key in sanitizable_questions and not sanitize_string(value):
                raise InvalidXMLSubmission(SANITIZE_ERROR)

    def upload_submission_data(self, request):
        if 'xml_submission_file' not in request.data.keys():
            raise InvalidXMLSubmission(_('XML submission not found'))

        xml_submission_file = request.data['xml_submission_file'].read()
        full_submission = XFormToDict(
            xml_submission_file.decode('utf-8')).get_dict()

        submission = full_submission[list(full_submission.keys())[0]]

        sanitizable_questions = Question.objects.filter(
            questionnaire__id=submission['id'],
            questionnaire__version=submission['version'],
            type__in=['TX', 'NO']).values_list('name', flat=True)
        self.sanitize_submission(submission, sanitizable_questions)

        with transaction.atomic():
            (questionnaire,
             parties, party_resources,
             locations, location_resources,
             tenure_relationships, tenure_resources
             ) = self.create_models(submission, request.user)

            party_submissions = [submission]
            location_submissions = [submission]
            tenure_submissions = [submission]

            if 'party_repeat' in submission:
                party_submissions = self._format_repeat(submission, ['party'])
                if 'tenure_type' in party_submissions[0]:
                    tenure_submissions = party_submissions

            elif 'location_repeat' in submission:
                location_submissions = self._format_repeat(
                    submission, ['location']
                )
                if 'tenure_type' in location_submissions[0]:
                    tenure_submissions = location_submissions

            party_resource_files = []
            location_resource_files = []
            tenure_resource_files = []

            for group in party_submissions:
                party_resource_files.extend(
                    self._get_resource_files(group, 'party')
                )

            for group in location_submissions:
                location_resource_files.extend(
                    self._get_resource_files(group, 'location')
                )

            for group in tenure_submissions:
                tenure_resource_files.extend(
                    self._get_resource_files(group, 'tenure')
                )

            resource_data = {
                'project': questionnaire.project,
                'location_resources': location_resource_files,
                'locations': location_resources,
                'party_resources': party_resource_files,
                'parties': party_resources,
                'tenure_resources': tenure_resource_files,
                'tenures': tenure_resources,
            }
            self.upload_resource_files(request, resource_data)

        if XFormSubmission.objects.filter(
                instanceID=submission['meta']['instanceID']).exists():
            return XFormSubmission.objects.get(
                instanceID=submission['meta']['instanceID'])

        xform_submission = XFormSubmission(
            json_submission=full_submission,
            user=request.user,
            questionnaire=questionnaire,
            instanceID=submission['meta']['instanceID']
            )
        return xform_submission, parties, locations, tenure_relationships

    def upload_resource_files(self, request, data):
        user = request.user
        files = request.FILES
        files.pop('xml_submission_file')
        project = data['project']
        for file_name in files:
            args = [data, user, project, files, file_name]

            if file_name in data['location_resources']:
                self._format_create_resource(
                   *args, 'locations', SpatialUnit)

            elif file_name in data['party_resources']:
                self._format_create_resource(
                    *args, 'parties', Party)

            elif file_name in data['tenure_resources']:
                self._format_create_resource(
                    *args, 'tenures', TenureRelationship)

            else:
                self.create_resource(data=files[file_name],
                                     user=user,
                                     project=project,
                                     content_object=None
                                     )

    def _format_repeat(self, data, model_type):
        repeat_group = [data]
        for model in model_type:
            if '{}_repeat'.format(model) in data:
                repeat_group = data['{}_repeat'.format(model)]

        if type(repeat_group) != list:
            repeat_group = [repeat_group]

        return repeat_group

    def _format_geometry(self, data):
        if 'location_geotrace' in data:
            geom = data['location_geotrace']
        elif 'location_geoshape' in data:
            geom = data['location_geoshape']
        else:
            geom = data['location_geometry']
        return odk_geom_to_wkt(geom)

    def _format_create_resource(self, data, user,  project, files, file_name,
                                model_type, model):
        for obj in data[model_type]:
            if file_name in obj['resources']:
                content_object = model.objects.get(
                    id=obj['id'])
                self.create_resource(data=files[file_name],
                                     user=user,
                                     project=project,
                                     content_object=content_object
                                     )

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
                    if Attribute.objects.filter(
                        name=item,
                        attr_type=AttributeType.objects.get(
                            name='select_multiple')).exists():
                        answers = data[attr_group][item].split(' ')
                        attributes[item] = answers
                    else:
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
