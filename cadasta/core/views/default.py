import json

from django.shortcuts import redirect
from django.views.generic import TemplateView
from organization.models import Project, Organization
from tutelary.models import Role

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
                                extent__isnull=False))
            projects.extend(Project.objects.filter(
                access='public',
                extent__isnull=False))
        context = self.get_context_data(projects=projects)
        return super(TemplateView, self).render_to_response(context)
