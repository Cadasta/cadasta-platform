import os
import itertools
import re
import hashlib

from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from django.db import models, transaction
from django.db.models import Max
from django.utils.translation import ugettext as _
from jsonattrs.models import Attribute, AttributeType, Schema
from pyxform.xls2json import parse_file_to_json
from pyxform.builder import create_survey_element_from_dict
from pyxform.errors import PyXFormError

from questionnaires.exceptions import InvalidXLSForm

ATTRIBUTE_GROUPS = {
    'location_attributes': {
        'app_label': 'spatial',
        'model': 'spatialunit'
    },
    'party_attributes': {
        'app_label': 'party',
        'model': 'party'
    },
    'location_relationship_attributes': {
        'app_label': 'spatial',
        'model': 'spatialrelationship'
    },
    'party_relationship_attributes': {
        'app_label': 'party',
        'model': 'partyrelationship'
    },
    'tenure_relationship_attributes': {
        'app_label': 'party',
        'model': 'tenurerelationship'
    }
}


def create_children(children, errors=[], project=None, kwargs={}):
    if children:
        for c in children:
            if c.get('type') == 'group':
                model_name = 'QuestionGroup'

                # parse attribute group
                attribute_group = c.get('name')
                for attr_group in ATTRIBUTE_GROUPS.keys():
                    if attribute_group.startswith(attr_group):
                        app_label = ATTRIBUTE_GROUPS[attr_group]['app_label']
                        model = ATTRIBUTE_GROUPS[attr_group]['model']
                        content_type = ContentType.objects.get(
                            app_label=app_label, model=model)
                        create_attrs_schema(
                            project=project, dict=c,
                            content_type=content_type, errors=errors
                        )
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


def create_attrs_schema(project=None, dict=None, content_type=None, errors=[]):
    fields = []
    selectors = (project.organization.pk, project.pk,
                 project.current_questionnaire)

    # check if the attribute group has a relevant bind statement,
    # eg ${party_type}='IN'
    # this enables conditional attribute schema creation
    bind = dict.get('bind', None)
    if bind:
        relevant = bind.get('relevant', None)
        if relevant:
            clauses = relevant.split('=')
            selector = re.sub("'", '', clauses[1])
            selectors += (selector,)

    schema_obj = Schema.objects.create(content_type=content_type,
                                       selectors=selectors)

    for c in dict.get('children'):
        field = {}
        field['name'] = c.get('name')
        field['long_name'] = c.get('label')
        # HACK: pyxform strips underscores from xform field names
        field['attr_type'] = c.get('type').replace(' ', '_')
        if c.get('default'):
            field['default'] = c.get('default', '')
        if c.get('omit'):
            field['omit'] = c.get('omit')
        bind = c.get('bind')
        if bind:
            field['required'] = True if bind.get(
                'required', 'no') == 'yes' else False
        if c.get('choices'):
            field['choices'] = [choice.get('name')
                                for choice in c.get('choices')]
        fields.append(field)

    for field, index in zip(fields, itertools.count(1)):
        long_name = field.get('long_name', field['name'])
        attr_type = AttributeType.objects.get(name=field['attr_type'])
        choices = field.get('choices', [])
        default = field.get('default', '')
        required = field.get('required', False)
        omit = True if field.get('omit', '') == 'yes' else False
        Attribute.objects.create(
            schema=schema_obj,
            name=field['name'], long_name=long_name,
            attr_type=attr_type, index=index,
            choices=choices, default=default,
            required=required, omit=omit
        )


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
            instance.md5_hash = self.get_hash(
                instance.id_string, instance.version)
            # ignoring pyxform errors to provide more verbose errors later.
            try:
                survey = create_survey_element_from_dict(json)
                xml_form = survey.xml().toprettyxml()
                content = str.encode(xml_form)
                name = os.path.join(instance.xml_form.field.upload_to,
                                    os.path.basename(instance.name))
                url = instance.xml_form.storage.save(
                    '{}.xml'.format(name), content)

                instance.xml_form = url
            except PyXFormError:
                pass
            instance.save()

            project.current_questionnaire = instance.id
            project.save()

            errors = []

            create_children(
                children=json.get('children'),
                errors=errors,
                project=project,
                kwargs={'questionnaire': instance}
            )

            if errors:
                raise InvalidXLSForm(errors)

            return instance

    def get_hash(self, id_string, version):
        string = str(id_string) + str(version)
        return hashlib.md5(string.encode()).hexdigest()


class QuestionGroupManager(models.Manager):

    def create_from_dict(self, dict=None, questionnaire=None, errors=[]):
        instance = self.model(questionnaire=questionnaire)

        instance.name = dict.get('name')
        instance.label = dict.get('label')
        instance.save()

        create_children(
            children=dict.get('children'),
            errors=errors,
            project=questionnaire.project,
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
