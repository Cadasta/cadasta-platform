from django.core.management.base import BaseCommand

from organization.models import Project
from xforms.models import XFormSubmission
from resources.models import Resource, ContentObject
from questionnaires.models import Questionnaire


project_slugs = [
    'projet-maji-ya-amani',
    'projet-maji-ya-amani-bloc-mukama',
    'projet-maji-ya-amani-bloc-sango2',
    'projet-maji-ya-amani-bloc-sango3',
    'projet-maji-ya-amani-sango1',
    'projet-maji-ya-amani-v57'
]


def projects():
    for slug in project_slugs:
        yield Project.objects.get(slug=slug)


class Command(BaseCommand):
    def handle(self, *args, **options):
        for p in projects():
            print(p.name)

            questionnaire = Questionnaire.objects.get(
                id=p.current_questionnaire)
            id_string = questionnaire.id_string
            submissions = XFormSubmission.objects.filter(
                questionnaire_id=questionnaire.id)

            for s in submissions:
                submission = s.json_submission[id_string]

                location_photo = submission.get('renco_resource_photo')
                if location_photo:
                    # Using filter here because some images are duplicates
                    res = Resource.objects.filter(original_file=location_photo,
                                                  project_id=p.id).first()
                    location = s.spatial_units.first()

                    if res:
                        ContentObject.objects.create(
                            resource=res,
                            content_object=location
                        )
                    else:
                        print('Resource {} not found.'.format(location_photo))
                        print('- Spatial Unit ID: {}'.format(location.id))

                party_photo = submission.get('id_resource_photo')
                if party_photo:
                    res = Resource.objects.filter(original_file=party_photo,
                                                  project_id=p.id).first()
                    party = s.parties.first()

                    if res:
                        ContentObject.objects.create(
                            resource=res,
                            content_object=party
                        )
                    else:
                        print('Resource {} not found.'.format(party_photo))
                        print('- Party ID: {}'.format(party.id))
            print('Done')
