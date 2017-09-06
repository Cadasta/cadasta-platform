import json
import uuid
from django.db import models
from django.contrib.postgres.fields import JSONField
from core.models import RandomIDModel
from questionnaires.models import Questionnaire
from accounts.models import User
from spatial.models import SpatialUnit
from party.models import Party, TenureRelationship


class XFormSubmission(RandomIDModel):
    json_submission = JSONField(default={}, null=False)
    user = models.ForeignKey(User, related_name='submissions', null=False)
    questionnaire = models.ForeignKey(
        Questionnaire, null=False, related_name='submissions')

    instanceID = models.UUIDField(
        primary_key=False, default=uuid.uuid4, editable=False)

    spatial_units = models.ManyToManyField(
      SpatialUnit, related_name='xform_submissions',
      )

    parties = models.ManyToManyField(
      Party, related_name='xform_submissions',
      )

    tenure_relationships = models.ManyToManyField(
        TenureRelationship, related_name='xform_submissions',
      )

    # Audit history
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __repr__(self):
        repr_string = ('<XFormSubmission id={obj.id}'
                       ' user={obj.user.username}'
                       ' questionnaire={obj.questionnaire.title}'
                       ' json_submission={json}'
                       ' instanceID={obj.instanceID}'
                       ' spatial_units={spatial_units}'
                       ' parties={parties}'
                       ' tenure_relationships={tenure_relationships}>')
        return repr_string.format(
                         obj=self,
                         json=json.dumps(self.json_submission),
                         spatial_units=list(self.spatial_units.all()),
                         parties=list(self.parties.all()),
                         tenure_relationships=list(
                            self.tenure_relationships.all()))
