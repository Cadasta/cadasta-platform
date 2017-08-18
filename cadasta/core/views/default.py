import json

from django.db.models import Q
from core.views.generic import TemplateView
from django.shortcuts import redirect
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

    def get_queryset(self):
        user = self.request.user
        default = Q(access='public', archived=False)
        all_projects = Project.objects.select_related(
            'organization').filter(extent__isnull=False)
        if user.is_superuser:
            return all_projects
        if user.is_anonymous:
            return all_projects.filter(default)
        else:
            org_roles = (user.organizationrole_set
                         .select_related('organization'))
            ids = []
            ids += (org_roles.filter(
                    organization__projects__access='private',
                    organization__projects__extent__isnull=False,
                    organization__projects__archived=False,
                    group__permissions__codename__in=['project.view.private'])
                    .values_list('organization__projects', flat=True))
            ids += (org_roles.filter(
                    organization__projects__archived=True,
                    organization__projects__extent__isnull=False,
                    group__permissions__codename__in=[
                        'project.view.archived'])
                    .values_list('organization__projects', flat=True))

            prj_roles = user.projectrole_set.select_related('project')

            # public archived
            ids += prj_roles.filter(project__archived=True,
                                    project__access='public',
                                    project__extent__isnull=False,
                                    group__permissions__codename__in=[
                                        'project.view.archived',
                                        'project.view']
                                    ).values_list('project', flat=True)

            # private active projects
            ids += prj_roles.filter(project__access='private',
                                    project__archived=False,
                                    project__extent__isnull=False,
                                    group__permissions__codename__in=[
                                        'project.view.private']
                                    ).values_list('project', flat=True)

            # private archived projects
            ids += prj_roles.filter(project__access='private',
                                    project__archived=True,
                                    project__extent__isnull=False,
                                    group__permissions__codename__in=[
                                        'project.view.private',
                                        'project.view.archived']
                                    ).values_list('project', flat=True)

            query = default | Q(id__in=set(ids))
            return all_projects.filter(query)

    def get(self, request, *args, **kwargs):
        projects = self.get_queryset()
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
