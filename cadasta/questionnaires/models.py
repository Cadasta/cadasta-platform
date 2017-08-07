import hashlib
from datetime import datetime
from buckets.fields import S3FileField
from core.models import RandomIDModel
from django.db import models
from django.utils.translation import ugettext as _
from django.utils.translation import get_language
from django.contrib.postgres.fields import JSONField
from simple_history.models import HistoricalRecords
from tutelary.decorators import permissioned_model

from . import managers, messages, choices


class MultilingualLabelsMixin:
    @property
    def default_language(self):
        if not hasattr(self, '_default_language'):
            if hasattr(self, 'questionnaire'):
                q = self.questionnaire
            else:
                q = self.get_questionnaire()
            self._default_language = q.default_language
        return self._default_language

    @property
    def label(self):
        if isinstance(self.label_xlat, dict):
            return self.label_xlat.get(
                get_language(),
                self.label_xlat[self.default_language]
            )
        else:
            return self.label_xlat

    @label.setter
    def label(self, value):
        self.label_xlat = value


@permissioned_model
class Questionnaire(RandomIDModel):
    filename = models.CharField(max_length=100)
    title = models.CharField(max_length=500)
    id_string = models.CharField(max_length=50)
    default_language = models.CharField(max_length=3, null=True)
    xls_form = S3FileField(upload_to='xls-forms')
    xml_form = S3FileField(upload_to='xml-forms', default=False)
    original_file = models.CharField(max_length=200, null=True)
    project = models.ForeignKey('organization.Project',
                                related_name='questionnaires')
    version = models.BigIntegerField()
    md5_hash = models.CharField(max_length=50, default=False)

    objects = managers.QuestionnaireManager()
    history = HistoricalRecords()

    class Meta:
        unique_together = ('project', 'id_string', 'version')

    class TutelaryMeta:
        perm_type = 'questionnaire'
        path_fields = ('project', 'pk')
        actions = (
            ('questionnaire.view',
             {'description': _("View the questionnaire of the project"),
              'error_message': messages.QUESTIONNAIRE_VIEW,
              'permissions_object': 'project'}),
            ('questionnaire.add',
             {'description': _("Add a questionnaire to the project"),
              'error_message': messages.QUESTIONNAIRE_ADD,
              'permissions_object': 'project'}),
            ('questionnaire.edit',
             {'description': _("Edit an existing questionnaire"),
              'error_message': messages.QUESTIONNAIRE_EDIT,
              'permissions_object': 'project'}),
        )

    def __repr__(self):
        repr_string = ('<Questionnaire id={obj.id} title={obj.title}'
                       ' project={obj.project.slug}>')
        return repr_string.format(obj=self)

    def save(self, *args, **kwargs):
        if not self.id and not self.version:
            self.version = int(
                datetime.utcnow().strftime('%Y%m%d%H%M%S%f')[:-4])

        if not self.id and not self.md5_hash:
            string = (str(self.filename) + str(self.id_string) +
                      str(self.version))
            self.md5_hash = hashlib.md5(string.encode()).hexdigest()

        return super().save(*args, **kwargs)


class QuestionGroup(MultilingualLabelsMixin, RandomIDModel):
    class Meta:
        ordering = ('index',)

    name = models.CharField(max_length=100)
    label_xlat = JSONField(default={})
    relevant = models.CharField(max_length=100, null=True, blank=True)
    questionnaire = models.ForeignKey(Questionnaire,
                                      related_name='question_groups')
    question_group = models.ForeignKey('QuestionGroup',
                                       related_name='question_groups',
                                       null=True)
    type = models.CharField(max_length=50, default='group')
    index = models.IntegerField(null=True)

    objects = managers.QuestionGroupManager()

    history = HistoricalRecords()

    def __repr__(self):
        repr_string = ('<QuestionGroup id={obj.id} name={obj.name}'
                       ' questionnaire={obj.questionnaire.id}>')
        return repr_string.format(obj=self)


class Question(MultilingualLabelsMixin, RandomIDModel):
    class Meta:
        ordering = ('index',)

    name = models.CharField(max_length=100)
    label_xlat = JSONField(default={})
    type = models.CharField(max_length=2, choices=choices.QUESTION_TYPES)
    required = models.BooleanField(default=False)
    default = models.CharField(max_length=100, null=True, blank=True)
    hint = models.CharField(max_length=2500, null=True, blank=True)
    relevant = models.CharField(max_length=100, null=True, blank=True)
    constraint = models.CharField(max_length=50, null=True, blank=True)
    questionnaire = models.ForeignKey(Questionnaire, related_name='questions')
    question_group = models.ForeignKey(QuestionGroup,
                                       related_name='questions',
                                       null=True)
    index = models.IntegerField(null=True)

    objects = managers.QuestionManager()

    history = HistoricalRecords()

    def __repr__(self):
        repr_string = (
            '<Question id={obj.id} name={obj.name}'
            ' questionnaire={obj.questionnaire.id}'
            ' question_group=' +
            ('{obj.question_group.id}' if self.question_group else 'None') +
            '>'
        )
        return repr_string.format(obj=self)

    @property
    def has_options(self):
        return self.type in ['S1', 'SM']


class QuestionOption(MultilingualLabelsMixin, RandomIDModel):
    class Meta:
        ordering = ('index',)

    def get_questionnaire(self):
        return self.question.questionnaire

    name = models.CharField(max_length=100)
    label_xlat = JSONField(default={})
    index = models.IntegerField(null=False)
    question = models.ForeignKey(Question, related_name='options')

    history = HistoricalRecords()

    def __repr__(self):
        repr_string = ('<QuestionOption id={obj.id} name={obj.name}'
                       ' question={obj.question.id}>')
        return repr_string.format(obj=self)
