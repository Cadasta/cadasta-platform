import json
from django.db import models
from django.contrib.postgres.fields import JSONField
from core.models import RandomIDModel
from questionnaires.models import Questionnaire
from accounts.models import User


class XFormSubmission(RandomIDModel):
    json_submission = JSONField(default={}, null=False)
    user = models.ForeignKey(User, related_name='submissions', null=False)
    questionnaire = models.ForeignKey(
        Questionnaire, null=False, related_name='submissions')

    def __repr__(self):
        repr_string = ('<XFormSubmission id={obj.id}'
                       ' user={obj.user.username}'
                       ' questionnaire={obj.questionnaire.title}'
                       ' json_submission={json}>')
        return repr_string.format(obj=self,
                                  json=json.dumps(self.json_submission))
