from django.core.urlresolvers import reverse
from core.mixins import PermissionRequiredMixin
import core.views.generic as generic

from . import mixins
from .. import messages as error_messages
from ..models import Project


class ProjectDashboard(PermissionRequiredMixin,
                       mixins.ProjectAdminCheckMixin,
                       mixins.ProjectMixin,
                       generic.DetailView):

    def get_actions(self, view):
        if self.prj.archived:
            return 'project.view_archived'
        if self.prj.public():
            return 'project.view'
        else:
            return 'project.view_private'

    model = Project
    template_name = 'organization/project_dashboard.html'
    permission_required = {'GET': get_actions}
    permission_denied_message = error_messages.PROJ_VIEW

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        num_locations = self.object.spatial_units.count()
        num_parties = self.object.parties.count()
        num_resources = self.object.resource_set.filter(
            archived=False).count()
        context['has_content'] = (
            num_locations > 0 or num_parties > 0 or num_resources > 0)
        context['num_locations'] = num_locations
        context['num_parties'] = num_parties
        context['num_resources'] = num_resources
        context['success_url'] = reverse('organization:project-dashboard',
                                         kwargs=self.kwargs)

        return context

    def get_object(self, queryset=None):
        return self.get_project()
