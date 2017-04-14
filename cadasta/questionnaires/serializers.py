import re
from buckets.serializers import S3Field
from rest_framework import serializers

from django.db import transaction
from django.db.utils import IntegrityError
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from jsonattrs.models import Attribute, AttributeType, Schema
from .messages import MISSING_RELEVANT
from .exceptions import InvalidQuestionnaire
from .validators import validate_questionnaire
from .managers import fix_labels
from . import models


ATTRIBUTE_GROUPS = settings.ATTRIBUTE_GROUPS
QUESTION_TYPES = dict(models.Question.TYPE_CHOICES)


def create_questions(questions, context):
    question_serializer = QuestionSerializer(
        data=questions,
        many=True,
        context=context)
    question_serializer.is_valid(raise_exception=True)
    question_serializer.save()


def create_groups(groups, context):
    group_serializer = QuestionGroupSerializer(
        data=groups,
        many=True,
        context=context)
    group_serializer.is_valid(raise_exception=True)
    group_serializer.save()


class FindInitialMixin:
    def find_initial_data(self, name):
        if isinstance(self.initial_data, list):
            for item in self.initial_data:
                if item['name'] == name:
                    return item

        return self.initial_data


class QuestionOptionSerializer(FindInitialMixin, serializers.ModelSerializer):
    label_xlat = serializers.JSONField(required=False)

    class Meta:
        model = models.QuestionOption
        fields = ('id', 'name', 'label', 'index', 'label_xlat')
        read_only_fields = ('id',)
        write_only_fields = ('label_xlat', )

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        if isinstance(instance, models.QuestionOption):
            rep['label'] = instance.label_xlat
        return rep

    def create(self, validated_data):
        initial_data = self.find_initial_data(validated_data['name'])
        validated_data['question_id'] = self.context.get('question_id')
        validated_data['label_xlat'] = initial_data['label']
        return super().create(validated_data)


class QuestionSerializer(FindInitialMixin, serializers.ModelSerializer):
    label_xlat = serializers.JSONField(required=False)

    class Meta:
        model = models.Question
        fields = ('id', 'name', 'label', 'type', 'required', 'constraint',
                  'default', 'hint', 'relevant', 'label_xlat', 'index', )
        read_only_fields = ('id', )
        write_only_fields = ('label_xlat', )

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        if isinstance(instance, models.Question):
            rep['label'] = instance.label_xlat
            if instance.has_options:
                serializer = QuestionOptionSerializer(instance.options,
                                                      many=True)
                rep['options'] = serializer.data

        return rep

    def create(self, validated_data):
        initial_data = self.find_initial_data(validated_data['name'])
        validated_data['label_xlat'] = initial_data['label']
        question = models.Question.objects.create(
            questionnaire_id=self.context['questionnaire_id'],
            question_group_id=self.context.get('question_group_id'),
            **validated_data)

        option_serializer = QuestionOptionSerializer(
                data=initial_data.get('options', []),
                many=True,
                context={'question_id': question.id})

        option_serializer.is_valid(raise_exception=True)
        option_serializer.save()

        return question


