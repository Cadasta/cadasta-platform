from django.template.loader import render_to_string
from django.db.models import Q
from tutelary.mixins import APIPermissionRequiredMixin
from jsonattrs.mixins import template_xlang_labels
from rest_framework import generics
from rest_framework.response import Response

from core.views.mixins import AsyncList
from questionnaires.models import Question, QuestionOption


from . import mixins


class PartyList(APIPermissionRequiredMixin,
                AsyncList,
                mixins.PartyQuerySetMixin,
                generics.ListAPIView):
    sort_columns = ('name', 'type', )

    def get_actions(self, request):
        if self.get_project().archived:
            return ['project.view_archived', 'party.list']
        if self.get_project().public():
            return ['project.view', 'party.list']
        else:
            return ['project.view_private', 'party.list']

    permission_required = {
        'GET': get_actions
    }

    def get_perms_objects(self):
        return [self.get_project()]

    def build_search_query(self, term):
        return Q(name__contains=term)

    def get(self, *args, **kwargs):
        qs, records_total, records_filtered = self.get_results()

        party_opts = {}
        project = self.get_project()
        if project.current_questionnaire:
            try:
                party_type = Question.objects.get(
                    name='party_type',
                    questionnaire_id=project.current_questionnaire)
                party_opts = QuestionOption.objects.filter(question=party_type)
                party_opts = dict(party_opts.values_list('name', 'label_xlat'))
            except Question.DoesNotExist:
                pass

        for party in qs:
            party.type_labels = template_xlang_labels(
                party_opts.get(party.type))

        return Response({
            'draw': int(self.request.GET.get('draw')),
            'recordsTotal': records_total,
            'recordsFiltered': records_filtered,
            'data': [],
            'tbody': render_to_string(
                'party/table_snippets/party.html',
                context={
                    'parties': qs,
                    'project': project
                },
                request=self.request)
        })
