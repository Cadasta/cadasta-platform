import re
from xml.dom.minidom import Element
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models, transaction
from django.utils.translation import ugettext as _
from django.db.utils import IntegrityError
from jsonattrs.models import Attribute, AttributeType, Schema
from pyxform.builder import create_survey_element_from_dict
from pyxform.errors import PyXFormError
from pyxform.xls2json import parse_file_to_json
from core.messages import SANITIZE_ERROR
from core.validators import sanitize_string
from .choices import QUESTION_TYPES, XFORM_GEOM_FIELDS
from .exceptions import InvalidQuestionnaire
from .messages import MISSING_RELEVANT, INVALID_ACCURACY
from .validators import validate_accuracy, validate_required

ATTRIBUTE_GROUPS = settings.ATTRIBUTE_GROUPS


def get_attr_type_ids():
    return {
        _type: _id
        for _type, _id in AttributeType.objects.values_list('name', 'id')
    }


def create_children(children, errors=[], project=None, default_language='',
                    questionnaire=None, question_group=None):
    if children:
        ATTR_TYPE_IDS = get_attr_type_ids()
        for idx, child in enumerate(children):
            if child.get('type') in ['group', 'repeat']:
                model_name = 'QuestionGroup'

                # parse attribute group
                attribute_group = child.get('name')
                for attr_group in ATTRIBUTE_GROUPS.keys():
                    if attribute_group.startswith(attr_group):
                        app_label = ATTRIBUTE_GROUPS[attr_group]['app_label']
                        model = ATTRIBUTE_GROUPS[attr_group]['model']
                        content_type = ContentType.objects.get(
                            app_label=app_label, model=model)
                        create_attrs_schema(
                            project=project, question_group_dict=child,
                            attr_type_ids=ATTR_TYPE_IDS,
                            content_type=content_type,
                            default_language=default_language, errors=errors
                        )
            else:
                model_name = 'Question'

            model = apps.get_model('questionnaires', model_name)
            model.objects.create_from_dict(
                data=child, index=idx, errors=errors,
                questionnaire=questionnaire, question_group=question_group)


def create_options(options, question, errors=[]):
    if options:
        for idx, option in enumerate(options, 1):
            QuestionOption = apps.get_model('questionnaires', 'QuestionOption')

            QuestionOption.objects.create(
                question=question, index=idx, name=option['name'],
                label_xlat=option.get('label_xlat', option.get('label', {}))
            )
    else:
        errors.append(_("Please provide at least one option for field"
                        " '{field_name}'").format(field_name=question.name))


def fix_labels(labels):
    if isinstance(labels, dict):
        return {k: str(v) for k, v in labels.items()}
    else:
        return labels


def create_attrs_schema(project, question_group_dict, attr_type_ids,
                        content_type, default_language='', errors=[]):
    fields = []
    selectors = (project.organization.pk, project.pk,
                 project.current_questionnaire)
    # check if the attribute group has a relevant bind statement,
    # eg ${party_type}='IN'
    # this enables conditional attribute schema creation
    bind = question_group_dict.get('bind', None)
    if bind:
        relevant = bind.get('relevant', None)
        if relevant:
            clauses = relevant.split('=')
            selector = re.sub("'", '', clauses[1])
            selectors += (selector,)

    try:
        schema_obj = Schema.objects.create(content_type=content_type,
                                           selectors=selectors,
                                           default_language=default_language)
    except IntegrityError:
        raise InvalidQuestionnaire(errors=[MISSING_RELEVANT])

    for child in question_group_dict['children']:
        field = {}
        field['name'] = child.get('name')
        field['long_name'] = child.get('label')

        if any('{}_resource'.format(model_type) in field['name']
               for model_type in ('tenure', 'location', 'party')):
            continue

        # HACK: pyxform renames select_multiple to select all that apply
        if child.get('type') == 'select all that apply':
            field['attr_type'] = 'select_multiple'
        else:
            # HACK: pyxform strips underscores from xform field names
            field['attr_type'] = child.get('type').replace(' ', '_')
        if child.get('default'):
            field['default'] = child.get('default', '')
        if child.get('omit'):
            field['omit'] = child.get('omit')
        bind = child.get('bind')
        if bind:
            field['required'] = True if bind.get(
                'required') == 'yes' else False
        if child.get('choices'):
            field['choices'] = [choice.get('name')
                                for choice in child.get('choices')]
            field['choice_labels'] = [fix_labels(choice.get('label'))
                                      for choice in child.get('choices')]
        fields.append(field)

    for idx, field in enumerate(fields, 1):
        long_name = field.get('long_name', field['name'])
        try:
            attr_type_id = attr_type_ids[field['attr_type']]
        except KeyError:
            msg = _(
                    "{attr_type!r} (found in the {name!r} question) is not "
                    "a supported attribute type."
                ).format(**field)
            raise InvalidQuestionnaire([msg])
        choices = field.get('choices', [])
        choice_labels = field.get('choice_labels', None)
        default = field.get('default', '')
        required = field.get('required', False)
        omit = True if field.get('omit', '') == 'yes' else False
        Attribute.objects.create(
            schema=schema_obj,
            name=field['name'], long_name=long_name,
            attr_type_id=attr_type_id, index=idx,
            choices=choices, choice_labels=choice_labels,
            default=default, required=required, omit=omit
        )