class QuestionGroupSerializer(FindInitialMixin, serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    question_groups = serializers.SerializerMethodField()
    label_xlat = serializers.JSONField(required=False)

    class Meta:
        model = models.QuestionGroup
        fields = ('id', 'name', 'label',  'type', 'questions',
                  'question_groups', 'label_xlat', 'relevant', 'index', )
        read_only_fields = ('id', 'questions', 'question_groups', )
        write_only_fields = ('label_xlat', )

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        if isinstance(instance, models.QuestionGroup):
            rep['label'] = instance.label_xlat
        return rep

    def get_question_groups(self, group):
        serializer = QuestionGroupSerializer(
            group.question_groups.all(),
            many=True,
        )
        return serializer.data

    def create(self, validated_data):
        initial_data = self.find_initial_data(validated_data['name'])
        validated_data['label_xlat'] = initial_data['label']
        group = models.QuestionGroup.objects.create(
            questionnaire_id=self.context['questionnaire_id'],
            question_group_id=self.context.get('question_group_id'),
            **validated_data)

        context = {
            'question_group_id': group.id,
            'questionnaire_id': self.context['questionnaire_id'],
            'project': self.context['project']
        }

        create_groups(initial_data.get('question_groups', []), context)
        create_questions(initial_data.get('questions', []), context)

        project = self.context['project']
        attribute_group = validated_data['name']
        for attr_group in ATTRIBUTE_GROUPS.keys():
            if attribute_group.startswith(attr_group):
                selectors = (project.organization.pk, project.pk,
                             project.current_questionnaire)

                relevant = initial_data.get('relevant', None)
                if relevant:
                    clauses = relevant.split('=')
                    selector = re.sub("'", '', clauses[1])
                    selectors += (selector,)

                app_label = ATTRIBUTE_GROUPS[attr_group]['app_label']
                model = ATTRIBUTE_GROUPS[attr_group]['model']
                content_type = ContentType.objects.get(app_label=app_label,
                                                       model=model)

                try:
                    schema_obj = Schema.objects.create(
                        content_type=content_type,
                        selectors=selectors,
                        default_language=self.context['default_language'])
                except IntegrityError:
                    raise InvalidQuestionnaire(errors=[MISSING_RELEVANT])

                for field in initial_data.get('questions', []):
                    if field['type'] == 'S1':
                        field_type = 'select_one'
                    elif field['type'] == 'SM':
                        field_type = 'select_multiple'
                    else:
                        field_type = QUESTION_TYPES.get(field['type'])

                    attr_type = AttributeType.objects.get(name=field_type)
                    choices = [c.get('name') for c in field.get('options', [])]
                    choice_labels = [fix_labels(c.get('label'))
                                     for c in field.get('options', [])]
                    default = field.get('default', '')

                    Attribute.objects.create(
                        schema=schema_obj,
                        name=field['name'],
                        long_name=field.get('label', field['name']),
                        attr_type=attr_type,
                        index=field['index'],
                        choices=choices,
                        choice_labels=choice_labels if choice_labels else None,
                        default=(default if default is not None else ''),
                        required=field.get('required', False),
                        omit=field.get('omit', False),
                    )

        return group


class QuestionnaireSerializer(serializers.ModelSerializer):
    xls_form = S3Field(required=False)
    id_string = serializers.CharField(
        max_length=50, required=False, default=''
    )
    version = serializers.IntegerField(required=False, default=1)
    questions = serializers.SerializerMethodField()
    question_groups = serializers.SerializerMethodField()

    class Meta:
        model = models.Questionnaire
        fields = (
            'id', 'filename', 'title', 'id_string', 'xls_form',
            'version', 'questions', 'question_groups', 'md5_hash'
        )
        read_only_fields = (
            'id', 'filename', 'title', 'id_string', 'version',
            'questions', 'question_groups'
        )

    def validate_json(self, json, raise_exception=False):
        errors = validate_questionnaire(json)
        self._validated_data = json
        self._errors = {}

        if errors:
            self._validated_data = {}
            self._errors = errors

            if raise_exception:
                raise serializers.ValidationError(self.errors)

        return not bool(self._errors)

    def is_valid(self, **kwargs):
        if 'xls_form' in self.initial_data:
            return super().is_valid(**kwargs)
        else:
            return self.validate_json(self.initial_data, **kwargs)

    def create(self, validated_data):
        project = self.context['project']
        if 'xls_form' in validated_data:
            form = validated_data['xls_form']
            instance = models.Questionnaire.objects.create_from_form(
                xls_form=form,
                project=project
            )
            return instance
        else:
            questions = validated_data.pop('questions', [])
            question_groups = validated_data.pop('question_groups', [])
            with transaction.atomic():
                instance = models.Questionnaire.objects.create(
                    project=project,
                    **validated_data)

                context = {
                    'questionnaire_id': instance.id,
                    'project': project,
                    'default_language': instance.default_language or 'en'
                }
                create_questions(questions, context)
                create_groups(question_groups, context)

                project.current_questionnaire = instance.id
                project.save()

                return instance

    def get_questions(self, instance):
        questions = instance.questions.filter(question_group__isnull=True)
        serializer = QuestionSerializer(questions, many=True)
        return serializer.data

    def get_question_groups(self, instance):
        groups = instance.question_groups.filter(question_group__isnull=True)
        serializer = QuestionGroupSerializer(groups, many=True)
        return serializer.data
