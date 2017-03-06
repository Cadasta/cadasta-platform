import itertools
import re
from xml.dom.minidom import Element
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.utils.translation import ugettext as _
from jsonattrs.models import Attribute, AttributeType, Schema
from pyxform.builder import create_survey_element_from_dict
from pyxform.errors import PyXFormError
from pyxform.xls2json import parse_file_to_json
from questionnaires.exceptions import InvalidXLSForm

ATTRIBUTE_GROUPS = settings.ATTRIBUTE_GROUPS


def create_children(children, errors=[], project=None,
                    default_language='', kwargs={}):
    if children:
        for c, idx in zip(children, itertools.count()):
            if c.get('type') in ['group', 'repeat']:
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
                            content_type=content_type,
                            default_language=default_language,
                            errors=errors
                        )
            else:
                model_name = 'Question'

            model = apps.get_model('questionnaires', model_name)
            model.objects.create_from_dict(dict=c,
                                           index=idx,
                                           errors=errors,
                                           **kwargs)


def create_options(options, question, errors=[]):
    if options:
        for o, idx in zip(options, itertools.count()):
            QuestionOption = apps.get_model('questionnaires', 'QuestionOption')

            QuestionOption.objects.create(
                question=question, index=idx+1, name=o['name'],
                label_xlat=o.get('label_xlat', o.get('label', {}))
            )
    else:
        errors.append(_("Please provide at least one option for field"
                        " '{field_name}'".format(field_name=question.name)))


def fix_labels(labels):
    if isinstance(labels, dict):
        return {k: str(v) for k, v in labels.items()}
    else:
        return labels


def create_attrs_schema(project=None, dict=None, content_type=None,
                        default_language='', errors=[]):
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
                                       selectors=selectors,
                                       default_language=default_language)

    for c in dict.get('children'):
        field = {}
        field['name'] = c.get('name')
        field['long_name'] = c.get('label')
        # HACK: pyxform renames select_multiple to select all that apply
        if c.get('type') == 'select all that apply':
            field['attr_type'] = 'select_multiple'
        else:
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
            field['choice_labels'] = [fix_labels(choice.get('label'))
                                      for choice in c.get('choices')]
        fields.append(field)

    for field, index in zip(fields, itertools.count(1)):
        long_name = field.get('long_name', field['name'])
        attr_type = AttributeType.objects.get(name=field['attr_type'])
        choices = field.get('choices', [])
        choice_labels = field.get('choice_labels', None)
        default = field.get('default', '')
        required = field.get('required', False)
        omit = True if field.get('omit', '') == 'yes' else False
        Attribute.objects.create(
            schema=schema_obj,
            name=field['name'], long_name=long_name,
            attr_type=attr_type, index=index,
            choices=choices, choice_labels=choice_labels,
            default=default, required=required, omit=omit
        )


def check_for_language(lang):
    return lang in settings.FORM_LANGS.keys()


def multilingual_label_check(children):
    has_multi = False
    for c in children:
        if 'label' in c and isinstance(c['label'], dict):
            has_multi = True
            for lang in c['label'].keys():
                if lang != 'default' and not check_for_language(lang):
                    raise InvalidXLSForm(
                        ["Label language code '{}' unknown".format(lang)]
                    )
        # Note the order of the short-cut "or" in the following two
        # statements: it's like this to force the recursive call to
        # multilingual_label_check to make sure we check the language
        # codes everywhere, rather than dropping out as soon as we
        # find that the form is multilingual.
        if 'children' in c:
            has_multi = multilingual_label_check(c['children']) or has_multi
        if 'choices' in c:
            has_multi = multilingual_label_check(c['choices']) or has_multi
    return has_multi


def fix_languages(node):
    if (isinstance(node, Element) and
       node.tagName == 'translation' and node.hasAttribute('lang')):
        iso_lang = node.getAttribute('lang')
        local_lang = settings.FORM_LANGS.get(iso_lang)
        node.setAttribute('lang', local_lang)
    else:
        for child in node.childNodes:
            fix_languages(child)


class QuestionnaireManager(models.Manager):

    def create_from_form(self, xls_form=None, original_file=None,
                         project=None):
        try:
            with transaction.atomic():
                errors = []
                instance = self.model(
                    xls_form=xls_form,
                    original_file=original_file,
                    project=project
                )
                json = parse_file_to_json(instance.xls_form.file.name)
                has_default_language = (
                    'default_language' in json and
                    json['default_language'] != 'default'
                )
                if (has_default_language and
                   not check_for_language(json['default_language'])):
                    raise InvalidXLSForm(
                        ["Default language code '{}' unknown".format(
                            json['default_language']
                        )]
                    )
                is_multilingual = multilingual_label_check(json['children'])
                if is_multilingual and not has_default_language:
                    raise InvalidXLSForm(["Multilingual XLS forms must have "
                                          "a default_language setting"])
                instance.default_language = json['default_language']
                if instance.default_language == 'default':
                    instance.default_language = ''
                instance.filename = json.get('name')
                instance.title = json.get('title')
                instance.id_string = json.get('id_string')

                survey = create_survey_element_from_dict(json)
                xml_form = survey.xml()
                fix_languages(xml_form)

                instance.save()

                project.current_questionnaire = instance.id
                project.save()

                create_children(
                    children=json.get('children'),
                    errors=errors,
                    project=project,
                    default_language=instance.default_language,
                    kwargs={'questionnaire': instance}
                )

                # all these errors handled by PyXForm so turning off for now
                # if errors:
                #     raise InvalidXLSForm(errors)

                return instance

        except PyXFormError as e:
            raise InvalidXLSForm([str(e)])


class QuestionGroupManager(models.Manager):

    def create_from_dict(self, dict=None, question_group=None,
                         questionnaire=None, errors=[], index=0):
        instance = self.model(questionnaire=questionnaire,
                              question_group=question_group)

        relevant = None
        bind = dict.get('bind')
        if bind:
            relevant = bind.get('relevant', None)

        instance.name = dict.get('name')
        instance.label_xlat = dict.get('label', {})
        instance.type = dict.get('type')
        instance.relevant = relevant
        instance.index = index
        instance.save()

        create_children(
            children=dict.get('children'),
            errors=errors,
            project=questionnaire.project,
            default_language=questionnaire.default_language,
            kwargs={
                'questionnaire': questionnaire,
                'question_group': instance
            }
        )

        return instance


class QuestionManager(models.Manager):

    def create_from_dict(self, errors=[], index=0, **kwargs):
        dict = kwargs.pop('dict')
        instance = self.model(**kwargs)
        type_dict = {name: code for code, name in instance.TYPE_CHOICES}

        relevant = None
        required = False
        bind = dict.get('bind')
        if bind:
            relevant = bind.get('relevant', None)
            required = True if bind.get('required', 'no') == 'yes' else False

        instance.type = type_dict[dict.get('type')]
        instance.name = dict.get('name')
        instance.label_xlat = dict.get('label', {})
        instance.required = required
        instance.constraint = dict.get('constraint')
        instance.default = dict.get('default', None)
        instance.hint = dict.get('hint', None)
        instance.relevant = relevant
        instance.index = index
        instance.save()

        if instance.has_options:
            create_options(dict.get('choices'), instance, errors=errors)

        return instance
