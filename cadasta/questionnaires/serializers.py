from buckets.serializers import S3Field
from rest_framework import serializers

from .validators import validate_questionnaire
from . import models


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
            questionnaire_id=self.context.get('questionnaire_id'),
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
            questionnaire_id=self.context.get('questionnaire_id'),
            question_group_id=self.context.get('question_group_id'),
            **validated_data)

        context = {
            'question_group_id': group.id,
            'questionnaire_id': self.context.get('questionnaire_id')
        }

        create_groups(initial_data.get('question_groups', []), context)
        create_questions(initial_data.get('questions', []), context)

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
            instance = models.Questionnaire.objects.create(
                project=project,
                **validated_data)

            context = {'questionnaire_id': instance.id}
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