def check_for_language(lang):
    return lang in settings.FORM_LANGS.keys()


def multilingual_label_check(children):
    has_multi = False
    for child in children:
        if isinstance(child.get('label'), dict):
            has_multi = True
            for lang in child['label'].keys():
                if lang != 'default' and not check_for_language(lang):
                    raise InvalidQuestionnaire(
                        ["Label language code '{}' unknown".format(lang)]
                    )
        # Note the order of the short-cut "or" in the following two
        # statements: it's like this to force the recursive call to
        # multilingual_label_check to make sure we check the language
        # codes everywhere, rather than dropping out as soon as we
        # find that the form is multilingual.
        if 'children' in child:
            has_multi = (
                multilingual_label_check(child['children']) or has_multi)
        if 'choices' in child:
            has_multi = multilingual_label_check(child['choices']) or has_multi
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


def santize_form(form_json):
    for key, value in form_json.items():
        if isinstance(value, list):
            for list_item in value:
                santize_form(list_item)
        elif isinstance(value, dict):
            santize_form(value)
        else:
            if not sanitize_string(value):
                raise InvalidQuestionnaire([SANITIZE_ERROR])


class QuestionnaireManager(models.Manager):

    def create_from_form(self, xls_form, project, original_file=None):
        try:
            with transaction.atomic():
                errors = []
                instance = self.model(
                    xls_form=xls_form,
                    original_file=original_file,
                    project=project
                )
                xls_file = instance.xls_form.file
                json = parse_file_to_json(xls_file.name)
                xls_file.close()

                id_string = json['id_string']
                if re.search(r"\s", id_string):
                    raise InvalidQuestionnaire([
                        _("'form_id' field must not contain whitespace.")])

                validate_required(json.get('children', []))
                santize_form(json)

                has_default_language = (
                    'default_language' in json and
                    json['default_language'] != 'default'
                )
                if (has_default_language and
                   not check_for_language(json['default_language'])):
                    raise InvalidQuestionnaire(
                        ["Default language code '{}' unknown".format(
                            json['default_language']
                        )]
                    )
                is_multilingual = multilingual_label_check(json['children'])
                if is_multilingual and not has_default_language:
                    raise InvalidQuestionnaire(
                        ["Multilingual XLS forms must have a default_language"
                         " setting"])
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

                create_children(
                    children=json.get('children'),
                    errors=errors,
                    project=project,
                    default_language=instance.default_language,
                    questionnaire=instance
                )
                project.save()

                # all these errors handled by PyXForm so turning off for now
                # if errors:
                #     raise InvalidQuestionnaire(errors)

                return instance

        except PyXFormError as e:
            raise InvalidQuestionnaire([str(e)])


class QuestionGroupManager(models.Manager):

    def create_from_dict(self, data, questionnaire, question_group=None,
                         errors=[], index=0):
        instance = self.model(questionnaire=questionnaire,
                              question_group=question_group)

        relevant = None
        bind = data.get('bind')
        if bind:
            relevant = bind.get('relevant')

        instance.name = data.get('name')
        instance.label_xlat = data.get('label', {})
        instance.type = data.get('type')
        instance.relevant = relevant
        instance.index = index
        instance.save()

        create_children(
            children=data.get('children'),
            errors=errors,
            project=questionnaire.project,
            default_language=questionnaire.default_language,
            questionnaire=questionnaire,
            question_group=instance
        )

        return instance


class QuestionManager(models.Manager):

    def create_from_dict(self, data, questionnaire, question_group=None,
                         errors=[], index=0):
        instance = self.model(
            questionnaire=questionnaire, question_group=question_group)
        type_dict = {name: code for code, name in QUESTION_TYPES}
        relevant = None
        required = False
        bind = data.get('bind')
        if bind:
            relevant = bind.get('relevant', None)
            required = True if bind.get('required', 'no') == 'yes' else False

        gps_accuracy = None
        control = data.get('control')
        if control and type_dict[data.get('type')] in XFORM_GEOM_FIELDS:
            gps_accuracy = control.get('accuracyThreshold', None)
            if gps_accuracy and not validate_accuracy(gps_accuracy):
                raise(InvalidQuestionnaire([INVALID_ACCURACY]))
        appearance = None
        if control:
            appearance = control.get('appearance', None)

        instance.type = type_dict[data.get('type')]
        instance.name = data.get('name')
        instance.label_xlat = data.get('label', {})
        instance.required = required
        instance.gps_accuracy = gps_accuracy
        instance.constraint = data.get('constraint')
        instance.default = data.get('default', None)
        instance.hint = data.get('hint', None)
        instance.relevant = relevant
        instance.appearance = appearance
        instance.index = index
        instance.save()

        if instance.has_options:
            create_options(data.get('choices'), instance, errors=errors)

        return instance
