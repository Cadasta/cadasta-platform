import json

from django.db.models import Q
from django.shortcuts import redirect

from core.views.generic import TemplateView
from organization.models import Project
from organization.serializers import ProjectGeometrySerializer


class IndexPage(TemplateView):
    template_name = 'core/index.html'

    def get(self, request, *args, **kwargs):
        return redirect('core:dashboard')


class Dashboard(TemplateView):
    template_name = 'core/dashboard.html'

    def get_context_data(self, projects, **kwargs):
        context = super().get_context_data(**kwargs)
        context['geojson'] = json.dumps(
            ProjectGeometrySerializer(projects, many=True).data
        )
        return context

    def get(self, request, *args, **kwargs):
        projects = Project.objects.filter(extent__isnull=False)
        if not self.is_superuser:
            query = Q(access='public')

            if self.request.user.is_authenticated:
                query |= Q(
                    organization__organizationrole__user=self.request.user,
                    access='private')
            projects = projects.filter(query)
            projects = projects.filter(archived=False)
        projects = projects.select_related('organization').distinct()
        context = self.get_context_data(projects=projects)
        return super(TemplateView, self).render_to_response(context)


def server_error(request, template_name='500.html'):
    """
    500 error handler.

    Templates: `500.html`
    Context: None
    """
    from django.template import loader
    from django.http import HttpResponseServerError
    t = loader.get_template(template_name)
    return HttpResponseServerError(t.render())
