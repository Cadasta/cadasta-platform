import json

from config.settings.default import LEAFLET_CONFIG
from core.views.generic import TemplateView
from django.shortcuts import redirect
from django.utils.encoding import force_text
from organization.models import Organization, Project
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
        context['leaflet_tiles'] = [
            {
              'label': force_text(label),
              'url': url,
              'attrs': force_text(attrs)
            } for (label, url, attrs) in LEAFLET_CONFIG.get('TILES')]
        return context

    def get(self, request, *args, **kwargs):
        projects = []
        if self.is_superuser:
            projects = (Project.objects.select_related('organization')
                        .filter(extent__isnull=False))
        if projects == []:
            if hasattr(self.request.user, 'organizations'):
                user_orgs = self.request.user.organizations.all()
                if len(user_orgs) > 0:
                    for org in Organization.objects.all():
                        if org in user_orgs:
                            projects.extend(org.projects
                                            .select_related('organization')
                                            .filter(
                                                access='private',
                                                extent__isnull=False,
                                                archived=False))
            projects.extend(Project.objects.select_related('organization')
                            .filter(
                                access='public',
                                extent__isnull=False,
                                archived=False).select_related('organization'))
        context = self.get_context_data(projects=projects)
        return super(TemplateView, self).render_to_response(context)


def server_error(request, template_name='500.html'):
    """
    500 error handler.

    Templates: `500.html`
    Context: None
    """
    from django.template import RequestContext, loader
    from django.http import HttpResponseServerError
    t = loader.get_template(template_name)
    return HttpResponseServerError(t.render(RequestContext(request)))
