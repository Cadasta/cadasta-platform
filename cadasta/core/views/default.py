import json

from core.views.generic import TemplateView
from django.shortcuts import redirect
from organization.models import Organization, Project
from organization.serializers import ProjectGeometrySerializer
from tutelary.models import Role


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
        projects = []
        superuser = Role.objects.filter(name='superuser')
        if len(superuser) and hasattr(self.request.user, 'assigned_policies'):
            if superuser[0] in self.request.user.assigned_policies():
                projects = Project.objects.filter(extent__isnull=False)
        if projects == []:
            if hasattr(self.request.user, 'organizations'):
                user_orgs = self.request.user.organizations.all()
                if len(user_orgs) > 0:
                    for org in Organization.objects.all():
                        if org in user_orgs:
                            projects.extend(org.projects.filter(
                                access='private',
                                extent__isnull=False,
                                archived=False))
            projects.extend(Project.objects.filter(
                access='public',
                extent__isnull=False,
                archived=False))
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
