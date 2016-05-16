from django.db import models, transaction
from django.db.models import Max
from django.apps import apps
from django.utils.translation import ugettext as _

from pyxform.xls2json import parse_file_to_json

from .exceptions import InvalidXLSForm


def create_children(children, errors=[], kwargs={}):
    if children:
        for c in children:
            if c.get('type') == 'group':
                model_name = 'QuestionGroup'
            else:
                model_name = 'Question'

            model = apps.get_model('questionnaires', model_name)
            model.objects.create_from_dict(dict=c, errors=errors, **kwargs)


def create_options(options, question, errors=[]):
    if options:
        for o in options:
            QuestionOption = apps.get_model('questionnaires', 'QuestionOption')
            QuestionOption.objects.create(question=question, **o)
    else:
        errors.append(_("Please provide at least one option for field"
                        " '{field_name}'".format(field_name=question.name)))


class QuestionnaireManager(models.Manager):
    def current(self, **kwargs):
        max = self.filter(**kwargs).aggregate(Max('version'))['version__max']
        return self.get(version=max, **kwargs)

    def create_from_form(self, xls_form=None, project=None):
        with transaction.atomic():
            instance = self.model(
                xls_form=xls_form,
                project=project
            )

            json = parse_file_to_json(instance.xls_form.file.name)

            try:
                current = self.current(
                    project=project,
                    name=json.get('name'))
                version = current.version + 1
            except self.model.DoesNotExist:
                version = 1

            instance.name = json.get('name')
            instance.title = json.get('title')
            instance.id_string = json.get('id_string')
            instance.version = version
            instance.save()

            project.current_questionnaire = instance.id
            project.save()

            errors = []

            create_children(
                children=json.get('children'),
                errors=errors,
                kwargs={'questionnaire': instance},
            )

            if errors:
                raise InvalidXLSForm(errors)

            return instance


class QuestionGroupManager(models.Manager):
    def create_from_dict(self, dict=None, questionnaire=None, errors=[]):
        instance = self.model(questionnaire=questionnaire)

        instance.name = dict.get('name')
        instance.label = dict.get('label')
        instance.save()

        create_children(
            children=dict.get('children'),
            errors=errors,
            kwargs={
                'questionnaire': questionnaire,
                'question_group': instance
            }
        )

        return instance


class QuestionManager(models.Manager):
    def create_from_dict(self, errors=[], **kwargs):
        dict = kwargs.pop('dict')
        instance = self.model(**kwargs)

        type_dict = {name: code for code, name in instance.TYPE_CHOICES}

        try:
            instance.type = type_dict[dict.get('type')]
        except KeyError as e:
            errors.append(
                _('{type} is not an accepted question type').format(type=e)
            )

        instance.name = dict.get('name')
        instance.label = dict.get('label')
        instance.required = dict.get('required', False)
        instance.constraint = dict.get('constraint')
        instance.save()

        if instance.has_options:
            create_options(dict.get('choices'), instance, errors=errors)

        return instance
