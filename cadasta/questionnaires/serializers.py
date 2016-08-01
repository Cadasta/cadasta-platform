from buckets.serializers import S3Field
from rest_framework import serializers

from . import models


class QuestionOptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.QuestionOption
        fields = ('id', 'name', 'label',)
        read_only_fields = ('id', 'name', 'label',)


class QuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Question
        fields = ('id', 'name', 'label', 'type', 'required', 'constraint',)
        read_only_fields = ('id', 'name', 'label', 'type', 'required',
                            'constraint',)

    def to_representation(self, instance):
        rep = super().to_representation(instance)

        if (isinstance(instance, models.Question) and instance.has_options):
            serializer = QuestionOptionSerializer(instance.options, many=True)
            rep['options'] = serializer.data

        return rep


class QuestionGroupSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = models.QuestionGroup
        fields = ('id', 'name', 'label', 'questions',)
        read_only_fields = ('id', 'name', 'label', 'questions',)


class QuestionnaireSerializer(serializers.ModelSerializer):
    xls_form = S3Field()
    xml_form = S3Field(required=False)
    id_string = serializers.CharField(
        max_length=50, required=False, default=''
    )
    version = serializers.IntegerField(required=False, default=1)
    questions = serializers.SerializerMethodField()
    question_groups = QuestionGroupSerializer(many=True, read_only=True)

    class Meta:
        model = models.Questionnaire
        fields = (
            'id', 'filename', 'title', 'id_string', 'xls_form', 'xml_form',
            'version', 'questions', 'question_groups', 'md5_hash'
        )
        read_only_fields = (
            'id', 'filename', 'title', 'id_string', 'version',
            'questions', 'question_groups'
        )

    def create(self, validated_data):
        project = self.context['project']
        form = validated_data['xls_form']
        instance = models.Questionnaire.objects.create_from_form(
            xls_form=form,
            project=project
        )
        return instance

    def get_questions(self, instance):
        questions = instance.questions.filter(question_group__isnull=True)
        serializer = QuestionSerializer(questions, many=True)
        return serializer.data
