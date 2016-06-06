import json

from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from organization.models import Project, Organization

from organization.serializers import ProjectGeometrySerializer


class IndexPage(TemplateView):
    template_name = 'core/index.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_anonymous():
            return redirect('core:dashboard')

        return super(IndexPage, self).get(request, *args, **kwargs)


class Dashboard(LoginRequiredMixin, TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, projects, **kwargs):
        context = super().get_context_data(**kwargs)
        projects.extend(Project.objects.filter(access='public'))
        context['geojson'] = json.dumps(
            ProjectGeometrySerializer(projects, many=True).data
        )
        return context

    def get(self, request, *args, **kwargs):
        projects = []
        if hasattr(self.request.user, 'organizations'):
            user_orgs = self.request.user.organizations.all()
            if len(user_orgs) > 0:
                for org in Organization.objects.all():
                    if org in user_orgs:
                        projects.extend(org.projects.filter(access='private'))
        context = self.get_context_data(projects=projects)
        return super(TemplateView, self).render_to_response(context)
