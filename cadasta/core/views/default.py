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
            org_admin_roles = user.organizationrole_set.filter(
                group__name='OrgAdmin').select_related('organization')
            prj_roles = user.projectrole_set.all().select_related(
                'project').filter(project__extent__isnull=False)
            ids = []
            for role in org_admin_roles:
                ids += [
                    prj.id for prj in role.organization.all_projects().filter(
                        extent__isnull=False)]
            for role in prj_roles:
                perms = role.permissions
                prj = role.project
                if ('project.view.private' in perms and prj.access ==
                        'private' and not prj.archived):
                        ids.append(prj.id)
                if ('project.view.archived' in perms and prj.archived):
                    ids.append(prj.id)
            default |= Q(id__in=set(ids))
            return all_projects.filter(default)

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
