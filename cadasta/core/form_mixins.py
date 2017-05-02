from django.forms import Form, ModelForm, MultipleChoiceField, CharField
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.translation import get_language
from jsonattrs.mixins import template_xlang_labels
from jsonattrs.forms import form_field_from_name
from tutelary.models import Role

from core.validators import sanitize_string
from questionnaires.models import Questionnaire, Question, QuestionOption
from .mixins import SchemaSelectorMixin
from .widgets import XLangSelect, XLangSelectMultiple
from .messages import SANITIZE_ERROR


def get_types(question_name, default, questionnaire_id=None,
              include_labels=False):
    types = []
    if questionnaire_id:
        try:
            question = Question.objects.get(
                name=question_name,
                questionnaire=questionnaire_id)
        except Question.DoesNotExist:
            pass
        else:
            options = QuestionOption.objects.filter(
                question=question).values_list('name', 'label_xlat')

            lang = get_language()
            default_lang = question.questionnaire.default_language

            for key, label in options:
                if isinstance(label, dict):
                    label = label.get(lang, label.get(default_lang))

                types.append((key, label))

    if not types:
        types = default

    if include_labels:
        return types
    else:
        return [key for key, _ in types]


class SuperUserCheck:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._su_role = None

    def is_superuser(self, user):
        if not hasattr(self, 'su_role'):
            self.su_role = Role.objects.get(name='superuser')

        return any([isinstance(pol, Role) and pol == self.su_role
                    for pol in user.assigned_policies()])


class AttributeFormMixin(SchemaSelectorMixin):
    def set_standard_field(self, name, empty_choice=None, field_name=None):
        if not field_name:
            field_name = name
        q = Questionnaire.objects.get(id=self.project.current_questionnaire)
        default_lang = q.default_language
        try:
            question = Question.objects.get(name=name, questionnaire=q)
            self.fields[field_name].labels_xlang = template_xlang_labels(
                    question.label_xlat)

            if question.has_options:
                choices = QuestionOption.objects.filter(
                    question=question).values_list('name', 'label_xlat')

                try:
                    choices, xlang_labels = zip(
                        *[((c[0], c[1].get(default_lang)),
                          (c[0], c[1])) for c in choices])
                except AttributeError:
                    choices = choices
                    xlang_labels = ''

                choices = ([('', empty_choice)] + list(choices)
                           if empty_choice else list(choices))
                self.fields[field_name].choices = choices
                self.fields[field_name].widget = XLangSelect(
                    attrs=self.fields[field_name].widget.attrs,
                    choices=choices,
                    xlang_labels=dict(xlang_labels)
                )
        except Question.DoesNotExist:
            pass

    def create_model_fields(self, field_prefix, attribute_map, new_item=False):
        for selector, attributes in attribute_map.items():
            for name, attr in attributes.items():
                fieldname = '{}::{}::{}'.format(
                    field_prefix, selector.lower(), name)
                atype = attr.attr_type

                field_kwargs = {
                    'label': attr.long_name, 'required': attr.required
                }
                field = form_field_from_name(atype.form_field)
                if not new_item:
                    self.set_initial(field_kwargs, attr.name, attr)
                if atype.form_field in ['ChoiceField', 'MultipleChoiceField']:
                    if (attr.choice_labels is not None and
                            attr.choice_labels != []):
                        chs = list(zip(attr.choices, attr.choice_labels))
                    else:
                        chs = [(c, c) for c in attr.choices]

                    field_kwargs['choices'] = chs
                if atype.form_field == 'BooleanField':
                    field_kwargs['required'] = attr.required
                    if len(attr.default) > 0:
                        self.set_default(field_kwargs, attr, boolean=True)
                else:
                    if attr.required and new_item:
                        field_kwargs['required'] = True
                    if len(attr.default) > 0 and len(str(
                            field_kwargs.get('initial', ''))) == 0:
                        self.set_default(field_kwargs, attr)

                f = field(**field_kwargs)

                if hasattr(f.widget, 'choices'):
                    try:
                        xlang_labels = dict(zip(attr.choices,
                                                attr.choice_labels_xlat))
                    except TypeError:
                        xlang_labels = {}

                    widget_args = {
                        'attrs': f.widget.attrs,
                        'choices': f.widget.choices,
                        'xlang_labels': xlang_labels
                    }

                    if isinstance(f, MultipleChoiceField):
                        f.widget = XLangSelectMultiple(**widget_args)
                    else:
                        f.widget = XLangSelect(**widget_args)

                f.labels_xlang = template_xlang_labels(attr.long_name_xlat)
                self.fields[fieldname] = f

    def set_default(self, field_kwargs, attr, boolean=False):
        if len(attr.default) > 0:
            if boolean:
                field_kwargs['initial'] = (attr.default != 'False')
            else:
                field_kwargs['initial'] = attr.default

    def set_initial(self, field_kwargs, name, attr):
        if hasattr(self, 'instance'):
            attrvals = getattr(self.instance, self.attributes_field)
            if name in attrvals:
                if attr.attr_type.form_field == 'BooleanField':
                    field_kwargs['initial'] = (
                        attrvals[name]
                        if isinstance(attrvals[name], bool)
                        else attrvals[name] != 'False'
                    )
                else:
                    field_kwargs['initial'] = attrvals.get(name, None)

    def process_attributes(self, key, entity_type=''):
        attributes = {}
        for k, v in self.cleaned_data.items():
            if k.startswith(key + '::'):
                _, type, name = k.split('::')
                if type in [entity_type.lower(), 'default']:
                    attributes[name] = v
        if hasattr(self, 'instance'):
            setattr(self.instance, self.attributes_field, attributes)
        else:
            return attributes


class AttributeForm(AttributeFormMixin, Form):
    def add_attribute_fields(self, content_type):
        label = '{}.{}'.format(content_type.app_label, content_type.model)
        attributes = self.get_model_attributes(self.project, label)
        new_item = self.data.get('new_item') == 'on'
        self.create_model_fields(
            content_type.model, attributes, new_item=new_item
        )


class AttributeModelForm(AttributeFormMixin, ModelForm):
    def add_attribute_fields(self):
        content_type = ContentType.objects.get_for_model(self.Meta.model)
        label = '{}.{}'.format(content_type.app_label, content_type.model)
        attributes = self.get_model_attributes(self.project, label)
        new_item = self.data.get('new_item') == 'on'
        self.create_model_fields(
            content_type.model, attributes, new_item=new_item
        )

    def save(self, *args, **kwargs):
        entity_type = kwargs.get('entity_type', '')
        project_id = kwargs.get('project_id', None)
        instance = super().save(commit=False)
        content_type = ContentType.objects.get_for_model(instance)
        if self.attributes_field is not None:
            self.process_attributes(content_type.model, entity_type)
        if project_id is not None and hasattr(instance, 'project_id'):
            setattr(instance, 'project_id', project_id)
        return super().save()


class SanitizeFieldsForm:
    def clean(self):
        cleaned_data = super().clean()
        for name in self.fields:
            field = self.fields[name]
            if type(field) is not CharField:
                continue

            value = cleaned_data.get(name)
            if not sanitize_string(value):
                self.add_error(name, ValidationError(SANITIZE_ERROR))

        return cleaned_data
