import json

from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from organization.models import Project
from django.core.serializers import serialize

from organization.serializers import ProjectGeometrySerializer


class IndexPage(TemplateView):
    template_name = 'core/index.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_anonymous():
            return redirect('core:dashboard')

        return super(IndexPage, self).get(request, *args, **kwargs)


class Dashboard(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data( **kwargs)
        projects = Project.objects.filter(extent__isnull=False)
        context['geojson'] = json.dumps(ProjectGeometrySerializer(projects, many=True).data)
        return context
